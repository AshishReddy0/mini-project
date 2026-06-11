# Document upload and management logic.

import uuid
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import ALLOWED_CONTENT_TYPES, MAX_UPLOAD_SIZE_BYTES, UPLOAD_DIR
from app.models.document import Document
from app.models.extracted_text import ExtractedText
from app.models.workspace import Workspace


def list_documents(db: Session, workspace: Workspace) -> list[Document]:
    """List all documents in a workspace."""
    return db.query(Document).filter(Document.workspace_id == workspace.id).all()


def get_document(db: Session, workspace: Workspace, document_id: UUID) -> Document:
    """Fetch a single document within a workspace."""
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.workspace_id == workspace.id,
        )
        .first()
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


async def upload_document(
    db: Session, workspace: Workspace, file: UploadFile
) -> Document:
    """
    Save an uploaded PDF to disk and store metadata in the database.
    Phase 3 will populate extracted_text.content after PDF parsing.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported in Phase 2",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds the 10 MB upload limit",
        )

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # Store files in uploads/<workspace_id>/ to keep them organized
    workspace_dir = UPLOAD_DIR / str(workspace.id)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename or "document.pdf").name
    stored_name = f"{uuid.uuid4()}_{safe_name}"
    file_path = workspace_dir / stored_name

    file_path.write_bytes(contents)

    document = Document(
        workspace_id=workspace.id,
        filename=safe_name,
        file_type="pdf",
        file_path=str(file_path),
        file_size=len(contents),
    )
    db.add(document)
    db.flush()

    # Create empty extracted text row — Phase 3 fills this after parsing
    extracted = ExtractedText(document_id=document.id, content="")
    db.add(extracted)

    db.commit()
    db.refresh(document)
    return document


def delete_document(db: Session, document: Document) -> None:
    """Remove document file from disk and delete database records."""
    file_path = Path(document.file_path)
    if file_path.exists():
        file_path.unlink()

    db.delete(document)
    db.commit()
