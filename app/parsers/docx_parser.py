import uuid
from pathlib import Path

from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from app.models.ir import (
    BlockNode,
    Document,
    DocumentMeta,
    HorizontalRule,
    ImageReference,
    InlineImage,
    PageBreak,
    Paragraph,
    Run,
    Section,
    Table,
    TableCell,
    TableRow,
)
from app.parsers.base import BaseParser, ParseError

HEADING_STYLES = {}
for i in range(1, 7):
    for variant in [f"Heading {i}", f"heading {i}", f"Heading{i}", f"heading{i}"]:
        HEADING_STYLES[variant] = f"heading{i}"


class DocxParser(BaseParser):
    def parse(self, file_path: str) -> Document:
        try:
            docx = DocxDocument(file_path)
        except Exception as e:
            raise ParseError(f"无法解析 .docx 文件，文件可能已损坏: {e}")

        meta = DocumentMeta()
        if docx.core_properties.title:
            meta.title = docx.core_properties.title
        if docx.core_properties.author:
            meta.author = docx.core_properties.author

        section = Section()
        images: list[InlineImage] = []
        image_map: dict[str, str] = {}  # rId -> image_id

        self._extract_images(docx, file_path, images, image_map)

        for element in docx.element.body:
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

            if tag == "p":
                para = self._parse_paragraph(element, image_map)
                if para is not None:
                    section.blocks.append(para)
            elif tag == "tbl":
                table = self._parse_table(element, image_map)
                section.blocks.append(table)

        return Document(
            metadata=meta,
            sections=[section] if section.blocks else [Section()],
            images=images,
        )

    def _extract_images(
        self,
        docx: DocxDocument,
        file_path: str,
        images: list[InlineImage],
        image_map: dict[str, str],
    ) -> None:
        src_dir = Path(file_path).parent
        for rel in docx.part.rels.values():
            if "image" in rel.reltype:
                img_id = str(uuid.uuid4())[:8]
                image_map[rel.rId] = img_id
                try:
                    data = rel.target_part.blob
                except Exception:
                    continue
                content_type = rel.target_part.content_type or "image/png"
                filename = Path(rel.target_ref).name if rel.target_ref else f"{img_id}.png"
                images.append(InlineImage(
                    image_id=img_id,
                    data=data,
                    content_type=content_type,
                    filename=filename,
                ))

    def _parse_paragraph(self, element, image_map: dict[str, str]) -> BlockNode | None:
        style = element.find(qn("w:pPr"))
        style_name = ""
        if style is not None:
            pstyle = style.find(qn("w:pStyle"))
            if pstyle is not None:
                style_name = pstyle.get(qn("w:val"), "")

        # Check for images in paragraph
        images_in_para = element.findall(".//" + qn("w:drawing"))
        for drawing in images_in_para:
            blip = drawing.find(".//" + qn("a:blip"))
            if blip is not None:
                embed = blip.get(qn("r:embed"))
                if embed and embed in image_map:
                    return ImageReference(image_id=image_map[embed])

        # Check for inline images
        for blip_elem in element.findall(".//" + qn("a:blip")):
            embed = blip_elem.get(qn("r:embed"))
            if embed and embed in image_map:
                return ImageReference(image_id=image_map[embed])

        runs: list[Run] = []
        for r_elem in element.findall(qn("w:r")):
            text_parts = r_elem.findall(qn("w:t"))
            text = "".join(t.text or "" for t in text_parts)
            if not text:
                # Check for line break
                br = r_elem.find(qn("w:br"))
                if br is not None:
                    runs.append(Run(text="\n"))
                continue

            rpr = r_elem.find(qn("w:rPr"))
            bold = False
            italic = False
            underline = False
            strikethrough = False
            font_name = None
            font_size_pt = None
            font_color_hex = None

            if rpr is not None:
                bold = rpr.find(qn("w:b")) is not None
                italic = rpr.find(qn("w:i")) is not None
                underline = rpr.find(qn("w:u")) is not None
                strikethrough = rpr.find(qn("w:strike")) is not None

                rfonts = rpr.find(qn("w:rFonts"))
                if rfonts is not None:
                    font_name = rfonts.get(qn("w:ascii")) or rfonts.get(qn("w:eastAsia"))

                sz = rpr.find(qn("w:sz"))
                if sz is not None:
                    val = sz.get(qn("w:val"))
                    if val:
                        font_size_pt = float(val) / 2.0

                color = rpr.find(qn("w:color"))
                if color is not None:
                    val = color.get(qn("w:val"))
                    if val and val != "auto":
                        font_color_hex = f"#{val}"

            runs.append(Run(
                text=text,
                bold=bold,
                italic=italic,
                underline=underline,
                strikethrough=strikethrough,
                font_name=font_name,
                font_size_pt=font_size_pt,
                font_color_hex=font_color_hex,
            ))

        if not runs:
            runs.append(Run(text=""))

        style_hint = HEADING_STYLES.get(style_name)
        return Paragraph(runs=runs, style_hint=style_hint)

    def _parse_table(self, element, image_map: dict[str, str]) -> Table:
        rows: list[TableRow] = []
        for tr in element.findall(qn("w:tr")):
            cells: list[TableCell] = []
            for tc in tr.findall(qn("w:tc")):
                blocks: list[BlockNode] = []
                for p_elem in tc.findall(qn("w:p")):
                    para = self._parse_paragraph(p_elem, image_map)
                    if para is not None:
                        blocks.append(para)
                cells.append(TableCell(blocks=blocks))
            rows.append(TableRow(cells=cells))
        return Table(rows=rows)
