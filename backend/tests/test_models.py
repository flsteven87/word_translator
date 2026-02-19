import json

from src.models.translation import (
    ParagraphStyle,
    TranslatedParagraph,
    TranslationDirection,
    TranslationResult,
    TranslationSummary,
)


def test_translation_result_defaults():
    result = TranslationResult(
        filename="test.docx",
        paragraphs=[
            TranslatedParagraph(original="Hello", translated="你好"),
        ],
    )
    assert result.id is not None
    assert result.filename == "test.docx"
    assert result.created_at is not None
    assert len(result.paragraphs) == 1
    assert result.paragraphs[0].original == "Hello"


def test_translation_result_json_roundtrip():
    result = TranslationResult(
        filename="test.docx",
        paragraphs=[
            TranslatedParagraph(original="Hello", translated="你好"),
        ],
    )
    json_str = result.model_dump_json()
    restored = TranslationResult.model_validate_json(json_str)
    assert restored.id == result.id
    assert restored.paragraphs[0].translated == "你好"


def test_translation_summary():
    summary = TranslationSummary(
        id="550e8400-e29b-41d4-a716-446655440000",
        filename="doc.docx",
        created_at="2026-01-01T00:00:00Z",
        paragraph_count=5,
    )
    assert summary.paragraph_count == 5


def test_figure_and_table_styles_roundtrip():
    result = TranslationResult(
        filename="test.pdf",
        paragraphs=[
            TranslatedParagraph(
                original="<::bar chart::>Y-axis label: results",
                translated="",
                style=ParagraphStyle.FIGURE,
            ),
            TranslatedParagraph(
                original='<table id="1-1"><tr><td>Data</td></tr></table>',
                translated="",
                style=ParagraphStyle.TABLE,
            ),
        ],
    )
    json_str = result.model_dump_json()
    restored = TranslationResult.model_validate_json(json_str)
    assert restored.paragraphs[0].style == ParagraphStyle.FIGURE
    assert restored.paragraphs[1].style == ParagraphStyle.TABLE
    assert restored.paragraphs[0].translated == ""
    assert restored.paragraphs[1].translated == ""


def test_translation_result_default_direction():
    result = TranslationResult(
        filename="test.docx",
        paragraphs=[
            TranslatedParagraph(original="Hello", translated="你好"),
        ],
    )
    assert result.direction == TranslationDirection.EN_TO_ZH


def test_translation_result_zh_to_en_direction():
    result = TranslationResult(
        filename="test.docx",
        direction=TranslationDirection.ZH_TO_EN,
        paragraphs=[
            TranslatedParagraph(original="你好", translated="Hello"),
        ],
    )
    assert result.direction == TranslationDirection.ZH_TO_EN


def test_translation_result_direction_json_roundtrip():
    result = TranslationResult(
        filename="test.docx",
        direction=TranslationDirection.ZH_TO_EN,
        paragraphs=[
            TranslatedParagraph(original="你好", translated="Hello"),
        ],
    )
    json_str = result.model_dump_json()
    restored = TranslationResult.model_validate_json(json_str)
    assert restored.direction == TranslationDirection.ZH_TO_EN


def test_translation_result_missing_direction_defaults():
    """Old JSON without a direction field should default to EN_TO_ZH."""
    data = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "filename": "legacy.docx",
        "created_at": "2026-01-01T00:00:00Z",
        "paragraphs": [
            {"original": "Hello", "translated": "你好"},
        ],
    }
    result = TranslationResult.model_validate_json(json.dumps(data))
    assert result.direction == TranslationDirection.EN_TO_ZH
