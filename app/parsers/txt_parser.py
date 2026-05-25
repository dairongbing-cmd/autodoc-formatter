from app.models.ir import Document, Section, Paragraph, Run
from app.parsers.base import BaseParser, ParseError
from app.utils.encoding import detect_and_read


class TxtParser(BaseParser):
    def parse(self, file_path: str) -> Document:
        try:
            text = detect_and_read(file_path)
        except Exception as e:
            raise ParseError(f"无法读取文本文件: {e}")

        if not text.strip():
            return Document(
                sections=[Section(blocks=[Paragraph(runs=[Run(text="")])])]
            )

        sections: list[Section] = []
        current_section = Section()

        paragraphs = text.split("\n\n")
        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            lines = para_text.split("\n")
            runs: list[Run] = []
            for i, line in enumerate(lines):
                if i > 0:
                    runs.append(Run(text="\n"))
                runs.append(Run(text=line))

            current_section.blocks.append(Paragraph(runs=runs))

        sections.append(current_section)
        return Document(sections=sections)
