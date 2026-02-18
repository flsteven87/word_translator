import asyncio
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from docx import Document

from src.core.exceptions import NotFoundError
from src.models.translation import TranslationResult
from src.services.translation_service import TranslationService


@pytest.fixture
def service(tmp_path):
    return TranslationService(
        storage_dir=tmp_path,
        openai_api_key="test-key",
        openai_model="gpt-4o-mini",
        vision_agent_api_key="test-key",
    )


def _make_docx(paragraphs: list[str]) -> bytes:
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_translate_document(service):
    docx_content = _make_docx(["Hello world.", "Good morning."])

    with patch.object(
        service._strategy, "translate", new_callable=AsyncMock
    ) as mock_translate:
        mock_translate.return_value = ["你好世界。", "早安。"]
        result = await service.translate_document(docx_content, "test.docx")

    assert isinstance(result, TranslationResult)
    assert result.filename == "test.docx"
    assert len(result.paragraphs) == 2
    assert result.paragraphs[0].original == "Hello world."
    assert result.paragraphs[0].translated == "你好世界。"


@pytest.mark.asyncio
async def test_translate_document_is_persisted(service):
    docx_content = _make_docx(["Hello."])

    with patch.object(
        service._strategy, "translate", new_callable=AsyncMock
    ) as mock_translate:
        mock_translate.return_value = ["你好。"]
        result = await service.translate_document(docx_content, "test.docx")

    loaded = service.get_translation(str(result.id))
    assert loaded.id == result.id


def test_list_translations_empty(service):
    assert service.list_translations() == []


def test_get_translation_not_found(service):
    with pytest.raises(NotFoundError):
        service.get_translation("nonexistent")


def test_export_translation(service):
    docx_content = _make_docx(["Hello."])

    with patch.object(service._strategy, "translate", new_callable=AsyncMock) as m:
        m.return_value = ["你好。"]
        result = asyncio.get_event_loop().run_until_complete(
            service.translate_document(docx_content, "test.docx")
        )

    loaded = service.get_translation(str(result.id))
    docx_bytes, filename = service.export_translation(loaded)
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 0
    assert filename == "test_中文.docx"
