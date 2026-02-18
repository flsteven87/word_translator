import json
from pathlib import Path

from pydantic import ValidationError

from src.core.exceptions import AppException, NotFoundError
from src.models.translation import TranslationResult, TranslationSummary


class TranslationStore:
    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._uploads_dir = self._storage_dir / "uploads"
        self._uploads_dir.mkdir(parents=True, exist_ok=True)

    def save(self, result: TranslationResult) -> None:
        path = self._storage_dir / f"{result.id}.json"
        path.write_text(
            json.dumps(
                result.model_dump(mode="json"), ensure_ascii=False, indent=2
            ),
            encoding="utf-8",
        )

    def load(self, translation_id: str) -> TranslationResult:
        path = self._storage_dir / f"{translation_id}.json"
        if not path.exists():
            raise NotFoundError("Translation", translation_id)
        try:
            return TranslationResult.model_validate_json(path.read_text(encoding="utf-8"))
        except ValidationError as e:
            raise AppException(f"Invalid translation data for '{translation_id}'") from e

    def save_upload(self, translation_id: str, filename: str, content: bytes) -> None:
        ext = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else "bin"
        path = self._uploads_dir / f"{translation_id}.{ext}"
        path.write_bytes(content)

    def delete(self, translation_id: str) -> None:
        path = self._storage_dir / f"{translation_id}.json"
        if not path.exists():
            raise NotFoundError("Translation", translation_id)
        path.unlink()
        for upload in self._uploads_dir.glob(f"{translation_id}.*"):
            upload.unlink()

    def list_all(self) -> list[TranslationSummary]:
        results: list[TranslationSummary] = []
        paths = sorted(
            self._storage_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for path in paths:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                results.append(
                    TranslationSummary(
                        id=data["id"],
                        filename=data["filename"],
                        created_at=data["created_at"],
                        paragraph_count=len(data["paragraphs"]),
                    )
                )
            except (json.JSONDecodeError, KeyError) as e:
                raise AppException(f"Corrupted translation file: {path.name}") from e
        return results
