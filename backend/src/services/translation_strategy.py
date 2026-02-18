import asyncio
import re
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from src.core.exceptions import AppException

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
        batches = [
            paragraphs[i : i + self._batch_size]
            for i in range(0, len(paragraphs), self._batch_size)
        ]
        translated_batches = await asyncio.gather(
            *[self._translate_batch(batch) for batch in batches]
        )
        return [item for batch in translated_batches for item in batch]

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
        result = [translations.get(n, "") for n in range(1, expected_count + 1)]
        missing = [n for n in range(1, expected_count + 1) if n not in translations]
        if missing:
            raise AppException(
                f"Translation response missing paragraph(s): {missing}"
            )
        return result
