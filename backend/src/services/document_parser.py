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


def _strip_inline_markers(text: str) -> str:
    return _INLINE_MARKERS.sub(r"\1", text).strip()


@dataclass(frozen=True)
class ParsedParagraph:
    text: str
    style: ParagraphStyle


class DocumentParser:
    def __init__(self, vision_agent_api_key: str) -> None:
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


def _parse_markdown(md_text: str) -> list[ParsedParagraph]:
    results: list[ParsedParagraph] = []
    buffer: list[str] = []
    in_code_block = False

    def flush_buffer() -> None:
        text = " ".join(buffer).strip()
        if text:
            results.append(ParsedParagraph(text=text, style=ParagraphStyle.NORMAL))
        buffer.clear()

    for line in md_text.split("\n"):
        stripped = line.strip()

        if _CODE_FENCE.match(stripped):
            flush_buffer()
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        if not stripped or _HORIZONTAL_RULE.match(stripped):
            flush_buffer()
            continue

        if _IMAGE_PATTERN.match(stripped) or _TABLE_ROW.match(stripped):
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

    flush_buffer()
    return results
