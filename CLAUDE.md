# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
# Either:
python3 app/main.py

# Or:
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The SPA is served at `http://127.0.0.1:8000`. No build step — vanilla JS on Jinja2-rendered HTML (template includes are flattened into `templates/index.html`).

## Architecture

```
.docx/.txt/.md  →  Parser  →  IR (Document)  →  FormatEngine + Rules  →  .docx output
                                                  HTMLRenderer          →  HTML preview
```

**All formats normalize to the same IR** (`app/models/ir.py`). Parsers produce `Document` objects; the formatter and previewer consume only IR. Adding a new input format means adding a parser — nothing else changes.

### Core data flow

1. `Pipeline.ingest()` — saves uploaded file to `temp/uploads/`, picks a parser via `parsers/registry.py`, produces `Document` IR
2. `Pipeline.set_rules()` — stores `FormattingRules` (Pydantic model from `models/rules.py`) keyed by doc_id
3. `Pipeline.preview()` — `HTMLRenderer` converts IR + Rules into a self-contained HTML document
4. `Pipeline.format()` — `FormatEngine` converts IR + Rules into a `.docx` via python-docx
5. `Pipeline.cleanup()` — purges in-memory state and temp files

### Key modules

| Module | Role |
|---|---|
| `models/ir.py` | `Document`, `Section`, `Paragraph`, `Run`, `Table` dataclasses — the central contract |
| `models/rules.py` | `FormattingRules` Pydantic model — font, paragraph, page, headings, header/footer, images |
| `parsers/registry.py` | Maps file extension to parser instance (`DocxParser`, `TxtParser`, `MarkdownParser`) |
| `formatter/engine.py` | `FormatEngine.apply(document, output_path)` — walks IR blocks, emits python-docx elements |
| `preview/html_renderer.py` | `HTMLRenderer.render(document, rules)` — same IR + rules, outputs HTML with inline CSS |
| `services/pipeline.py` | Orchestrator holding in-memory `_documents` and `_rules` dicts |
| `services/storage.py` | Temp file lifecycle — save uploads, save outputs, stale cleanup every 5 min |
| `utils/validators.py` | Extension whitelist, size cap (50MB), .docx magic-byte check |

### Presets

Three JSON presets in `presets/`: `academic.json`, `business.json`, `casual.json`. Each contains a full `FormattingRules` dict. Loaded via `formatter/presets.py`.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/upload` | Upload file → returns `doc_id` |
| `GET` | `/api/documents/{id}` | Document summary |
| `POST` | `/api/documents/{id}/rules` | Save formatting rules |
| `GET` | `/api/documents/{id}/rules` | Get rules |
| `GET` | `/api/documents/{id}/preview` | HTML preview |
| `POST` | `/api/documents/{id}/format` | Generate .docx |
| `GET` | `/api/documents/{id}/download` | Download .docx |
| `GET` | `/api/presets` | List presets |
| `GET` | `/api/presets/{name}` | Get preset rules |
| `DELETE` | `/api/documents/{id}` | Cleanup |

## Caveats

- **State is in-memory** — server restart loses all documents and rules. Pipeline stores IR in `self._documents` dict, nothing persisted to disk beyond temp files.
- **Jinja2 3.1.6 + Python 3.14** has a template-cache bug (unhashable dict in cache key). The index page avoids `Jinja2Templates` entirely and serves `templates/index.html` as a raw file via `aiofiles` + `HTMLResponse`.
- **`.docx` heading detection** matches style IDs like `Heading1` (no space, from XML) as well as display names like `Heading 1`.
- **Encoding detection** for `.txt` uses `chardet` with a fallback chain: UTF-8 → UTF-16 → Latin-1 → Windows-1252 → GBK.
- **Routers import `pipeline` from `routes/upload.py`**, and `routes/upload.py` imports `storage` from `main.py`. The `routes/documents.py` router also imports `pipeline` from `routes/upload.py` — the Pipeline instance is shared this way.
