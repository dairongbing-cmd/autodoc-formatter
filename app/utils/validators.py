import os
from pathlib import Path

from app.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES


class ValidationError(Exception):
    pass


def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".markdown":
        ext = ".md"
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"不支持的文件格式: {ext}。支持: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    return ext


def validate_size(file_path: str) -> int:
    size = os.path.getsize(file_path)
    if size > MAX_UPLOAD_BYTES:
        raise ValidationError(
            f"文件过大: {size / 1024 / 1024:.1f}MB。最大允许: {MAX_UPLOAD_BYTES / 1024 / 1024:.0f}MB"
        )
    if size == 0:
        raise ValidationError("文件为空")
    return size


def validate_docx_magic(file_path: str) -> bool:
    with open(file_path, "rb") as f:
        header = f.read(4)
    return header[:2] == b"PK"
