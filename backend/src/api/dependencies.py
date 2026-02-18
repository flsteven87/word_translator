from functools import lru_cache
from pathlib import Path

from src.core.config import get_settings
from src.services.translation_service import TranslationService


@lru_cache
def get_translation_service() -> TranslationService:
    settings = get_settings()
    return TranslationService(
        storage_dir=Path(settings.storage_dir),
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
        vision_agent_api_key=settings.vision_agent_api_key,
    )
