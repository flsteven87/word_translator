from fastapi import APIRouter

from src.api.v1.endpoints import translations

router = APIRouter()
router.include_router(translations.router)
