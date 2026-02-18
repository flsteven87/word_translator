from src.models.translation import TranslatedParagraph, TranslationResult, TranslationSummary


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
