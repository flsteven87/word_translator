from pathlib import PurePosixPath
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
    "application/pdf",
}

ALLOWED_EXTENSIONS = {".docx", ".pdf"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload")
async def upload_and_translate(
    file: UploadFile,
    service: TranslationServiceDep,
) -> TranslationResult:
    ext = PurePosixPath(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_CONTENT_TYPES and ext not in ALLOWED_EXTENSIONS:
        raise InputValidationError("Only .docx and .pdf files are supported")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise InputValidationError("File size exceeds the 10 MB limit")
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


@router.delete("/{translation_id}", status_code=204)
def delete_translation(
    translation_id: str,
    service: TranslationServiceDep,
) -> None:
    service.delete_translation(translation_id)


@router.get("/{translation_id}/download")
def download_translation(
    translation_id: str,
    service: TranslationServiceDep,
) -> Response:
    result = service.get_translation(translation_id)
    docx_bytes = service.export_translation(result)
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="translated_{result.filename}"'
        },
    )
