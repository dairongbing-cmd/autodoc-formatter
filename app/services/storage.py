import shutil
import time
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.config import UPLOAD_DIR, OUTPUT_DIR, STALE_CLEANUP_MINUTES


class StorageService:
    def __init__(self):
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def _doc_upload_dir(self, doc_id: str) -> Path:
        path = UPLOAD_DIR / doc_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _doc_output_dir(self, doc_id: str) -> Path:
        path = OUTPUT_DIR / doc_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def save_upload(self, doc_id: str, file: UploadFile) -> Path:
        upload_dir = self._doc_upload_dir(doc_id)
        ext = Path(file.filename or "upload").suffix or ".bin"
        dest = upload_dir / f"original{ext}"
        async with aiofiles.open(dest, "wb") as f:
            content = await file.read()
            await f.write(content)
        return dest

    async def save_output(self, doc_id: str, data: bytes) -> Path:
        output_dir = self._doc_output_dir(doc_id)
        dest = output_dir / "formatted.docx"
        async with aiofiles.open(dest, "wb") as f:
            await f.write(data)
        return dest

    def get_upload_path(self, doc_id: str) -> Path | None:
        upload_dir = UPLOAD_DIR / doc_id
        if not upload_dir.exists():
            return None
        files = list(upload_dir.glob("original.*"))
        return files[0] if files else None

    def get_output_path(self, doc_id: str) -> Path | None:
        dest = OUTPUT_DIR / doc_id / "formatted.docx"
        return dest if dest.exists() else None

    def get_output_size(self, doc_id: str) -> int:
        path = self.get_output_path(doc_id)
        return path.stat().st_size if path else 0

    def cleanup_document(self, doc_id: str) -> None:
        for base in [UPLOAD_DIR, OUTPUT_DIR]:
            doc_dir = base / doc_id
            if doc_dir.exists():
                shutil.rmtree(doc_dir)

    def cleanup_stale(self) -> int:
        removed = 0
        cutoff = time.time() - STALE_CLEANUP_MINUTES * 60
        for base in [UPLOAD_DIR, OUTPUT_DIR]:
            if not base.exists():
                continue
            for doc_dir in base.iterdir():
                if doc_dir.is_dir():
                    mtime = doc_dir.stat().st_mtime
                    if mtime < cutoff:
                        shutil.rmtree(doc_dir)
                        removed += 1
        return removed
