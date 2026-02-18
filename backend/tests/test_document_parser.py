from io import BytesIO

from docx import Document

from src.models.translation import ParagraphStyle
from src.services.document_parser import DocumentParser, ParsedParagraph


def _make_docx(paragraphs: list[str]) -> bytes:
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_parse_extracts_paragraphs():
    content = _make_docx(["First paragraph.", "Second paragraph."])
    result = DocumentParser(vision_agent_api_key="test-key").parse(content, "test.docx")
    assert len(result) == 2
    assert result[0] == ParsedParagraph(text="First paragraph.", style=ParagraphStyle.NORMAL)
    assert result[1] == ParsedParagraph(text="Second paragraph.", style=ParagraphStyle.NORMAL)


def test_parse_skips_empty_paragraphs():
    content = _make_docx(["Hello.", "", "  ", "World."])
    result = DocumentParser(vision_agent_api_key="test-key").parse(content, "test.docx")
    assert len(result) == 2
    assert result[0].text == "Hello."
    assert result[1].text == "World."


def test_parse_extracts_headings():
    doc = Document()
    doc.add_heading("Title", level=1)
    doc.add_paragraph("Body text.")
    buf = BytesIO()
    doc.save(buf)
    result = DocumentParser(vision_agent_api_key="test-key").parse(buf.getvalue(), "test.docx")
    assert len(result) == 2
    assert result[0] == ParsedParagraph(text="Title", style=ParagraphStyle.HEADING_1)
    assert result[1] == ParsedParagraph(text="Body text.", style=ParagraphStyle.NORMAL)
