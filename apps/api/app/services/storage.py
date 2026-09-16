import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md"}
CHUNK_SIZE = 1024 * 1024


class StorageError(ValueError):
    pass


@dataclass(frozen=True)
class StoredFile:
    path: Path
    sha256: str
    size: int
    extension: str


def normalized_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise StorageError("Only PDF, DOCX and Markdown files are supported.")
    return extension


async def save_upload(upload: UploadFile, upload_dir: Path | None = None) -> StoredFile:
    target_dir = upload_dir or settings.upload_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    extension = normalized_extension(upload.filename or "")
    temporary_path = target_dir / f".{uuid.uuid4().hex}.upload"
    digest = hashlib.sha256()
    size = 0

    try:
        async with aiofiles.open(temporary_path, "wb") as target:
            while chunk := await upload.read(CHUNK_SIZE):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise StorageError(f"File exceeds the {settings.max_upload_mb} MB limit.")
                digest.update(chunk)
                await target.write(chunk)

        if size == 0:
            raise StorageError("Uploaded file is empty.")

        final_path = target_dir / f"{uuid.uuid4().hex}{extension}"
        temporary_path.replace(final_path)
        return StoredFile(
            path=final_path,
            sha256=digest.hexdigest(),
            size=size,
            extension=extension,
        )
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()


def remove_file(path: str) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass

