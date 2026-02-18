import asyncio
import re
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

SYSTEM_PROMPT = (
    "You are a professional English to Traditional Chinese (繁體中文) translator. "
    "Translate each numbered item into Traditional Chinese accurately and naturally. "
    "You MUST use Traditional Chinese characters only — never use Simplified Chinese. "
    "If an item contains multiple paragraphs separated by blank lines, "
    "preserve the same paragraph structure in your translation. "
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
        result = self._parse_numbered_response(content, len(batch))

        missing_indices = [i for i, t in enumerate(result) if not t]
        if missing_indices:
            retried = await asyncio.gather(
                *[self._translate_single(batch[i]) for i in missing_indices]
            )
            for idx, text in zip(missing_indices, retried):
                result[idx] = text

        return result

    async def _translate_single(self, text: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"[1] {text}"},
            ],
        )
        content = (response.choices[0].message.content or "").strip()
        return re.sub(r"^\[1\]\s*", "", content)

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
