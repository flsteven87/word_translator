from io import BytesIO

from docx import Document
from docx.shared import Pt

from src.models.translation import ParagraphStyle, TranslationResult

_NON_EXPORTABLE_STYLES = frozenset({ParagraphStyle.FIGURE, ParagraphStyle.TABLE})

_STYLE_MAP: dict[ParagraphStyle, str] = {
    ParagraphStyle.TITLE: "Title",
    ParagraphStyle.HEADING_1: "Heading 1",
    ParagraphStyle.HEADING_2: "Heading 2",
    ParagraphStyle.HEADING_3: "Heading 3",
    ParagraphStyle.HEADING_4: "Heading 4",
    ParagraphStyle.NORMAL: "Normal",
}


class WordExporter:
    def export(
        self, result: TranslationResult, original_docx: bytes | None = None
    ) -> bytes:
        if original_docx is not None:
            return self._export_from_docx(result, original_docx)
        return self._export_from_scratch(result)

    def _export_from_docx(
        self, result: TranslationResult, original_docx: bytes
    ) -> bytes:
        doc = Document(BytesIO(original_docx))
        lookup = {p.original: p.translated for p in result.paragraphs}
        for paragraph in doc.paragraphs:
            translated = lookup.get(paragraph.text)
            if translated is None:
                continue
            if not paragraph.runs:
                paragraph.text = translated
                continue
            paragraph.runs[0].text = translated
            for run in paragraph.runs[1:]:
                run.text = ""
        buf = BytesIO()
        doc.save(buf)
        return buf.getvalue()

    def _export_from_scratch(self, result: TranslationResult) -> bytes:
        doc = Document()
        style = doc.styles["Normal"]
        font = style.font
        font.size = Pt(12)

        for para in result.paragraphs:
            if para.style in _NON_EXPORTABLE_STYLES:
                continue
            word_style = _STYLE_MAP[para.style]
            doc.add_paragraph(para.translated, style=word_style)

        buf = BytesIO()
        doc.save(buf)
        return buf.getvalue()
