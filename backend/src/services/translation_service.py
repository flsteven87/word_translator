from pathlib import Path

from openai import AsyncOpenAI

from src.models.translation import (
    TranslatedParagraph,
    TranslationResult,
    TranslationSummary,
)
from src.services.document_parser import DocumentParser
from src.services.translation_store import TranslationStore
from src.services.translation_strategy import BatchTranslationStrategy
from src.services.word_exporter import WordExporter


class TranslationService:
    def __init__(
        self, storage_dir: Path, openai_api_key: str, openai_model: str
    ) -> None:
        self._parser = DocumentParser()
        self._store = TranslationStore(storage_dir=storage_dir)
        self._exporter = WordExporter()
        client = AsyncOpenAI(api_key=openai_api_key)
        self._strategy = BatchTranslationStrategy(client=client, model=openai_model)

    async def translate_document(
        self, file_content: bytes, filename: str
    ) -> TranslationResult:
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

    def export_translation(self, result: TranslationResult) -> bytes:
        return self._exporter.export(result)
