from io import BytesIO
from unittest.mock import MagicMock, patch

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


def test_parse_pdf_uses_ade_when_available():
    fake_response = MagicMock()
    fake_response.markdown = "# Title\n\nFirst paragraph.\n\nSecond paragraph."

    parser = DocumentParser(vision_agent_api_key="test-key")
    with patch.object(parser._ade_client, "parse", return_value=fake_response) as mock_parse:
        result = parser.parse(b"fake-pdf-bytes", "test.pdf")

    mock_parse.assert_called_once()
    assert len(result) == 3
    assert result[0] == ParsedParagraph(text="Title", style=ParagraphStyle.TITLE)
    assert result[1] == ParsedParagraph(text="First paragraph.", style=ParagraphStyle.NORMAL)
    assert result[2] == ParsedParagraph(text="Second paragraph.", style=ParagraphStyle.NORMAL)


def test_parse_pdf_falls_back_to_pymupdf_on_ade_failure():
    parser = DocumentParser(vision_agent_api_key="test-key")

    with patch.object(parser._ade_client, "parse", side_effect=Exception("API down")), \
         patch("src.services.document_parser.pymupdf4llm") as mock_pymupdf4llm, \
         patch("src.services.document_parser.pymupdf") as mock_pymupdf:
        mock_doc = MagicMock()
        mock_doc.page_count = 1
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_pymupdf.open.return_value = mock_doc
        mock_pymupdf4llm.IdentifyHeaders.return_value = {}
        mock_pymupdf4llm.to_markdown.return_value = "# Fallback Title\n\nFallback body."

        result = parser.parse(b"fake-pdf-bytes", "test.pdf")

    assert len(result) == 2
    assert result[0].text == "Fallback Title"
    assert result[1].text == "Fallback body."
