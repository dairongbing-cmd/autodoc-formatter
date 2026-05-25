from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional, Union


@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    font_name: Optional[str] = None
    font_size_pt: Optional[float] = None
    font_color_hex: Optional[str] = None


@dataclass
class Paragraph:
    runs: list[Run] = field(default_factory=list)
    style_hint: Optional[str] = None  # "heading1".."heading6", "quote", "code"
    alignment: Optional[str] = None
    list_level: int = 0
    list_type: Optional[str] = None  # "bullet" | "number"


@dataclass
class TableCell:
    blocks: list["BlockNode"] = field(default_factory=list)


@dataclass
class TableRow:
    cells: list[TableCell] = field(default_factory=list)


@dataclass
class Table:
    rows: list[TableRow] = field(default_factory=list)
    caption: Optional[str] = None


@dataclass
class InlineImage:
    image_id: str
    data: bytes
    content_type: str
    filename: str
    width_px: Optional[int] = None
    height_px: Optional[int] = None


@dataclass
class ImageReference:
    image_id: str
    caption: Optional[str] = None
    alignment: Optional[str] = None  # "left" | "center" | "right"
    width_px: Optional[int] = None
    height_px: Optional[int] = None


@dataclass
class PageBreak:
    pass


@dataclass
class HorizontalRule:
    pass


BlockNode = Union[Paragraph, Table, ImageReference, PageBreak, HorizontalRule]


@dataclass
class Section:
    blocks: list[BlockNode] = field(default_factory=list)


@dataclass
class DocumentMeta:
    title: str = ""
    author: str = ""


@dataclass
class Document:
    metadata: DocumentMeta = field(default_factory=DocumentMeta)
    sections: list[Section] = field(default_factory=list)
    images: list[InlineImage] = field(default_factory=list)

    @property
    def block_counts(self) -> dict:
        counts = {"paragraphs": 0, "tables": 0, "images": 0, "headings": 0}
        for section in self.sections:
            for block in section.blocks:
                if isinstance(block, Paragraph):
                    counts["paragraphs"] += 1
                    if block.style_hint and block.style_hint.startswith("heading"):
                        counts["headings"] += 1
                elif isinstance(block, Table):
                    counts["tables"] += 1
                elif isinstance(block, ImageReference):
                    counts["images"] += 1
        return counts
