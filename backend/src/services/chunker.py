from dataclasses import dataclass

from src.models.translation import ParagraphStyle
from src.services.document_parser import ParsedParagraph

_HEADING_STYLES = frozenset(
    {
        ParagraphStyle.TITLE,
        ParagraphStyle.HEADING_1,
        ParagraphStyle.HEADING_2,
        ParagraphStyle.HEADING_3,
        ParagraphStyle.HEADING_4,
    }
)

SEPARATOR = "\n\n"


@dataclass(frozen=True)
class Chunk:
    text: str
    members: tuple[ParsedParagraph, ...]


def merge_paragraphs(
    paragraphs: list[ParsedParagraph], max_words: int = 384
) -> list[Chunk]:
    """Merge adjacent NORMAL paragraphs into larger chunks for better translation context.

    Headings always start a new chunk. Chunks are split when accumulated word count
    exceeds *max_words*. A single paragraph exceeding the limit is kept intact.
    """
    if not paragraphs:
        return []

    chunks: list[Chunk] = []
    current_members: list[ParsedParagraph] = []
    current_words = 0

    def _flush() -> None:
        nonlocal current_words
        if current_members:
            text = SEPARATOR.join(m.text for m in current_members)
            chunks.append(Chunk(text=text, members=tuple(current_members)))
            current_members.clear()
            current_words = 0

    for para in paragraphs:
        is_heading = para.style in _HEADING_STYLES
        word_count = len(para.text.split())

        if is_heading:
            _flush()
            current_members.append(para)
            current_words = word_count
            continue

        if current_members and current_words + word_count > max_words:
            _flush()

        current_members.append(para)
        current_words += word_count

    _flush()
    return chunks


def unmerge_translation(translated_text: str, member_count: int) -> list[str]:
    """Split a translated chunk back into individual paragraph translations.

    - Exact match: return parts as-is
    - More parts than members: join extras into the last element
    - Fewer parts than members: pad with empty strings
    """
    if member_count == 1:
        return [translated_text.strip()]

    parts = [p.strip() for p in translated_text.split(SEPARATOR)]

    if len(parts) == member_count:
        return parts

    if len(parts) > member_count:
        merged_tail = SEPARATOR.join(parts[member_count - 1 :])
        return [*parts[: member_count - 1], merged_tail]

    # Fewer parts than expected — pad with empty strings
    return parts + [""] * (member_count - len(parts))
