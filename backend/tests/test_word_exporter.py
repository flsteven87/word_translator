from io import BytesIO

from docx import Document

from src.models.translation import TranslatedParagraph, TranslationResult
from src.services.word_exporter import WordExporter


def test_export_creates_valid_docx():
    result = TranslationResult(
        filename="test.docx",
        paragraphs=[
            TranslatedParagraph(original="Hello", translated="你好"),
            TranslatedParagraph(original="World", translated="世界"),
        ],
    )
    exporter = WordExporter()
    docx_bytes = exporter.export(result)

    doc = Document(BytesIO(docx_bytes))
    tables = doc.tables
    assert len(tables) == 1

    table = tables[0]
    # Header row + 2 data rows
    assert len(table.rows) == 3
    assert table.rows[0].cells[0].text == "English (Original)"
    assert table.rows[0].cells[1].text == "中文 (Translation)"
    assert table.rows[1].cells[0].text == "Hello"
    assert table.rows[1].cells[1].text == "你好"
    assert table.rows[2].cells[0].text == "World"
    assert table.rows[2].cells[1].text == "世界"
