from io import BytesIO
from unittest.mock import AsyncMock, patch

from docx import Document
from fastapi.testclient import TestClient

from src.main import app


def _make_docx(paragraphs: list[str]) -> bytes:
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_upload_returns_translation():
    client = TestClient(app)
    docx = _make_docx(["Hello."])
    with patch(
        "src.services.translation_strategy.BatchTranslationStrategy._translate_batch",
        new_callable=AsyncMock,
        return_value=["你好。"],
    ):
        response = client.post(
            "/api/v1/translations/upload",
            files={
                "file": (
                    "test.docx",
                    docx,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.docx"
    assert len(data["paragraphs"]) == 1
    assert data["paragraphs"][0]["original"] == "Hello."


def test_upload_rejects_non_docx():
    client = TestClient(app)
    response = client.post(
        "/api/v1/translations/upload",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 422


def test_list_translations():
    client = TestClient(app)
    response = client.get("/api/v1/translations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
