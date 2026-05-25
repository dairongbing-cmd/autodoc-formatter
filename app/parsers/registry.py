from app.parsers.base import BaseParser
from app.parsers.docx_parser import DocxParser
from app.parsers.markdown_parser import MarkdownParser
from app.parsers.txt_parser import TxtParser

_parsers: dict[str, BaseParser] = {
    ".docx": DocxParser(),
    ".txt": TxtParser(),
    ".md": MarkdownParser(),
}


def get_parser(extension: str) -> BaseParser:
    ext = extension.lower()
    if ext == ".markdown":
        ext = ".md"
    parser = _parsers.get(ext)
    if parser is None:
        raise ValueError(f"不支持的格式: {ext}")
    return parser
