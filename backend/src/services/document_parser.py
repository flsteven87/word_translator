from dataclasses import dataclass
from io import BytesIO

from docx import Document

from src.models.translation import ParagraphStyle

_STYLE_MAP: dict[str, ParagraphStyle] = {
    "Title": ParagraphStyle.TITLE,
    "Heading 1": ParagraphStyle.HEADING_1,
    "Heading 2": ParagraphStyle.HEADING_2,
    "Heading 3": ParagraphStyle.HEADING_3,
    "Heading 4": ParagraphStyle.HEADING_4,
}


@dataclass(frozen=True)
class ParsedParagraph:
    text: str
    style: ParagraphStyle


class DocumentParser:
    def parse(self, file_content: bytes) -> list[ParsedParagraph]:
        doc = Document(BytesIO(file_content))
        results: list[ParsedParagraph] = []
        for p in doc.paragraphs:
            if not p.text.strip():
                continue
            style_name = p.style.name
            style = _STYLE_MAP.get(style_name, ParagraphStyle.NORMAL)
            results.append(ParsedParagraph(text=p.text, style=style))
        return results
