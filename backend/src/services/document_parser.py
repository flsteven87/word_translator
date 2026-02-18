from io import BytesIO

from docx import Document


class DocumentParser:
    def parse(self, file_content: bytes) -> list[str]:
        doc = Document(BytesIO(file_content))
        return [p.text for p in doc.paragraphs if p.text.strip()]
