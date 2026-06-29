# Document upload and management API routes.

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services import document_service, workspace_service
from app.utils.security import get_current_user

router = APIRouter(tags=["Documents"])


@router.get(
    "/workspaces/{workspace_id}/documents",
    response_model=list[DocumentResponse],
)
def list_documents(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all documents in a workspace."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return document_service.list_documents(db, workspace)


@router.post(
    "/workspaces/{workspace_id}/documents",
    response_model=DocumentResponse,
    status_code=201,
)
async def upload_document(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
):
    """Upload a PDF or DOCX document to a workspace."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return await document_service.upload_document(db, workspace, file)


@router.get(
    "/workspaces/{workspace_id}/documents/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    workspace_id: UUID,
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get metadata for a single document."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return document_service.get_document(db, workspace, document_id)


@router.delete(
    "/workspaces/{workspace_id}/documents/{document_id}",
    status_code=204,
)
def delete_document(
    workspace_id: UUID,
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a document and its extracted text record."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    document = document_service.get_document(db, workspace, document_id)
    document_service.delete_document(db, document)
