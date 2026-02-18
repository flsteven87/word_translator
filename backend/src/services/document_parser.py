import logging
import re
from dataclasses import dataclass
from io import BytesIO

import pymupdf
import pymupdf4llm
from docx import Document
from landingai_ade import LandingAIADE

from src.core.exceptions import InputValidationError
from src.models.translation import ParagraphStyle

logger = logging.getLogger(__name__)

_DOCX_STYLE_MAP: dict[str, ParagraphStyle] = {
    "Title": ParagraphStyle.TITLE,
    "Heading 1": ParagraphStyle.HEADING_1,
    "Heading 2": ParagraphStyle.HEADING_2,
    "Heading 3": ParagraphStyle.HEADING_3,
    "Heading 4": ParagraphStyle.HEADING_4,
}

_MD_STYLE_MAP: dict[int, ParagraphStyle] = {
    1: ParagraphStyle.TITLE,
    2: ParagraphStyle.HEADING_1,
    3: ParagraphStyle.HEADING_2,
    4: ParagraphStyle.HEADING_3,
    5: ParagraphStyle.HEADING_4,
}

_HEADING_PATTERN = re.compile(r"^(#{1,5})\s+(.+)$")
_IMAGE_PATTERN = re.compile(r"^!\[.*?\]\(.*?\)$")
_HORIZONTAL_RULE = re.compile(r"^-{3,}$")
_CODE_FENCE = re.compile(r"^`{3,}")
_TABLE_ROW = re.compile(r"^\|.+\|$")
_LIST_ITEM = re.compile(r"^(?:[-*+]|\d+\.)\s+(.+)$")
_INLINE_MARKERS = re.compile(r"\*{1,3}(.+?)\*{1,3}")
_HTML_ANCHOR = re.compile(r"^<a\s+id=['\"].*?['\"]>\s*</a>$")
_HTML_ANCHOR_PREFIX = re.compile(r"^<a\s+id=['\"].*?['\"]>\s*</a>\s*")
_HTML_COMMENT = re.compile(r"^<!--.*?-->$")
_HTML_TAGS = re.compile(r"</?(?:sup|sub|em|strong|span|a|i|b)[^>]*>")

_ADE_DELIMITER = re.compile(r"<::.*?::>")
_HTML_TABLE_OPEN = re.compile(r"<table[\s>]", re.IGNORECASE)
_HTML_TABLE_CLOSE = re.compile(r"</table>", re.IGNORECASE)

_CHUNK_FIGURE_TYPES = frozenset({
    "figure", "logo", "card", "attestation", "scanCode",
})
_CHUNK_SKIP_TYPES = frozenset({
    "marginalia", "pageHeader", "pageFooter", "pageNumber",
})


def _strip_inline_markers(text: str) -> str:
    text = _HTML_TAGS.sub("", text)
    return _INLINE_MARKERS.sub(r"\1", text).strip()


@dataclass(frozen=True)
class ParsedParagraph:
    text: str
    style: ParagraphStyle


class DocumentParser:
    def __init__(self, vision_agent_api_key: str | None = None) -> None:
        self._ade_client: LandingAIADE | None = None
        if vision_agent_api_key:
            self._ade_client = LandingAIADE(
                apikey=vision_agent_api_key,
                environment="production",
            )

    def parse(self, file_content: bytes, filename: str) -> list[ParsedParagraph]:
        ext = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""
        if ext == "pdf":
            return self._parse_pdf(file_content)
        if ext == "docx":
            return self._parse_docx(file_content)
        raise InputValidationError(f"Unsupported file format: .{ext}")

    def _parse_docx(self, file_content: bytes) -> list[ParsedParagraph]:
        doc = Document(BytesIO(file_content))
        results: list[ParsedParagraph] = []
        for p in doc.paragraphs:
            if not p.text.strip():
                continue
            style_name = p.style.name
            style = _DOCX_STYLE_MAP.get(style_name, ParagraphStyle.NORMAL)
            results.append(ParsedParagraph(text=p.text, style=style))
        return results

    def _parse_pdf(self, file_content: bytes) -> list[ParsedParagraph]:
        if not self._ade_client:
            return self._parse_pdf_with_pymupdf(file_content)
        try:
            return self._parse_pdf_with_ade(file_content)
        except InputValidationError:
            raise
        except Exception as exc:
            logger.warning("ADE parsing failed, falling back to pymupdf4llm: %s", exc)
            return self._parse_pdf_with_pymupdf(file_content)

    def _parse_pdf_with_ade(self, file_content: bytes) -> list[ParsedParagraph]:
        response = self._ade_client.parse(
            document=file_content,
            model="dpt-2-latest",
        )
        results = _parse_ade_chunks(response.chunks)
        if not results:
            raise ValueError("ADE returned no usable chunks")
        return results

    def _parse_pdf_with_pymupdf(self, file_content: bytes) -> list[ParsedParagraph]:
        with pymupdf.open(stream=file_content, filetype="pdf") as doc:
            if doc.page_count == 0:
                raise InputValidationError("PDF file contains no pages")
            hdr_info = pymupdf4llm.IdentifyHeaders(doc, max_levels=4)
            md_text = pymupdf4llm.to_markdown(
                doc,
                hdr_info=hdr_info,
                margins=(0, 50, 0, 50),
            )
        results = _parse_markdown(md_text)
        if not results:
            raise InputValidationError(
                "No text could be extracted from this PDF. "
                "It may be a scanned document — please use a text-based PDF."
            )
        return results


def _parse_ade_chunks(chunks: list) -> list[ParsedParagraph]:
    results: list[ParsedParagraph] = []
    for chunk in chunks:
        markdown = chunk.markdown.strip() if chunk.markdown else ""
        markdown = _HTML_ANCHOR_PREFIX.sub("", markdown).strip()
        if not markdown:
            continue
        chunk_type = chunk.type
        if chunk_type in _CHUNK_SKIP_TYPES:
            continue
        if chunk_type in _CHUNK_FIGURE_TYPES:
            results.append(ParsedParagraph(text=markdown, style=ParagraphStyle.FIGURE))
        elif chunk_type == "table":
            results.append(ParsedParagraph(text=markdown, style=ParagraphStyle.TABLE))
        else:
            results.extend(_parse_markdown(markdown))
    return results


def _parse_markdown(md_text: str) -> list[ParsedParagraph]:
    results: list[ParsedParagraph] = []
    buffer: list[str] = []
    in_code_block = False
    in_html_table = False
    table_buffer: list[str] = []

    def flush_buffer() -> None:
        text = " ".join(buffer).strip()
        if text:
            results.append(ParsedParagraph(text=text, style=ParagraphStyle.NORMAL))
        buffer.clear()

    def flush_table() -> None:
        nonlocal in_html_table
        text = "\n".join(table_buffer).strip()
        if text:
            results.append(ParsedParagraph(text=text, style=ParagraphStyle.TABLE))
        table_buffer.clear()
        in_html_table = False

    for line in md_text.split("\n"):
        stripped = line.strip()

        if in_html_table:
            table_buffer.append(stripped)
            if _HTML_TABLE_CLOSE.search(stripped):
                flush_table()
            continue

        if _HTML_TABLE_OPEN.search(stripped):
            flush_buffer()
            in_html_table = True
            table_buffer.append(stripped)
            if _HTML_TABLE_CLOSE.search(stripped):
                flush_table()
            continue

        if _CODE_FENCE.match(stripped):
            flush_buffer()
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        if not stripped or _HORIZONTAL_RULE.match(stripped):
            flush_buffer()
            continue

        if (
            _HTML_ANCHOR.match(stripped)
            or _HTML_COMMENT.match(stripped)
            or _IMAGE_PATTERN.match(stripped)
            or _TABLE_ROW.match(stripped)
        ):
            continue

        if _ADE_DELIMITER.search(stripped):
            flush_buffer()
            results.append(ParsedParagraph(text=stripped, style=ParagraphStyle.FIGURE))
            continue

        heading_match = _HEADING_PATTERN.match(stripped)
        if heading_match:
            flush_buffer()
            level = len(heading_match.group(1))
            text = _strip_inline_markers(heading_match.group(2))
            style = _MD_STYLE_MAP[level]
            if text:
                results.append(ParsedParagraph(text=text, style=style))
            continue

        list_match = _LIST_ITEM.match(stripped)
        if list_match:
            flush_buffer()
            text = _strip_inline_markers(list_match.group(1))
            if text:
                results.append(ParsedParagraph(text=text, style=ParagraphStyle.NORMAL))
            continue

        clean = _strip_inline_markers(stripped)
        if clean:
            buffer.append(clean)

    if in_html_table:
        flush_table()
    flush_buffer()
    return results
