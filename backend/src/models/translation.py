from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ParagraphStyle(str, Enum):
    TITLE = "title"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    HEADING_4 = "heading_4"
    NORMAL = "normal"


class TranslatedParagraph(BaseModel):
    original: str
    translated: str
    style: ParagraphStyle = ParagraphStyle.NORMAL


class TranslationResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    paragraphs: list[TranslatedParagraph]


class TranslationSummary(BaseModel):
    id: UUID
    filename: str
    created_at: datetime
    paragraph_count: int
