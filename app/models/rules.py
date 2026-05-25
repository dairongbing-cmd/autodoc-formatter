from typing import Literal, Optional

from pydantic import BaseModel, Field


class Margins(BaseModel):
    top_cm: float = 2.54
    bottom_cm: float = 2.54
    left_cm: float = 2.54
    right_cm: float = 2.54


class HeadingStyle(BaseModel):
    font_family: Optional[str] = None
    font_size_pt: Optional[float] = None
    bold: bool = True
    italic: bool = False
    color_hex: Optional[str] = None
    alignment: Optional[str] = None
    space_before_pt: Optional[float] = None
    space_after_pt: Optional[float] = None


class FontRules(BaseModel):
    family: str = "Times New Roman"
    size_pt: float = 12.0
    color_hex: str = "#000000"
    bold_default: bool = False
    italic_default: bool = False


class ParagraphRules(BaseModel):
    alignment: Literal["left", "center", "right", "justify"] = "left"
    line_spacing: float = 1.15
    first_line_indent_cm: Optional[float] = None
    space_before_pt: float = 0.0
    space_after_pt: float = 6.0


class PageRules(BaseModel):
    size: Literal["A4", "Letter"] = "A4"
    orientation: Literal["portrait", "landscape"] = "portrait"
    margins_cm: Margins = Field(default_factory=Margins)


class HeaderFooterRules(BaseModel):
    enabled: bool = False
    text: Optional[str] = None
    show_page_numbers: bool = False


class ImageRules(BaseModel):
    max_width_cm: Optional[float] = 16.0
    alignment: Literal["left", "center", "right"] = "center"
    add_captions: bool = True


class FormattingRules(BaseModel):
    preset_name: Optional[str] = None
    font: FontRules = Field(default_factory=FontRules)
    paragraph: ParagraphRules = Field(default_factory=ParagraphRules)
    page: PageRules = Field(default_factory=PageRules)
    headings: dict[int, HeadingStyle] = Field(default_factory=lambda: {
        i: HeadingStyle(font_size_pt=s, bold=True)
        for i, s in [(1, 22), (2, 18), (3, 16), (4, 14), (5, 12), (6, 11)]
    })
    header: HeaderFooterRules = Field(default_factory=HeaderFooterRules)
    footer: HeaderFooterRules = Field(
        default_factory=lambda: HeaderFooterRules(show_page_numbers=True)
    )
    images: ImageRules = Field(default_factory=ImageRules)
