import asyncio
from pathlib import Path

from openai import AsyncOpenAI

from src.models.translation import (
    ParagraphStyle,
    TranslatedParagraph,
    TranslationDirection,
    TranslationResult,
    TranslationSummary,
)
from src.services.chunker import group_paragraphs
from src.services.document_parser import DocumentParser, ParsedParagraph
from src.services.translation_store import TranslationStore
from src.services.translation_strategy import (
    BatchTranslationStrategy,
    TranslationStrategy,
    detect_language,
)
from src.services.word_exporter import WordExporter

_NON_TRANSLATABLE_STYLES = frozenset({ParagraphStyle.FIGURE, ParagraphStyle.TABLE})


class TranslationService:
    def __init__(
        self,
        storage_dir: Path,
        openai_api_key: str,
        openai_model: str,
        vision_agent_api_key: str | None = None,
    ) -> None:
        self._parser = DocumentParser(vision_agent_api_key)
        self._store = TranslationStore(storage_dir=storage_dir)
        self._exporter = WordExporter()
        self._client = AsyncOpenAI(api_key=openai_api_key)
        self._model = openai_model

    def _make_strategy(
        self, direction: TranslationDirection,
    ) -> BatchTranslationStrategy:
        return BatchTranslationStrategy(
            client=self._client, model=self._model, direction=direction,
        )

    async def translate_document(
        self, file_content: bytes, filename: str
    ) -> TranslationResult:
        parsed = await asyncio.to_thread(self._parser.parse, file_content, filename)
        texts = [
            p.text for p in parsed if p.style not in _NON_TRANSLATABLE_STYLES
        ]
        direction = await detect_language(self._client, self._model, texts)
        strategy = self._make_strategy(direction)
        paragraphs = await self._translate_parsed(parsed, strategy)
        result = TranslationResult(
            filename=filename, paragraphs=paragraphs, direction=direction,
        )
        await asyncio.gather(
            asyncio.to_thread(self._store.save, result),
            asyncio.to_thread(
                self._store.save_upload, str(result.id), filename, file_content,
            ),
        )
        return result

    async def retranslate(self, translation_id: str) -> TranslationResult:
        existing = await asyncio.to_thread(self._store.load, translation_id)
        parsed = [
            ParsedParagraph(text=p.original, style=p.style, image_base64=p.image)
            for p in existing.paragraphs
        ]
        texts = [
            p.text for p in parsed if p.style not in _NON_TRANSLATABLE_STYLES
        ]
        direction = await detect_language(self._client, self._model, texts)
        strategy = self._make_strategy(direction)
        paragraphs = await self._translate_parsed(parsed, strategy)
        result = TranslationResult(
            id=existing.id,
            filename=existing.filename,
            created_at=existing.created_at,
            paragraphs=paragraphs,
            direction=direction,
        )
        await asyncio.to_thread(self._store.save, result)
        return result

    async def _translate_parsed(
        self, parsed: list[ParsedParagraph], strategy: TranslationStrategy,
    ) -> list[TranslatedParagraph]:
        groups = group_paragraphs(parsed)

        async def _translate_group(
            group: list[ParsedParagraph],
        ) -> list[TranslatedParagraph]:
            if group[0].style in _NON_TRANSLATABLE_STYLES:
                return [
                    TranslatedParagraph(
                        original=member.text, translated="", style=member.style,
                        image=member.image_base64,
                    )
                    for member in group
                ]
            texts = [p.text for p in group]
            translated = await strategy.translate(texts)
            return [
                TranslatedParagraph(
                    original=member.text, translated=trans, style=member.style,
                )
                for member, trans in zip(group, translated)
            ]

        results = await asyncio.gather(
            *[_translate_group(g) for g in groups]
        )
        return [p for group_result in results for p in group_result]

    def get_translation(self, translation_id: str) -> TranslationResult:
        return self._store.load(translation_id)

    def list_translations(self) -> list[TranslationSummary]:
        return self._store.list_all()

    def delete_translation(self, translation_id: str) -> None:
        self._store.delete(translation_id)

    def export_translation(self, result: TranslationResult) -> tuple[bytes, str]:
        docx_bytes = self._exporter.export(result)
        stem = Path(result.filename).stem
        filename = f"{stem}_對照.docx"
        return docx_bytes, filename
