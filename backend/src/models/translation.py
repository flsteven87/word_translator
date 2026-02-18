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
