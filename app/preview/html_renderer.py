import base64

from app.models.ir import (
    Document,
    HorizontalRule,
    ImageReference,
    PageBreak,
    Paragraph,
    Run,
    Table,
)
from app.models.rules import FormattingRules


class HTMLRenderer:
    def render(self, document: Document, rules: FormattingRules) -> str:
        body = []
        for section in document.sections:
            body.append(self._render_section(section, rules, document))

        css = self._build_css(rules)
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><style>{css}</style></head>
<body>{"".join(body)}</body>
</html>"""

    def _render_section(self, section, rules: FormattingRules, document: Document) -> str:
        parts = []
        for block in section.blocks:
            if isinstance(block, Paragraph):
                parts.append(self._render_paragraph(block, rules))
            elif isinstance(block, Table):
                parts.append(self._render_table(block, rules))
            elif isinstance(block, ImageReference):
                parts.append(self._render_image(block, document))
            elif isinstance(block, PageBreak):
                parts.append('<div class="page-break"></div>')
            elif isinstance(block, HorizontalRule):
                parts.append("<hr>")
        return "".join(parts)

    def _render_paragraph(self, para: Paragraph, rules: FormattingRules) -> str:
        if para.style_hint and para.style_hint.startswith("heading"):
            level = int(para.style_hint[-1])
            hs = rules.headings.get(level)
            style = ""
            if hs:
                if hs.font_family:
                    style += f"font-family:{hs.font_family};"
                if hs.font_size_pt:
                    style += f"font-size:{hs.font_size_pt}pt;"
                if hs.color_hex:
                    style += f"color:{hs.color_hex};"
                style += f"font-weight:{'bold' if hs.bold else 'normal'};"
                style += f"font-style:{'italic' if hs.italic else 'normal'};"
                if hs.alignment:
                    style += f"text-align:{hs.alignment};"
            text = "".join(r.text for r in para.runs)
            return f"<h{level} style='{style}'>{self._escape(text)}</h{level}>"

        # Build inline-styled runs
        runs_html = []
        for r in para.runs:
            style = ""
            font = r.font_name or rules.font.family
            style += f"font-family:{font};"
            size = r.font_size_pt if r.font_size_pt is not None else rules.font.size_pt
            style += f"font-size:{size}pt;"
            color = r.font_color_hex or rules.font.color_hex
            style += f"color:{color};"
            if r.bold:
                style += "font-weight:bold;"
            if r.italic:
                style += "font-style:italic;"
            if r.underline:
                style += "text-decoration:underline;"
            runs_html.append(f"<span style='{style}'>{self._escape(r.text)}</span>")

        text = "".join(runs_html) or "&nbsp;"

        # Paragraph container style
        p_style = ""
        pr = rules.paragraph
        p_style += f"text-align:{para.alignment or pr.alignment};"
        p_style += f"line-height:{pr.line_spacing};"
        if pr.first_line_indent_cm:
            p_style += f"text-indent:{pr.first_line_indent_cm}cm;"
        p_style += f"margin-top:{pr.space_before_pt}pt;"
        p_style += f"margin-bottom:{pr.space_after_pt}pt;"

        tag = "p"
        if para.style_hint == "code":
            tag = "pre"
            p_style += "background:#f4f4f4;padding:12px;border-radius:4px;"
        elif para.style_hint == "quote":
            p_style += "border-left:3px solid #ccc;padding-left:16px;margin-left:24px;"

        return f"<{tag} style='{p_style}'>{text}</{tag}>"

    def _render_table(self, table: Table, rules: FormattingRules) -> str:
        if not table.rows:
            return ""
        html = '<table style="border-collapse:collapse;width:100%;margin:12px 0;">'
        for row in table.rows:
            html += "<tr>"
            for cell in row.cells:
                cell_text = ""
                for block in cell.blocks:
                    if isinstance(block, Paragraph):
                        cell_text += "".join(r.text for r in block.runs)
                html += f'<td style="border:1px solid #ccc;padding:8px;">{self._escape(cell_text)}</td>'
            html += "</tr>"
        html += "</table>"
        return html

    def _render_image(self, img_ref: ImageReference, document: Document) -> str:
        inline_img = None
        for img in document.images:
            if img.image_id == img_ref.image_id:
                inline_img = img
                break
        if inline_img:
            b64 = base64.b64encode(inline_img.data).decode()
            src = f"data:{inline_img.content_type};base64,{b64}"
        else:
            return f"<p>[图片: {img_ref.caption or img_ref.image_id}]</p>"

        max_w = "100%"
        if img_ref.width_px:
            max_w = f"{min(img_ref.width_px, 800)}px"
        html = f'<div style="text-align:center;margin:12px 0;">'
        html += f'<img src="{src}" style="max-width:{max_w};height:auto;" />'
        if img_ref.caption:
            html += f'<p style="font-style:italic;font-size:10pt;color:#666;">{self._escape(img_ref.caption)}</p>'
        html += "</div>"
        return html

    def _build_css(self, rules: FormattingRules) -> str:
        m = rules.page.margins_cm
        size = rules.page.size
        w_cm = 21.0 if size == "A4" else 21.59
        return f"""
body {{
    font-family: {rules.font.family};
    font-size: {rules.font.size_pt}pt;
    color: {rules.font.color_hex};
    max-width: {w_cm - m.left_cm - m.right_cm}cm;
    margin: 0 auto;
    padding: {m.top_cm}cm {m.right_cm}cm {m.bottom_cm}cm {m.left_cm}cm;
    background: #fff;
    line-height: {rules.paragraph.line_spacing};
}}
h1, h2, h3, h4, h5, h6 {{ margin-top: 0.8em; margin-bottom: 0.4em; }}
.page-break {{ page-break-after: always; margin: 20px 0; border: none; }}
hr {{ border: none; border-top: 1px solid #ccc; margin: 12px 0; }}
"""

    @staticmethod
    def _escape(text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
