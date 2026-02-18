from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.translation_strategy import BatchTranslationStrategy


@pytest.fixture
def mock_openai_client():
    client = AsyncMock()
    return client


def _make_completion_response(content: str):
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.mark.asyncio
async def test_batch_translate_single_batch(mock_openai_client):
    mock_openai_client.chat.completions.create.return_value = (
        _make_completion_response("<<<1>>> 你好\n<<<2>>> 世界")
    )
    strategy = BatchTranslationStrategy(
        client=mock_openai_client, model="gpt-4o-mini", batch_size=10
    )
    result = await strategy.translate(["Hello", "World"])
    assert result == ["你好", "世界"]
    mock_openai_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_batch_translate_multiple_batches(mock_openai_client):
    mock_openai_client.chat.completions.create.side_effect = [
        _make_completion_response("<<<1>>> 第一\n<<<2>>> 第二"),
        _make_completion_response("<<<1>>> 第三"),
    ]
    strategy = BatchTranslationStrategy(
        client=mock_openai_client, model="gpt-4o-mini", batch_size=2
    )
    result = await strategy.translate(["First", "Second", "Third"])
    assert result == ["第一", "第二", "第三"]
    assert mock_openai_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_batch_translate_with_academic_citations(mock_openai_client):
    """Regression: [N] citations in translated text must not break parsing."""
    mock_openai_client.chat.completions.create.return_value = (
        _make_completion_response(
            "<<<1>>> 可穿戴電子紡織品 [1]、應變傳感器 [2–4]、"
            "自供電 [5]、導電 [6]。\n"
            "<<<2>>> 材料的HV和THV [10–14]。"
        )
    )
    strategy = BatchTranslationStrategy(
        client=mock_openai_client, model="gpt-4o-mini", batch_size=10
    )
    result = await strategy.translate(["Paragraph about e-textiles [1]...", "HV and THV [10-14]."])
    assert result[0] == "可穿戴電子紡織品 [1]、應變傳感器 [2–4]、自供電 [5]、導電 [6]。"
    assert result[1] == "材料的HV和THV [10–14]。"


@pytest.mark.asyncio
async def test_batch_translate_empty_input(mock_openai_client):
    strategy = BatchTranslationStrategy(
        client=mock_openai_client, model="gpt-4o-mini", batch_size=10
    )
    result = await strategy.translate([])
    assert result == []
    mock_openai_client.chat.completions.create.assert_not_called()
