from pathlib import Path

from openai import AsyncOpenAI

from src.models.translation import (
    TranslatedParagraph,
    TranslationResult,
    TranslationSummary,
)
from src.services.chunker import merge_paragraphs, unmerge_translation
from src.services.document_parser import DocumentParser, ParsedParagraph
from src.services.translation_store import TranslationStore
from src.services.translation_strategy import BatchTranslationStrategy
from src.services.word_exporter import WordExporter


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
        client = AsyncOpenAI(api_key=openai_api_key)
        self._strategy = BatchTranslationStrategy(client=client, model=openai_model)

    async def translate_document(
        self, file_content: bytes, filename: str
    ) -> TranslationResult:
        parsed = self._parser.parse(file_content, filename)
        paragraphs = await self._translate_parsed(parsed)
        result = TranslationResult(filename=filename, paragraphs=paragraphs)
        self._store.save(result)
        self._store.save_upload(str(result.id), filename, file_content)
        return result

    async def retranslate(self, translation_id: str) -> TranslationResult:
        existing = self._store.load(translation_id)
        parsed = [
            ParsedParagraph(text=p.original, style=p.style)
            for p in existing.paragraphs
        ]
        paragraphs = await self._translate_parsed(parsed)
        result = TranslationResult(
            id=existing.id,
            filename=existing.filename,
            created_at=existing.created_at,
            paragraphs=paragraphs,
        )
        self._store.save(result)
        return result

    async def _translate_parsed(
        self, parsed: list[ParsedParagraph]
    ) -> list[TranslatedParagraph]:
        chunks = merge_paragraphs(parsed)
        translated_chunks = await self._strategy.translate(
            [c.text for c in chunks]
        )
        paragraphs: list[TranslatedParagraph] = []
        for chunk, translated_text in zip(chunks, translated_chunks):
            parts = unmerge_translation(translated_text, len(chunk.members))
            for member, part in zip(chunk.members, parts):
                paragraphs.append(
                    TranslatedParagraph(
                        original=member.text, translated=part, style=member.style
                    )
                )
        return paragraphs

    def get_translation(self, translation_id: str) -> TranslationResult:
        return self._store.load(translation_id)

    def list_translations(self) -> list[TranslationSummary]:
        return self._store.list_all()

    def delete_translation(self, translation_id: str) -> None:
        self._store.delete(translation_id)

    def export_translation(self, result: TranslationResult) -> tuple[bytes, str]:
        original_docx: bytes | None = None
        upload = self._store.load_upload(str(result.id))
        if upload is not None:
            path, ext = upload
            if ext == "docx":
                original_docx = path.read_bytes()
        docx_bytes = self._exporter.export(result, original_docx=original_docx)
        stem = Path(result.filename).stem
        filename = f"{stem}_中文.docx"
        return docx_bytes, filename
