import re

import mistune

from app.models.ir import (
    Document,
    HorizontalRule,
    ImageReference,
    Paragraph,
    Run,
    Section,
    Table,
    TableCell,
    TableRow,
)
from app.parsers.base import BaseParser, ParseError


class MarkdownToIRRenderer(mistune.HTMLRenderer):
    """Custom mistune renderer that produces IR blocks instead of HTML strings."""

    def __init__(self):
        super().__init__()
        self.blocks: list = []
        self._current_runs: list[Run] = []
        self._list_level = 0
        self._list_type: str | None = None
        self._table_rows: list[TableRow] = []
        self._in_table = False
        self._in_heading = False
        self._heading_level = 0

    def heading(self, text: str, level: int, **attrs) -> str:
        self.blocks.append(Paragraph(
            runs=[Run(text=text)],
            style_hint=f"heading{min(level, 6)}",
        ))
        return ""

    def paragraph(self, text: str) -> str:
        if not text.strip():
            return ""
        text = self._strip_html(text)
        self.blocks.append(Paragraph(
            runs=self._text_to_runs(text),
            list_level=self._list_level,
            list_type=self._list_type if self._list_level > 0 else None,
        ))
        return ""

    def block_code(self, code: str, info: str | None = None) -> str:
        self.blocks.append(Paragraph(
            runs=[Run(text=code, font_name="Courier New")],
            style_hint="code",
        ))
        return ""

    def block_quote(self, text: str) -> str:
        text = self._strip_html(text)
        self.blocks.append(Paragraph(
            runs=[Run(text=text, italic=True)],
            style_hint="quote",
        ))
        return ""

    def list(self, text: str, ordered: bool, **attrs) -> str:
        self._list_level = attrs.get("level", 0) + 1
        self._list_type = "number" if ordered else "bullet"
        return ""

    def list_item(self, text: str) -> str:
        text = self._strip_html(text)
        self.blocks.append(Paragraph(
            runs=self._text_to_runs(text),
            list_level=self._list_level,
            list_type=self._list_type,
        ))
        return ""

    def thematic_break(self) -> str:
        self.blocks.append(HorizontalRule())
        return ""

    def table_entry(self, entry: dict) -> dict:
        # Accumulate table cells
        if not self._in_table:
            self._table_rows = []
            self._in_table = True
        return entry

    def table_cell(self, text: str, align: str | None = None, is_head: bool = False) -> str:
        text = self._strip_html(text)
        runs = [Run(text=text, bold=is_head)] if text else [Run(text="")]
        # Store cell data in a way we can process later
        if not hasattr(self, "_current_row"):
            self._current_row = []
        self._current_row.append(TableCell(blocks=[Paragraph(runs=runs)]))
        return ""

    def table_row(self, text: str) -> str:
        self._table_rows.append(TableRow(cells=getattr(self, "_current_row", [])))
        self._current_row = []
        return ""

    def table_end(self) -> str:
        if self._table_rows:
            self.blocks.append(Table(rows=self._table_rows))
        self._table_rows = []
        self._in_table = False
        return ""

    def image(self, src: str, alt: str = "", title: str | None = None) -> str:
        self.blocks.append(ImageReference(
            image_id="__external__",
            caption=alt or title,
        ))
        return ""

    def block_html(self, html: str) -> str:
        return ""

    def _strip_html(self, text: str) -> str:
        return re.sub(r"<[^>]+>", "", text)

    def _text_to_runs(self, text: str) -> list[Run]:
        # Parse **bold** and *italic*
        runs: list[Run] = []
        pattern = re.compile(r"(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)")
        last = 0
        for m in pattern.finditer(text):
            if m.start() > last:
                runs.append(Run(text=text[last:m.start()]))
            if m.group(2):  # ***bold italic***
                runs.append(Run(text=m.group(2), bold=True, italic=True))
            elif m.group(3):  # **bold**
                runs.append(Run(text=m.group(3), bold=True))
            elif m.group(4):  # *italic*
                runs.append(Run(text=m.group(4), italic=True))
            elif m.group(5):  # `code`
                runs.append(Run(text=m.group(5), font_name="Courier New"))
            last = m.end()
        if last < len(text):
            runs.append(Run(text=text[last:]))
        return runs or [Run(text=text)]


class MarkdownParser(BaseParser):
    def parse(self, file_path: str) -> Document:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            from app.utils.encoding import detect_and_read
            text = detect_and_read(file_path)
        except Exception as e:
            raise ParseError(f"无法读取 Markdown 文件: {e}")

        if not text.strip():
            return Document(sections=[Section(blocks=[Paragraph(runs=[Run(text="")])])])

        renderer = MarkdownToIRRenderer()
        markdown = mistune.create_markdown(renderer=renderer)
        markdown(text)

        return Document(
            sections=[Section(blocks=renderer.blocks)] if renderer.blocks else [Section()],
        )
