import uuid
from pathlib import Path

from fastapi import UploadFile

from app.formatter.engine import FormatEngine
from app.formatter.presets import list_presets, load_preset
from app.models.ir import Document
from app.models.rules import FormattingRules
from app.parsers.registry import get_parser
from app.preview.html_renderer import HTMLRenderer
from app.services.storage import StorageService
from app.utils.validators import ValidationError, validate_docx_magic, validate_extension, validate_size


class Pipeline:
    def __init__(self, storage: StorageService):
        self.storage = storage
        self._documents: dict[str, Document] = {}
        self._rules: dict[str, FormattingRules] = {}
        self._filenames: dict[str, str] = {}
        self._detected_formats: dict[str, str] = {}

    async def ingest(self, file: UploadFile) -> dict:
        doc_id = uuid.uuid4().hex[:12]
        ext = validate_extension(file.filename or "")

        file_path = await self.storage.save_upload(doc_id, file)
        validate_size(str(file_path))

        if ext == ".docx":
            if not validate_docx_magic(str(file_path)):
                self.storage.cleanup_document(doc_id)
                raise ValidationError("文件不是有效的 .docx 格式")

        parser = get_parser(ext)
        document = parser.parse(str(file_path))

        self._documents[doc_id] = document
        self._filenames[doc_id] = file.filename or "unknown"
        self._detected_formats[doc_id] = ext.lstrip(".")

        counts = document.block_counts

        return {
            "doc_id": doc_id,
            "filename": file.filename,
            "size": Path(file_path).stat().st_size,
            "detected_format": ext.lstrip("."),
            "block_counts": counts,
        }

    def get_document(self, doc_id: str) -> Document | None:
        return self._documents.get(doc_id)

    def get_summary(self, doc_id: str) -> dict | None:
        if doc_id not in self._documents:
            return None
        return {
            "doc_id": doc_id,
            "filename": self._filenames.get(doc_id, ""),
            "detected_format": self._detected_formats.get(doc_id, ""),
            "block_counts": self._documents[doc_id].block_counts,
        }

    def set_rules(self, doc_id: str, rules_data: dict) -> FormattingRules:
        rules = FormattingRules(**rules_data)
        self._rules[doc_id] = rules
        return rules

    def get_rules(self, doc_id: str) -> FormattingRules | None:
        return self._rules.get(doc_id)

    async def preview(self, doc_id: str) -> str | None:
        doc = self._documents.get(doc_id)
        if doc is None:
            return None
        rules = self._rules.get(doc_id, FormattingRules())
        renderer = HTMLRenderer()
        return renderer.render(doc, rules)

    async def format(self, doc_id: str) -> dict:
        doc = self._documents.get(doc_id)
        if doc is None:
            raise ValueError("文档未找到")

        rules = self._rules.get(doc_id, FormattingRules())
        engine = FormatEngine(rules)
        output_bytes = engine.apply(doc)

        output_path = await self.storage.save_output(doc_id, output_bytes)

        return {
            "output_id": doc_id,
            "download_url": f"/api/documents/{doc_id}/download",
            "size": output_path.stat().st_size,
        }

    def cleanup(self, doc_id: str) -> None:
        self._documents.pop(doc_id, None)
        self._rules.pop(doc_id, None)
        self._filenames.pop(doc_id, None)
        self._detected_formats.pop(doc_id, None)
        self.storage.cleanup_document(doc_id)
