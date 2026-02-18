from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response

from src.api.dependencies import get_translation_service
from src.core.exceptions import InputValidationError
from src.models.translation import TranslationResult, TranslationSummary
from src.services.translation_service import TranslationService

router = APIRouter(prefix="/translations", tags=["translations"])

TranslationServiceDep = Annotated[
    TranslationService, Depends(get_translation_service)
]

ALLOWED_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/upload")
async def upload_and_translate(
    file: UploadFile,
    service: TranslationServiceDep,
) -> TranslationResult:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise InputValidationError("Only .docx files are supported")
    content = await file.read()
    return await service.translate_document(content, file.filename or "unknown.docx")


@router.get("")
def list_translations(service: TranslationServiceDep) -> list[TranslationSummary]:
    return service.list_translations()


@router.get("/{translation_id}")
def get_translation(
    translation_id: str,
    service: TranslationServiceDep,
) -> TranslationResult:
    return service.get_translation(translation_id)


@router.get("/{translation_id}/download")
def download_translation(
    translation_id: str,
    service: TranslationServiceDep,
) -> Response:
    result = service.get_translation(translation_id)
    docx_bytes = service.export_translation(translation_id)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="translated_{result.filename}"'
        },
    )
