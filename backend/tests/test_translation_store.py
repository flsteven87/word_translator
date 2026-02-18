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


def test_load_upload_returns_path_and_ext(store, sample_result):
    store.save(sample_result)
    store.save_upload(str(sample_result.id), "test.docx", b"fake-docx-content")
    result = store.load_upload(str(sample_result.id))
    assert result is not None
    path, ext = result
    assert ext == "docx"
    assert path.read_bytes() == b"fake-docx-content"


def test_load_upload_returns_none_when_missing(store):
    assert store.load_upload("nonexistent-id") is None
