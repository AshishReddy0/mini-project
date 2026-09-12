# Document upload and management logic.


from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session


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


from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.document import Document
from app.utils.file_handler import validate_file_type, save_uploaded_file


async def upload_document(db: Session, workspace, file: UploadFile):
    """
    Upload document, extract text, and store both metadata + extracted content.
    """

    file_type = validate_file_type(file.filename)
    file_path, file_size = await save_uploaded_file(file)

    document = Document(
        workspace_id=workspace.id,
        filename=file.filename,
        file_type=file_type,
        file_path=file_path,
        file_size=file_size,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    extracted_content = ""

    # Text extraction based on file type with fallbacks
    if file_type == "pdf":
        from app.services.pdf_service import extract_pdf_text
        extracted_content = extract_pdf_text(file_path)

    elif file_type in ["docx", "doc"]:
        try:
            from app.services.docx_service import extract_docx_text
            extracted_content = extract_docx_text(file_path)
        except Exception:
            extracted_content = ""

    elif file_type == "txt":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                extracted_content = f.read()
        except Exception:
            extracted_content = ""

    # Universal fallback if extracted_content is still empty
    if not extracted_content or not extracted_content.strip():
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                extracted_content = f.read()
        except Exception:
            pass

    extracted_text = ExtractedText(
        document_id=document.id,
        content=extracted_content or "",
    )

    db.add(extracted_text)
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
