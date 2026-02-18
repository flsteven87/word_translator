from src.models.translation import ParagraphStyle
from src.services.chunker import merge_paragraphs, unmerge_translation
from src.services.document_parser import ParsedParagraph


def _normal(text: str) -> ParsedParagraph:
    return ParsedParagraph(text=text, style=ParagraphStyle.NORMAL)


def _heading(text: str, style: ParagraphStyle = ParagraphStyle.HEADING_1) -> ParsedParagraph:
    return ParsedParagraph(text=text, style=style)


# --- merge_paragraphs ---


class TestMergeParagraphs:
    def test_empty_input(self):
        assert merge_paragraphs([]) == []

    def test_single_paragraph(self):
        p = _normal("Hello world.")
        chunks = merge_paragraphs([p])
        assert len(chunks) == 1
        assert chunks[0].text == "Hello world."
        assert chunks[0].members == (p,)

    def test_multiple_short_paragraphs_merged(self):
        paragraphs = [_normal("One."), _normal("Two."), _normal("Three.")]
        chunks = merge_paragraphs(paragraphs, max_words=100)
        assert len(chunks) == 1
        assert chunks[0].text == "One.\n\nTwo.\n\nThree."
        assert len(chunks[0].members) == 3

    def test_heading_forces_new_chunk(self):
        paragraphs = [
            _normal("Body text."),
            _heading("Section Title"),
            _normal("More body."),
        ]
        chunks = merge_paragraphs(paragraphs, max_words=100)
        assert len(chunks) == 2
        assert chunks[0].text == "Body text."
        assert chunks[1].text == "Section Title\n\nMore body."

    def test_word_budget_triggers_split(self):
        paragraphs = [
            _normal("word " * 10),  # 10 words
            _normal("word " * 10),  # 10 words
            _normal("word " * 10),  # 10 words
        ]
        # max_words=25: first two fit (20 words), third triggers new chunk
        chunks = merge_paragraphs(paragraphs, max_words=25)
        assert len(chunks) == 2
        assert len(chunks[0].members) == 2
        assert len(chunks[1].members) == 1

    def test_oversized_single_paragraph_preserved(self):
        big = _normal("word " * 500)
        chunks = merge_paragraphs([big], max_words=100)
        assert len(chunks) == 1
        assert chunks[0].members == (big,)

    def test_consecutive_headings_each_start_new_chunk(self):
        paragraphs = [
            _heading("H1", ParagraphStyle.HEADING_1),
            _heading("H2", ParagraphStyle.HEADING_2),
            _heading("H3", ParagraphStyle.HEADING_3),
        ]
        chunks = merge_paragraphs(paragraphs, max_words=100)
        assert len(chunks) == 3
        for i, chunk in enumerate(chunks):
            assert len(chunk.members) == 1

    def test_heading_collects_following_body(self):
        paragraphs = [
            _heading("Title", ParagraphStyle.TITLE),
            _normal("First paragraph."),
            _normal("Second paragraph."),
        ]
        chunks = merge_paragraphs(paragraphs, max_words=100)
        assert len(chunks) == 1
        assert len(chunks[0].members) == 3
        assert chunks[0].text == "Title\n\nFirst paragraph.\n\nSecond paragraph."


# --- unmerge_translation ---


class TestUnmergeTranslation:
    def test_single_member(self):
        result = unmerge_translation("翻譯結果", 1)
        assert result == ["翻譯結果"]

    def test_exact_split(self):
        result = unmerge_translation("第一段\n\n第二段\n\n第三段", 3)
        assert result == ["第一段", "第二段", "第三段"]

    def test_too_many_parts(self):
        result = unmerge_translation("A\n\nB\n\nC\n\nD", 2)
        assert result == ["A", "B\n\nC\n\nD"]

    def test_too_few_parts(self):
        result = unmerge_translation("只有一段", 3)
        assert result == ["只有一段", "", ""]

    def test_whitespace_stripping(self):
        result = unmerge_translation("  第一段  \n\n  第二段  ", 2)
        assert result == ["第一段", "第二段"]
