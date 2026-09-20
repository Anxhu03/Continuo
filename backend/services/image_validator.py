"""
CONTINUO — Image Validation & Metadata Extraction Service
Validates image files via header magic bytes signatures, extracts dimensions safely
using Pillow, computes cryptographic checksums, and enforces upload limits.
"""

from dataclasses import dataclass
import hashlib
import io
import os
from typing import Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from PIL import Image

from backend.config import settings

# Supported magic bytes signatures
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
RIFF_MAGIC = b"RIFF"
WEBP_MAGIC = b"WEBP"


@dataclass
class ValidatedImage:
    stream: io.BytesIO
    mime_type: str
    image_format: str
    safe_extension: str
    file_size: int
    width: Optional[int]
    height: Optional[int]
    checksum_sha256: str
    original_filename: str


def detect_image_format_from_bytes(header: bytes) -> Tuple[str, str, str]:
    """
    Inspect magic bytes to determine image format, MIME type, and safe extension.
    Rejects unsupported formats or files with invalid signatures.
    Returns: (image_format, mime_type, safe_extension)
    """
    if len(header) < 12:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File is too small to be a valid image or header is truncated."
        )

    if header.startswith(PNG_MAGIC):
        return "png", "image/png", "png"
    elif header.startswith(JPEG_MAGIC):
        return "jpeg", "image/jpeg", "jpg"
    elif header.startswith(RIFF_MAGIC) and header[8:12] == WEBP_MAGIC:
        return "webp", "image/webp", "webp"

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Unsupported or invalid image format. Supported formats: PNG, JPEG, WebP."
    )


def sanitize_filename(filename: Optional[str]) -> str:
    """Sanitize the original filename to prevent directory traversal or header injection."""
    if not filename:
        return "unnamed_image"
    # Take only basename and strip null bytes
    clean = os.path.basename(filename.replace("\\", "/")).replace("\0", "").strip()
    return clean[:255] if clean else "unnamed_image"


async def process_and_validate_upload(
    upload_file: UploadFile,
    max_size_bytes: Optional[int] = None
) -> ValidatedImage:
    """
    Safely read UploadFile in bounded chunks, verify magic bytes,
    enforce size bounds, compute SHA-256, and extract dimensions.
    """
    limit = max_size_bytes or settings.MAX_UPLOAD_SIZE_BYTES
    sha256 = hashlib.sha256()
    buffer = bytearray()
    chunk_size = 64 * 1024  # 64 KB chunks

    while True:
        chunk = await upload_file.read(chunk_size)
        if not chunk:
            break
        buffer.extend(chunk)
        sha256.update(chunk)
        if len(buffer) > limit:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Uploaded file exceeds maximum allowed size of {limit} bytes."
            )

    total_size = len(buffer)
    if total_size == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empty file uploaded. Please provide a valid image."
        )

    raw_bytes = bytes(buffer)

    # 1. Magic bytes detection
    image_format, mime_type, safe_ext = detect_image_format_from_bytes(raw_bytes[:16])

    # 2. Check for contradictory client MIME types (MIME spoofing detection)
    client_content_type = (upload_file.content_type or "").lower().strip()
    if client_content_type and not client_content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Content-Type '{client_content_type}' does not match detected image format."
        )

    # 3. Dimensions extraction via Pillow
    width: Optional[int] = None
    height: Optional[int] = None
    try:
        with Image.open(io.BytesIO(raw_bytes)) as pil_img:
            # verify() audits headers and structure without rendering pixels
            pil_img.verify()
            # Reopen to read dimensions safely after verify closes image
            with Image.open(io.BytesIO(raw_bytes)) as dimension_img:
                width, height = dimension_img.size
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image structure is corrupted or unreadable: {exc}"
        )

    return ValidatedImage(
        stream=io.BytesIO(raw_bytes),
        mime_type=mime_type,
        image_format=image_format,
        safe_extension=safe_ext,
        file_size=total_size,
        width=width,
        height=height,
        checksum_sha256=sha256.hexdigest(),
        original_filename=sanitize_filename(upload_file.filename),
    )
