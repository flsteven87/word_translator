from src.models.translation import ParagraphStyle
from src.services.chunker import group_paragraphs
from src.services.document_parser import ParsedParagraph


def _normal(text: str) -> ParsedParagraph:
    return ParsedParagraph(text=text, style=ParagraphStyle.NORMAL)


def _heading(text: str, style: ParagraphStyle = ParagraphStyle.HEADING_1) -> ParsedParagraph:
    return ParsedParagraph(text=text, style=style)


class TestGroupParagraphs:
    def test_empty_input(self):
        assert group_paragraphs([]) == []

    def test_single_paragraph(self):
        p = _normal("Hello world.")
        groups = group_paragraphs([p])
        assert groups == [[p]]

    def test_short_paragraphs_grouped_together(self):
        paragraphs = [_normal("One."), _normal("Two."), _normal("Three.")]
        groups = group_paragraphs(paragraphs, max_words=100)
        assert len(groups) == 1
        assert groups[0] == paragraphs

    def test_heading_forces_new_group(self):
        paragraphs = [
            _normal("Body text."),
            _heading("Section Title"),
            _normal("More body."),
        ]
        groups = group_paragraphs(paragraphs, max_words=100)
        assert len(groups) == 3
        assert groups[0] == [paragraphs[0]]
        assert groups[1] == [paragraphs[1]]
        assert groups[2] == [paragraphs[2]]

    def test_word_budget_triggers_split(self):
        paragraphs = [
            _normal("word " * 10),
            _normal("word " * 10),
            _normal("word " * 10),
        ]
        groups = group_paragraphs(paragraphs, max_words=25)
        assert len(groups) == 2
        assert len(groups[0]) == 2
        assert len(groups[1]) == 1

    def test_oversized_single_paragraph_preserved(self):
        big = _normal("word " * 500)
        groups = group_paragraphs([big], max_words=100)
        assert len(groups) == 1
        assert groups[0] == [big]

    def test_consecutive_headings_each_standalone(self):
        paragraphs = [
            _heading("H1", ParagraphStyle.HEADING_1),
            _heading("H2", ParagraphStyle.HEADING_2),
            _heading("H3", ParagraphStyle.HEADING_3),
        ]
        groups = group_paragraphs(paragraphs, max_words=100)
        assert len(groups) == 3
        for group in groups:
            assert len(group) == 1

    def test_heading_then_body_paragraphs(self):
        paragraphs = [
            _heading("Title", ParagraphStyle.TITLE),
            _normal("First paragraph."),
            _normal("Second paragraph."),
        ]
        groups = group_paragraphs(paragraphs, max_words=100)
        assert len(groups) == 2
        assert groups[0] == [paragraphs[0]]
        assert groups[1] == [paragraphs[1], paragraphs[2]]

    def test_all_heading_styles_force_split(self):
        for style in [
            ParagraphStyle.TITLE,
            ParagraphStyle.HEADING_1,
            ParagraphStyle.HEADING_2,
            ParagraphStyle.HEADING_3,
            ParagraphStyle.HEADING_4,
        ]:
            paragraphs = [_normal("Before."), _heading("H", style), _normal("After.")]
            groups = group_paragraphs(paragraphs, max_words=100)
            assert len(groups) == 3, f"Failed for {style}"

    def test_no_text_merging(self):
        paragraphs = [_normal("One."), _normal("Two.")]
        groups = group_paragraphs(paragraphs, max_words=100)
        assert groups[0][0].text == "One."
        assert groups[0][1].text == "Two."
