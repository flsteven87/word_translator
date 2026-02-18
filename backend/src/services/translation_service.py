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
        self,
        storage_dir: Path,
        openai_api_key: str,
        openai_model: str,
        vision_agent_api_key: str,
    ) -> None:
        self._parser = DocumentParser(vision_agent_api_key)
        self._store = TranslationStore(storage_dir=storage_dir)
        self._exporter = WordExporter()
        client = AsyncOpenAI(api_key=openai_api_key)
        self._strategy = BatchTranslationStrategy(client=client, model=openai_model)

    async def translate_document(
        self, file_content: bytes, filename: str
    ) -> TranslationResult:
        parsed = self._parser.parse(file_content, filename)
        texts = [p.text for p in parsed]
        translated = await self._strategy.translate(texts)
        result = TranslationResult(
            filename=filename,
            paragraphs=[
                TranslatedParagraph(
                    original=p.text, translated=trans, style=p.style
                )
                for p, trans in zip(parsed, translated)
            ],
        )
        self._store.save(result)
        self._store.save_upload(str(result.id), filename, file_content)
        return result

    def get_translation(self, translation_id: str) -> TranslationResult:
        return self._store.load(translation_id)

    def list_translations(self) -> list[TranslationSummary]:
        return self._store.list_all()

    def delete_translation(self, translation_id: str) -> None:
        self._store.delete(translation_id)

    def export_translation(self, result: TranslationResult) -> bytes:
        return self._exporter.export(result)
