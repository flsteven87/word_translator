# Word Translator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the full Word translation pipeline — upload English .docx, translate to Chinese via OpenAI, display side-by-side, download bilingual Word file.

**Architecture:** 4-layer backend (API → Service → modules). Backend modules: DocumentParser, TranslationStrategy (ABC + BatchTranslationStrategy), TranslationStore (JSON files), WordExporter. Frontend: TanStack Query hooks + three pages (Upload, History, Dashboard).

**Tech Stack:** Python 3.13 + FastAPI + python-docx + OpenAI async client | React 19 + TypeScript + TanStack Query + shadcn/ui + Tailwind CSS 4

---

## Task 1: Pydantic Models

**Files:**
- Create: `backend/src/models/__init__.py`
- Create: `backend/src/models/translation.py`
- Test: `backend/tests/test_models.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_models.py
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
        id="abc-123",
        filename="doc.docx",
        created_at="2026-01-01T00:00:00Z",
        paragraph_count=5,
    )
    assert summary.paragraph_count == 5
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.models'`

**Step 3: Implement models**

```python
# backend/src/models/__init__.py
(empty)
```

```python
# backend/src/models/translation.py
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TranslatedParagraph(BaseModel):
    original: str
    translated: str


class TranslationResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    paragraphs: list[TranslatedParagraph]


class TranslationSummary(BaseModel):
    id: str
    filename: str
    created_at: datetime
    paragraph_count: int
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_models.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add backend/src/models/ backend/tests/test_models.py
git commit -m "feat: add Pydantic models for translation"
```

---

## Task 2: DocumentParser

**Files:**
- Create: `backend/src/services/document_parser.py`
- Test: `backend/tests/test_document_parser.py`
- Test fixture: `backend/tests/fixtures/sample.docx` (generated in test)

**Step 1: Write the failing test**

```python
# backend/tests/test_document_parser.py
from io import BytesIO

from docx import Document

from src.services.document_parser import DocumentParser


def _make_docx(paragraphs: list[str]) -> bytes:
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_parse_extracts_paragraphs():
    content = _make_docx(["First paragraph.", "Second paragraph."])
    parser = DocumentParser()
    result = parser.parse(content)
    assert result == ["First paragraph.", "Second paragraph."]


def test_parse_skips_empty_paragraphs():
    content = _make_docx(["Hello.", "", "  ", "World."])
    parser = DocumentParser()
    result = parser.parse(content)
    assert result == ["Hello.", "World."]


def test_parse_extracts_headings():
    doc = Document()
    doc.add_heading("Title", level=1)
    doc.add_paragraph("Body text.")
    buf = BytesIO()
    doc.save(buf)
    parser = DocumentParser()
    result = parser.parse(buf.getvalue())
    assert result == ["Title", "Body text."]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_document_parser.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement**

```python
# backend/src/services/document_parser.py
from io import BytesIO

from docx import Document


class DocumentParser:
    def parse(self, file_content: bytes) -> list[str]:
        doc = Document(BytesIO(file_content))
        return [p.text for p in doc.paragraphs if p.text.strip()]
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_document_parser.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add backend/src/services/document_parser.py backend/tests/test_document_parser.py
git commit -m "feat: add DocumentParser for .docx extraction"
```

---

## Task 3: TranslationStrategy + BatchTranslationStrategy

**Files:**
- Create: `backend/src/services/translation_strategy.py`
- Test: `backend/tests/test_translation_strategy.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_translation_strategy.py
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
    mock_openai_client.chat.completions.create.return_value = _make_completion_response(
        "[1] 你好\n[2] 世界"
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
        _make_completion_response("[1] 第一\n[2] 第二"),
        _make_completion_response("[1] 第三"),
    ]
    strategy = BatchTranslationStrategy(
        client=mock_openai_client, model="gpt-4o-mini", batch_size=2
    )
    result = await strategy.translate(["First", "Second", "Third"])
    assert result == ["第一", "第二", "第三"]
    assert mock_openai_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_batch_translate_empty_input(mock_openai_client):
    strategy = BatchTranslationStrategy(
        client=mock_openai_client, model="gpt-4o-mini", batch_size=10
    )
    result = await strategy.translate([])
    assert result == []
    mock_openai_client.chat.completions.create.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_translation_strategy.py -v`
Expected: FAIL — `ModuleNotFoundError`

Note: Need to `uv add --dev pytest-asyncio` first.

**Step 3: Implement**

```python
# backend/src/services/translation_strategy.py
import re
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

SYSTEM_PROMPT = (
    "You are a professional English to Chinese translator. "
    "Translate each numbered paragraph accurately and naturally. "
    "Return ONLY the translations in the exact same numbered format [N]. "
    "Do not add, remove, or reorder any items."
)


class TranslationStrategy(ABC):
    @abstractmethod
    async def translate(self, paragraphs: list[str]) -> list[str]: ...


class BatchTranslationStrategy(TranslationStrategy):
    def __init__(
        self, client: AsyncOpenAI, model: str, batch_size: int = 10
    ) -> None:
        self._client = client
        self._model = model
        self._batch_size = batch_size

    async def translate(self, paragraphs: list[str]) -> list[str]:
        if not paragraphs:
            return []
        results: list[str] = []
        for i in range(0, len(paragraphs), self._batch_size):
            batch = paragraphs[i : i + self._batch_size]
            translated = await self._translate_batch(batch)
            results.extend(translated)
        return results

    async def _translate_batch(self, batch: list[str]) -> list[str]:
        numbered = "\n".join(f"[{i + 1}] {p}" for i, p in enumerate(batch))
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": numbered},
            ],
        )
        content = response.choices[0].message.content or ""
        return self._parse_numbered_response(content, len(batch))

    @staticmethod
    def _parse_numbered_response(content: str, expected_count: int) -> list[str]:
        pattern = r"\[(\d+)\]\s*"
        parts = re.split(pattern, content.strip())
        translations: dict[int, str] = {}
        i = 1
        while i < len(parts) - 1:
            num = int(parts[i])
            text = parts[i + 1].strip()
            translations[num] = text
            i += 2
        return [translations.get(n, "") for n in range(1, expected_count + 1)]
```

**Step 4: Add pytest-asyncio and run tests**

Run: `cd backend && uv add --dev pytest-asyncio && uv run pytest tests/test_translation_strategy.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add backend/src/services/translation_strategy.py backend/tests/test_translation_strategy.py backend/pyproject.toml backend/uv.lock
git commit -m "feat: add TranslationStrategy ABC with batch implementation"
```

---

## Task 4: TranslationStore

**Files:**
- Create: `backend/src/services/translation_store.py`
- Test: `backend/tests/test_translation_store.py`
- Modify: `backend/src/core/config.py` (add `storage_dir` setting)

**Step 1: Write the failing test**

```python
# backend/tests/test_translation_store.py
import pytest

from src.core.exceptions import NotFoundError
from src.models.translation import TranslatedParagraph, TranslationResult
from src.services.translation_store import TranslationStore


@pytest.fixture
def store(tmp_path):
    return TranslationStore(storage_dir=tmp_path)


@pytest.fixture
def sample_result():
    return TranslationResult(
        filename="test.docx",
        paragraphs=[
            TranslatedParagraph(original="Hello", translated="你好"),
            TranslatedParagraph(original="World", translated="世界"),
        ],
    )


def test_save_and_load(store, sample_result):
    store.save(sample_result)
    loaded = store.load(str(sample_result.id))
    assert loaded.id == sample_result.id
    assert loaded.filename == "test.docx"
    assert len(loaded.paragraphs) == 2


def test_load_not_found(store):
    with pytest.raises(NotFoundError):
        store.load("nonexistent-id")


def test_list_all(store, sample_result):
    store.save(sample_result)
    summaries = store.list_all()
    assert len(summaries) == 1
    assert summaries[0].filename == "test.docx"
    assert summaries[0].paragraph_count == 2


def test_list_all_empty(store):
    assert store.list_all() == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_translation_store.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement**

```python
# backend/src/services/translation_store.py
import json
from pathlib import Path

from src.core.exceptions import NotFoundError
from src.models.translation import TranslationResult, TranslationSummary


class TranslationStore:
    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, result: TranslationResult) -> None:
        path = self._storage_dir / f"{result.id}.json"
        path.write_text(
            json.dumps(
                result.model_dump(mode="json"), ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )

    def load(self, translation_id: str) -> TranslationResult:
        path = self._storage_dir / f"{translation_id}.json"
        if not path.exists():
            raise NotFoundError("Translation", translation_id)
        return TranslationResult.model_validate_json(path.read_text(encoding="utf-8"))

    def list_all(self) -> list[TranslationSummary]:
        results: list[TranslationSummary] = []
        paths = sorted(
            self._storage_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in paths:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append(
                TranslationSummary(
                    id=data["id"],
                    filename=data["filename"],
                    created_at=data["created_at"],
                    paragraph_count=len(data["paragraphs"]),
                )
            )
        return results
```

Add `storage_dir` to settings in `backend/src/core/config.py`:

```python
# Add to Settings class:
    storage_dir: str = "data/translations"
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_translation_store.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add backend/src/services/translation_store.py backend/tests/test_translation_store.py backend/src/core/config.py
git commit -m "feat: add TranslationStore for JSON file persistence"
```

---

## Task 5: WordExporter

**Files:**
- Create: `backend/src/services/word_exporter.py`
- Test: `backend/tests/test_word_exporter.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_word_exporter.py
from io import BytesIO

from docx import Document

from src.models.translation import TranslatedParagraph, TranslationResult
from src.services.word_exporter import WordExporter


def test_export_creates_valid_docx():
    result = TranslationResult(
        filename="test.docx",
        paragraphs=[
            TranslatedParagraph(original="Hello", translated="你好"),
            TranslatedParagraph(original="World", translated="世界"),
        ],
    )
    exporter = WordExporter()
    docx_bytes = exporter.export(result)

    doc = Document(BytesIO(docx_bytes))
    tables = doc.tables
    assert len(tables) == 1

    table = tables[0]
    # Header row + 2 data rows
    assert len(table.rows) == 3
    assert table.rows[0].cells[0].text == "English (Original)"
    assert table.rows[0].cells[1].text == "中文 (Translation)"
    assert table.rows[1].cells[0].text == "Hello"
    assert table.rows[1].cells[1].text == "你好"
    assert table.rows[2].cells[0].text == "World"
    assert table.rows[2].cells[1].text == "世界"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_word_exporter.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement**

```python
# backend/src/services/word_exporter.py
from io import BytesIO

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.table import WD_TABLE_ALIGNMENT

from src.models.translation import TranslationResult


class WordExporter:
    def export(self, result: TranslationResult) -> bytes:
        doc = Document()
        doc.add_heading(result.filename, level=1)

        table = doc.add_table(rows=1, cols=2)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        header = table.rows[0].cells
        header[0].text = "English (Original)"
        header[1].text = "中文 (Translation)"
        for cell in header:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True

        for para in result.paragraphs:
            row = table.add_row().cells
            row[0].text = para.original
            row[1].text = para.translated

        for row in table.rows:
            for cell in row.cells:
                cell.width = Inches(3.5)
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_after = Pt(4)

        buf = BytesIO()
        doc.save(buf)
        return buf.getvalue()
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_word_exporter.py -v`
Expected: 1 passed

**Step 5: Commit**

```bash
git add backend/src/services/word_exporter.py backend/tests/test_word_exporter.py
git commit -m "feat: add WordExporter for bilingual .docx generation"
```

---

## Task 6: TranslationService (Orchestrator)

**Files:**
- Create: `backend/src/services/translation_service.py`
- Test: `backend/tests/test_translation_service.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_translation_service.py
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.models.translation import TranslationResult
from src.services.translation_service import TranslationService


@pytest.fixture
def service(tmp_path):
    return TranslationService(storage_dir=tmp_path, openai_api_key="test-key", openai_model="gpt-4o-mini")


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
    from src.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        service.get_translation("nonexistent")


def test_export_translation(service):
    docx_content = _make_docx(["Hello."])
    import asyncio
    from unittest.mock import AsyncMock as AM

    with patch.object(service._strategy, "translate", new_callable=AM) as m:
        m.return_value = ["你好。"]
        result = asyncio.get_event_loop().run_until_complete(
            service.translate_document(docx_content, "test.docx")
        )

    exported = service.export_translation(str(result.id))
    assert isinstance(exported, bytes)
    assert len(exported) > 0


def _make_docx(paragraphs: list[str]) -> bytes:
    from io import BytesIO
    from docx import Document
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_translation_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement**

```python
# backend/src/services/translation_service.py
from pathlib import Path

from openai import AsyncOpenAI

from src.models.translation import TranslatedParagraph, TranslationResult, TranslationSummary
from src.services.document_parser import DocumentParser
from src.services.translation_store import TranslationStore
from src.services.translation_strategy import BatchTranslationStrategy
from src.services.word_exporter import WordExporter


class TranslationService:
    def __init__(self, storage_dir: Path, openai_api_key: str, openai_model: str) -> None:
        self._parser = DocumentParser()
        self._store = TranslationStore(storage_dir=storage_dir)
        self._exporter = WordExporter()
        client = AsyncOpenAI(api_key=openai_api_key)
        self._strategy = BatchTranslationStrategy(client=client, model=openai_model)

    async def translate_document(self, file_content: bytes, filename: str) -> TranslationResult:
        paragraphs = self._parser.parse(file_content)
        translated = await self._strategy.translate(paragraphs)
        result = TranslationResult(
            filename=filename,
            paragraphs=[
                TranslatedParagraph(original=orig, translated=trans)
                for orig, trans in zip(paragraphs, translated)
            ],
        )
        self._store.save(result)
        return result

    def get_translation(self, translation_id: str) -> TranslationResult:
        return self._store.load(translation_id)

    def list_translations(self) -> list[TranslationSummary]:
        return self._store.list_all()

    def export_translation(self, translation_id: str) -> bytes:
        result = self._store.load(translation_id)
        return self._exporter.export(result)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_translation_service.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add backend/src/services/translation_service.py backend/tests/test_translation_service.py
git commit -m "feat: add TranslationService orchestrator"
```

---

## Task 7: API Endpoints + Dependency Injection

**Files:**
- Create: `backend/src/api/v1/endpoints/translations.py`
- Create: `backend/src/api/dependencies.py`
- Modify: `backend/src/api/v1/router.py` (register translations router)
- Modify: `backend/src/core/config.py` (add storage_dir if not done)
- Create: `backend/data/.gitkeep`
- Modify: `backend/.gitignore` (ignore data/translations/*.json)
- Test: `backend/tests/test_api_translations.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_api_translations.py
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from docx import Document
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _make_docx(paragraphs: list[str]) -> bytes:
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_upload_returns_translation(client):
    docx = _make_docx(["Hello."])
    with patch(
        "src.services.translation_strategy.BatchTranslationStrategy._translate_batch",
        new_callable=AsyncMock,
        return_value=["你好。"],
    ):
        response = client.post(
            "/api/v1/translations/upload",
            files={"file": ("test.docx", docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.docx"
    assert len(data["paragraphs"]) == 1
    assert data["paragraphs"][0]["original"] == "Hello."


def test_upload_rejects_non_docx(client):
    response = client.post(
        "/api/v1/translations/upload",
        files={"file": ("test.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 422


def test_list_translations(client):
    response = client.get("/api/v1/translations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_api_translations.py -v`
Expected: FAIL

**Step 3: Implement dependency injection**

```python
# backend/src/api/dependencies.py
from functools import lru_cache
from pathlib import Path

from src.core.config import get_settings
from src.services.translation_service import TranslationService


@lru_cache
def get_translation_service() -> TranslationService:
    settings = get_settings()
    return TranslationService(
        storage_dir=Path(settings.storage_dir),
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
    )
```

**Step 4: Implement endpoint**

```python
# backend/src/api/v1/endpoints/translations.py
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response

from src.api.dependencies import get_translation_service
from src.core.exceptions import InputValidationError
from src.models.translation import TranslationResult, TranslationSummary
from src.services.translation_service import TranslationService

router = APIRouter(prefix="/translations", tags=["translations"])

TranslationServiceDep = Annotated[TranslationService, Depends(get_translation_service)]

ALLOWED_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/upload")
async def upload_and_translate(
    file: UploadFile,
    service: TranslationServiceDep,
) -> TranslationResult:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise InputValidationError("Only .docx files are supported")
    content = await file.read()
    return await service.translate_document(content, file.filename or "unknown.docx")


@router.get("")
def list_translations(service: TranslationServiceDep) -> list[TranslationSummary]:
    return service.list_translations()


@router.get("/{translation_id}")
def get_translation(
    translation_id: str,
    service: TranslationServiceDep,
) -> TranslationResult:
    return service.get_translation(translation_id)


@router.get("/{translation_id}/download")
def download_translation(
    translation_id: str,
    service: TranslationServiceDep,
) -> Response:
    result = service.get_translation(translation_id)
    docx_bytes = service.export_translation(translation_id)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="translated_{result.filename}"'},
    )
```

**Step 5: Wire up router**

Update `backend/src/api/v1/router.py`:

```python
from fastapi import APIRouter

from src.api.v1.endpoints import health, translations

router = APIRouter()
router.include_router(health.router)
router.include_router(translations.router)
```

**Step 6: Add .gitignore for data and create data dir**

Create `backend/data/.gitkeep` (empty file).

Add to `backend/.gitignore` (create if needed):

```
data/translations/
__pycache__/
*.pyc
.env
```

**Step 7: Run tests**

Run: `cd backend && uv run pytest tests/test_api_translations.py -v`
Expected: 3 passed

**Step 8: Run all tests**

Run: `cd backend && uv run pytest -v`
Expected: All passed

**Step 9: Lint**

Run: `cd backend && uv run ruff check .`
Expected: No errors

**Step 10: Commit**

```bash
git add backend/src/api/ backend/src/services/ backend/src/core/ backend/src/models/ backend/tests/ backend/data/.gitkeep
git commit -m "feat: add translation API endpoints with dependency injection"
```

---

## Task 8: Frontend API Client + Query Hooks

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/hooks/queries/translation-keys.ts`
- Create: `frontend/src/hooks/queries/use-translations.ts`
- Create: `frontend/src/hooks/queries/use-upload-translation.ts`

**Step 1: API client**

```typescript
// frontend/src/lib/api.ts
const BASE_URL = "/api/v1";

export interface TranslatedParagraph {
  original: string;
  translated: string;
}

export interface TranslationResult {
  id: string;
  filename: string;
  created_at: string;
  paragraphs: TranslatedParagraph[];
}

export interface TranslationSummary {
  id: string;
  filename: string;
  created_at: string;
  paragraph_count: number;
}

export async function uploadDocument(file: File): Promise<TranslationResult> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/translations/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(error.detail);
  }
  return res.json();
}

export async function fetchTranslations(): Promise<TranslationSummary[]> {
  const res = await fetch(`${BASE_URL}/translations`);
  if (!res.ok) throw new Error("Failed to fetch translations");
  return res.json();
}

export async function fetchTranslation(id: string): Promise<TranslationResult> {
  const res = await fetch(`${BASE_URL}/translations/${id}`);
  if (!res.ok) throw new Error("Translation not found");
  return res.json();
}

export function getDownloadUrl(id: string): string {
  return `${BASE_URL}/translations/${id}/download`;
}
```

**Step 2: Query key factory**

```typescript
// frontend/src/hooks/queries/translation-keys.ts
export const translationKeys = {
  all: ["translations"] as const,
  lists: () => [...translationKeys.all, "list"] as const,
  detail: (id: string) => [...translationKeys.all, "detail", id] as const,
};
```

**Step 3: Query hooks**

```typescript
// frontend/src/hooks/queries/use-translations.ts
import { useQuery } from "@tanstack/react-query";
import { fetchTranslations, fetchTranslation } from "@/lib/api";
import { translationKeys } from "./translation-keys";

export function useTranslations() {
  return useQuery({
    queryKey: translationKeys.lists(),
    queryFn: fetchTranslations,
  });
}

export function useTranslation(id: string) {
  return useQuery({
    queryKey: translationKeys.detail(id),
    queryFn: () => fetchTranslation(id),
    enabled: !!id,
  });
}
```

```typescript
// frontend/src/hooks/queries/use-upload-translation.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadDocument } from "@/lib/api";
import { translationKeys } from "./translation-keys";

export function useUploadTranslation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: uploadDocument,
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: translationKeys.lists() });
    },
  });
}
```

**Step 4: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/hooks/queries/
git commit -m "feat: add frontend API client and TanStack Query hooks"
```

---

## Task 9: Upload Page

**Files:**
- Modify: `frontend/src/pages/Upload.tsx`

**Step 1: Implement the full Upload page**

The page has three states:
1. **Idle** — drag-drop zone to select a .docx file
2. **Loading** — uploading + translating indicator
3. **Result** — side-by-side bilingual view + download button

```tsx
// frontend/src/pages/Upload.tsx
import { useCallback, useRef, useState } from "react";
import { Upload as UploadIcon, FileText, Download, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUploadTranslation } from "@/hooks/queries/use-upload-translation";
import { getDownloadUrl } from "@/lib/api";
import type { TranslationResult } from "@/lib/api";

export default function Upload() {
  const [dragOver, setDragOver] = useState(false);
  const [result, setResult] = useState<TranslationResult | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const mutation = useUploadTranslation();

  const handleFile = useCallback(
    (file: File) => {
      if (!file.name.endsWith(".docx")) return;
      setResult(null);
      mutation.mutate(file, {
        onSuccess: (data) => setResult(data),
      });
    },
    [mutation],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleReset = () => {
    setResult(null);
    mutation.reset();
  };

  if (result) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Translation Result
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {result.filename} — {result.paragraphs.length} paragraphs
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" asChild>
              <a href={getDownloadUrl(result.id)} download>
                <Download className="mr-2 h-4 w-4" />
                Download
              </a>
            </Button>
            <Button variant="outline" size="sm" onClick={handleReset}>
              <UploadIcon className="mr-2 h-4 w-4" />
              New Upload
            </Button>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-px rounded-lg border bg-border overflow-hidden">
          <div className="bg-muted/30 px-4 py-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            English (Original)
          </div>
          <div className="bg-muted/30 px-4 py-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
            中文 (Translation)
          </div>
          {result.paragraphs.map((p, i) => (
            <div key={i} className="contents">
              <div className="bg-background px-4 py-3 text-sm leading-relaxed border-t">
                {p.original}
              </div>
              <div className="bg-background px-4 py-3 text-sm leading-relaxed border-t">
                {p.translated}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Upload</h1>
        <p className="mt-2 text-muted-foreground">
          Upload a Word document (.docx) for English to Chinese translation.
        </p>
      </div>

      <div
        role="button"
        tabIndex={0}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        className={`flex flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed p-16 transition-colors cursor-pointer ${
          dragOver
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50"
        }`}
      >
        {mutation.isPending ? (
          <>
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            <div className="text-center">
              <p className="font-medium">Translating...</p>
              <p className="mt-1 text-sm text-muted-foreground">
                This may take a moment depending on document length.
              </p>
            </div>
          </>
        ) : (
          <>
            <div className="rounded-full bg-muted p-4">
              <UploadIcon className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="text-center">
              <p className="font-medium">
                Drop a .docx file here or click to browse
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Supports .docx files only
              </p>
            </div>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".docx"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </div>

      {mutation.isError && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          <X className="h-4 w-4 shrink-0" />
          {mutation.error.message}
        </div>
      )}
    </div>
  );
}
```

**Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/pages/Upload.tsx
git commit -m "feat: implement Upload page with drag-drop and side-by-side view"
```

---

## Task 10: History Page

**Files:**
- Modify: `frontend/src/pages/History.tsx`

**Step 1: Implement**

```tsx
// frontend/src/pages/History.tsx
import { Link } from "react-router-dom";
import { FileText, ExternalLink } from "lucide-react";
import { useTranslations } from "@/hooks/queries/use-translations";
import { Skeleton } from "@/components/ui/skeleton";

export default function History() {
  const { data: translations, isLoading } = useTranslations();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">History</h1>
        <p className="mt-2 text-muted-foreground">
          View past translation records.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : !translations?.length ? (
        <div className="rounded-lg border border-dashed p-12 text-center">
          <FileText className="mx-auto h-8 w-8 text-muted-foreground" />
          <p className="mt-3 text-sm text-muted-foreground">
            No translations yet. Upload a document to get started.
          </p>
        </div>
      ) : (
        <div className="divide-y rounded-lg border">
          {translations.map((t) => (
            <Link
              key={t.id}
              to={`/history/${t.id}`}
              className="flex items-center justify-between px-4 py-3 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                <div>
                  <p className="text-sm font-medium">{t.filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {t.paragraph_count} paragraphs ·{" "}
                    {new Date(t.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <ExternalLink className="h-4 w-4 text-muted-foreground" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Step 2: Add history detail route**

Update `frontend/src/App.tsx` to add detail route:

```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import Dashboard from "@/pages/Dashboard"
import Upload from "@/pages/Upload"
import History from "@/pages/History"
import TranslationDetail from "@/pages/TranslationDetail"

export default function App() {
  return (
    <BrowserRouter>
      <DashboardLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/history" element={<History />} />
          <Route path="/history/:id" element={<TranslationDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </DashboardLayout>
    </BrowserRouter>
  )
}
```

**Step 3: Create TranslationDetail page**

```tsx
// frontend/src/pages/TranslationDetail.tsx
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/hooks/queries/use-translations";
import { getDownloadUrl } from "@/lib/api";

export default function TranslationDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: result, isLoading } = useTranslation(id!);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!result) {
    return <p className="text-muted-foreground">Translation not found.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/history">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {result.filename}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {result.paragraphs.length} paragraphs ·{" "}
              {new Date(result.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
        <Button variant="outline" size="sm" asChild>
          <a href={getDownloadUrl(result.id)} download>
            <Download className="mr-2 h-4 w-4" />
            Download
          </a>
        </Button>
      </div>
      <div className="grid grid-cols-2 gap-px rounded-lg border bg-border overflow-hidden">
        <div className="bg-muted/30 px-4 py-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          English (Original)
        </div>
        <div className="bg-muted/30 px-4 py-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          中文 (Translation)
        </div>
        {result.paragraphs.map((p, i) => (
          <div key={i} className="contents">
            <div className="bg-background px-4 py-3 text-sm leading-relaxed border-t">
              {p.original}
            </div>
            <div className="bg-background px-4 py-3 text-sm leading-relaxed border-t">
              {p.translated}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 4: Verify build**

Run: `cd frontend && npx tsc --noEmit`

**Step 5: Commit**

```bash
git add frontend/src/pages/History.tsx frontend/src/pages/TranslationDetail.tsx frontend/src/App.tsx
git commit -m "feat: implement History page and TranslationDetail view"
```

---

## Task 11: Dashboard Page

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`

**Step 1: Implement**

```tsx
// frontend/src/pages/Dashboard.tsx
import { Link } from "react-router-dom";
import { Upload, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTranslations } from "@/hooks/queries/use-translations";

export default function Dashboard() {
  const { data: translations } = useTranslations();
  const recent = translations?.slice(0, 5) ?? [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-2 text-muted-foreground">
          Upload Word documents and get side-by-side English-Chinese
          translations.
        </p>
      </div>

      <Button asChild>
        <Link to="/upload">
          <Upload className="mr-2 h-4 w-4" />
          Upload Document
        </Link>
      </Button>

      <div className="space-y-3">
        <h2 className="text-sm font-medium text-muted-foreground">
          Recent Translations
        </h2>
        {!recent.length ? (
          <p className="text-sm text-muted-foreground">No translations yet.</p>
        ) : (
          <div className="divide-y rounded-lg border">
            {recent.map((t) => (
              <Link
                key={t.id}
                to={`/history/${t.id}`}
                className="flex items-center gap-3 px-4 py-3 hover:bg-muted/50 transition-colors"
              >
                <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                <div>
                  <p className="text-sm font-medium">{t.filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {t.paragraph_count} paragraphs ·{" "}
                    {new Date(t.created_at).toLocaleDateString()}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Verify build**

Run: `cd frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add frontend/src/pages/Dashboard.tsx
git commit -m "feat: implement Dashboard page with recent translations"
```

---

## Task 12: Final Integration + Lint

**Step 1: Run all backend tests**

Run: `cd backend && uv run pytest -v`
Expected: All passed

**Step 2: Backend lint**

Run: `cd backend && uv run ruff check .`
Expected: No errors

**Step 3: Frontend type check + lint**

Run: `cd frontend && npx tsc --noEmit && npm run lint`
Expected: No errors

**Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "chore: fix lint and type errors"
```
