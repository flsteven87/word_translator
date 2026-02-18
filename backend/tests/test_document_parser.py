from io import BytesIO

from docx import Document

from src.services.document_parser import DocumentParser


def _make_docx(paragraphs: list[str]) -> bytes:
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_parse_extracts_paragraphs():
    content = _make_docx(["First paragraph.", "Second paragraph."])
    parser = DocumentParser()
    result = parser.parse(content)
    assert result == ["First paragraph.", "Second paragraph."]


def test_parse_skips_empty_paragraphs():
    content = _make_docx(["Hello.", "", "  ", "World."])
    parser = DocumentParser()
    result = parser.parse(content)
    assert result == ["Hello.", "World."]


def test_parse_extracts_headings():
    doc = Document()
    doc.add_heading("Title", level=1)
    doc.add_paragraph("Body text.")
    buf = BytesIO()
    doc.save(buf)
    parser = DocumentParser()
    result = parser.parse(buf.getvalue())
    assert result == ["Title", "Body text."]
