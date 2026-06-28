# Utility functions for file validation and saving.

import os
from pathlib import Path
from fastapi import HTTPException, UploadFile

UPLOAD_DIR = "uploads"
ALLOWED_TYPES = {
    ".pdf": "pdf",
    ".docx": "docx",
}


def validate_file_type(filename: str) -> str:
    """
    Validate uploaded file extension.
    Returns normalized file type.
    """
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed.",
        )

    return ALLOWED_TYPES[extension]


async def save_uploaded_file(file: UploadFile) -> tuple[str, int]:
    """
    Save uploaded file to local storage.
    Returns file path and file size.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    return file_path, len(content)