from io import BytesIO

from docx import Document

from src.models.translation import (
    ParagraphStyle,
    TranslatedParagraph,
    TranslationResult,
)
from src.services.word_exporter import WordExporter


def _make_result(**kwargs):
    defaults = dict(
        filename="test.docx",
        paragraphs=[
            TranslatedParagraph(original="Hello", translated="你好"),
            TranslatedParagraph(original="World", translated="世界"),
        ],
    )
    defaults.update(kwargs)
    return TranslationResult(**defaults)


def _make_docx(paragraphs: list[str]) -> bytes:
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_export_from_scratch_chinese_only():
    result = _make_result()
    exporter = WordExporter()
    docx_bytes = exporter.export(result)

    doc = Document(BytesIO(docx_bytes))
    texts = [p.text for p in doc.paragraphs if p.text]
    assert texts == ["你好", "世界"]


def test_export_from_scratch_applies_styles():
    result = _make_result(
        paragraphs=[
            TranslatedParagraph(
                original="Title", translated="標題", style=ParagraphStyle.TITLE
            ),
            TranslatedParagraph(
                original="Body", translated="內文", style=ParagraphStyle.NORMAL
            ),
        ],
    )
    exporter = WordExporter()
    docx_bytes = exporter.export(result)

    doc = Document(BytesIO(docx_bytes))
    non_empty = [p for p in doc.paragraphs if p.text]
    assert non_empty[0].style.name == "Title"
    assert non_empty[1].style.name == "Normal"


def test_export_from_docx_preserves_formatting():
    original_docx = _make_docx(["Hello", "World"])
    result = _make_result()
    exporter = WordExporter()
    docx_bytes = exporter.export(result, original_docx=original_docx)

    doc = Document(BytesIO(docx_bytes))
    texts = [p.text for p in doc.paragraphs if p.text]
    assert texts == ["你好", "世界"]


def test_export_from_docx_unmatched_paragraphs_unchanged():
    original_docx = _make_docx(["Hello", "Extra paragraph"])
    result = _make_result(
        paragraphs=[
            TranslatedParagraph(original="Hello", translated="你好"),
        ],
    )
    exporter = WordExporter()
    docx_bytes = exporter.export(result, original_docx=original_docx)

    doc = Document(BytesIO(docx_bytes))
    texts = [p.text for p in doc.paragraphs if p.text]
    assert "你好" in texts
    assert "Extra paragraph" in texts


def test_export_from_scratch_skips_figure_and_table():
    result = _make_result(
        paragraphs=[
            TranslatedParagraph(
                original="Hello", translated="你好", style=ParagraphStyle.NORMAL
            ),
            TranslatedParagraph(
                original="<::chart::>",
                translated="",
                style=ParagraphStyle.FIGURE,
            ),
            TranslatedParagraph(
                original="<table><tr><td>X</td></tr></table>",
                translated="",
                style=ParagraphStyle.TABLE,
            ),
            TranslatedParagraph(
                original="World", translated="世界", style=ParagraphStyle.NORMAL
            ),
        ],
    )
    exporter = WordExporter()
    docx_bytes = exporter.export(result)

    doc = Document(BytesIO(docx_bytes))
    texts = [p.text for p in doc.paragraphs if p.text]
    assert texts == ["你好", "世界"]
    # Verify figure/table content is not in the export
    all_text = " ".join(texts)
    assert "<::chart::>" not in all_text
    assert "<table>" not in all_text
