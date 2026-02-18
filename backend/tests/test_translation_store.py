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
