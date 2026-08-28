"""Safe file-upload helpers: extension checks, size caps, path sanitization."""

import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status

from backend.config import settings

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: Optional[str]) -> str:
    """Strip directories and allow only a conservative filename charset."""
    base = Path(name or "upload").name
    cleaned = _UNSAFE_CHARS.sub("_", base).strip("._")
    return (cleaned or "upload")[:180]


def validate_file_extension(filename: Optional[str]) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {settings.ALLOWED_FILE_EXTENSIONS}",
        )
    return ext


async def save_upload(file: UploadFile, max_mb: Optional[int] = None) -> str:
    """
    Stream an upload to a temp file with a hard size cap.
    Cleans up the temp file if validation fails.
    """
    ext = validate_file_extension(file.filename)
    max_bytes = (max_mb or settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024
    tmp_path = None
    size = 0
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=ext, dir=settings.UPLOAD_DIR
        ) as tmp:
            tmp_path = tmp.name
            while True:
                chunk = await file.read(64 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
                    )
                tmp.write(chunk)
        if size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )
        return tmp_path
    except Exception:
        unlink_quiet(tmp_path)
        raise


def unlink_quiet(path: Optional[str]) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.unlink(path)
    except OSError:
        pass
