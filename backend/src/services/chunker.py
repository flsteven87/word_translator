from src.models.translation import ParagraphStyle
from src.services.document_parser import ParsedParagraph

_STANDALONE_STYLES = frozenset(
    {
        ParagraphStyle.TITLE,
        ParagraphStyle.HEADING_1,
        ParagraphStyle.HEADING_2,
        ParagraphStyle.HEADING_3,
        ParagraphStyle.HEADING_4,
        ParagraphStyle.FIGURE,
        ParagraphStyle.TABLE,
    }
)


def group_paragraphs(
    paragraphs: list[ParsedParagraph], max_words: int = 384
) -> list[list[ParsedParagraph]]:
    """Group paragraphs for batched translation.

    Headings, figures, and tables are always standalone single-member groups.
    Consecutive NORMAL paragraphs accumulate until the word budget is exceeded.
    Each group becomes one ``strategy.translate()`` call where every paragraph
    gets its own ``<<<N>>>`` number.
    """
    if not paragraphs:
        return []

    groups: list[list[ParsedParagraph]] = []
    current: list[ParsedParagraph] = []
    current_words = 0

    def _flush() -> None:
        nonlocal current_words
        if current:
            groups.append(list(current))
            current.clear()
            current_words = 0

    for para in paragraphs:
        if para.style in _STANDALONE_STYLES:
            _flush()
            groups.append([para])
            continue

        word_count = len(para.text.split())
        if current and current_words + word_count > max_words:
            _flush()

        current.append(para)
        current_words += word_count

    _flush()
    return groups
