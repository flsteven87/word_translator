from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.translation import TranslationDirection
from src.services.translation_strategy import (
    _MAX_SAMPLE_PARAGRAPHS,
    detect_language,
)


def _make_parse_response(language: str):
    parsed = MagicMock()
    parsed.language = language
    message = MagicMock()
    message.parsed = parsed
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.fixture
def mock_openai_client():
    client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_detect_english(mock_openai_client):
    mock_openai_client.beta.chat.completions.parse.return_value = (
        _make_parse_response("en")
    )
    result = await detect_language(mock_openai_client, "gpt-4o-mini", ["Hello world"])
    assert result == TranslationDirection.EN_TO_ZH


@pytest.mark.asyncio
async def test_detect_chinese(mock_openai_client):
    mock_openai_client.beta.chat.completions.parse.return_value = (
        _make_parse_response("zh")
    )
    result = await detect_language(mock_openai_client, "gpt-4o-mini", ["你好世界"])
    assert result == TranslationDirection.ZH_TO_EN


@pytest.mark.asyncio
async def test_detect_samples_first_paragraphs(mock_openai_client):
    mock_openai_client.beta.chat.completions.parse.return_value = (
        _make_parse_response("en")
    )
    paragraphs = [f"Paragraph {i}" for i in range(_MAX_SAMPLE_PARAGRAPHS + 5)]
    await detect_language(mock_openai_client, "gpt-4o-mini", paragraphs)

    call_args = mock_openai_client.beta.chat.completions.parse.call_args
    user_content = call_args.kwargs["messages"][1]["content"]
    expected_sample = "\n".join(paragraphs[:_MAX_SAMPLE_PARAGRAPHS])
    assert user_content == expected_sample


@pytest.mark.asyncio
async def test_detect_fallback_on_error(mock_openai_client):
    mock_openai_client.beta.chat.completions.parse.side_effect = RuntimeError("API down")
    result = await detect_language(mock_openai_client, "gpt-4o-mini", ["Some text"])
    assert result == TranslationDirection.EN_TO_ZH


@pytest.mark.asyncio
async def test_detect_empty_paragraphs(mock_openai_client):
    result = await detect_language(mock_openai_client, "gpt-4o-mini", [])
    assert result == TranslationDirection.EN_TO_ZH
    mock_openai_client.beta.chat.completions.parse.assert_not_called()
