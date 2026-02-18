from fastapi import APIRouter

from src.api.v1.endpoints import health, translations

router = APIRouter()
router.include_router(health.router)
router.include_router(translations.router)
