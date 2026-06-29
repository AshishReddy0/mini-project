# Generated content API routes: revision, exam, and quiz placeholders.

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.generated_content import ContentType
from app.models.user import User
from app.schemas.content import ContentGenerateRequest, GeneratedContentResponse
from app.services import content_service, workspace_service
from app.utils.security import get_current_user

router = APIRouter(tags=["Generated Content"])


@router.get(
    "/workspaces/{workspace_id}/content",
    response_model=list[GeneratedContentResponse],
)
def list_content(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all generated content in a workspace."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return content_service.list_content(db, workspace)


@router.get(
    "/workspaces/{workspace_id}/content/{content_id}",
    response_model=GeneratedContentResponse,
)
def get_content(
    workspace_id: UUID,
    content_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a single generated content item."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return content_service.get_content(db, workspace, content_id)


@router.post(
    "/workspaces/{workspace_id}/content/revision",
    response_model=GeneratedContentResponse,
    status_code=201,
)
def generate_revision(
    workspace_id: UUID,
    data: ContentGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a revision notes record."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return content_service.create_content(
        db, workspace, ContentType.REVISION, data
    )


@router.post(
    "/workspaces/{workspace_id}/content/exam",
    response_model=GeneratedContentResponse,
    status_code=201,
)
def generate_exam(
    workspace_id: UUID,
    data: ContentGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create an exam answer record (placeholder until Phase 3)."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return content_service.create_content(
        db, workspace, ContentType.EXAM, data
    )


@router.post(
    "/workspaces/{workspace_id}/content/quiz",
    response_model=GeneratedContentResponse,
    status_code=201,
)
def generate_quiz(
    workspace_id: UUID,
    data: ContentGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a quiz record (placeholder until Phase 3)."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return content_service.create_content(
        db, workspace, ContentType.QUIZ, data
    )


@router.delete(
    "/workspaces/{workspace_id}/content/{content_id}",
    status_code=204,
)
def delete_content(
    workspace_id: UUID,
    content_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    workspace = workspace_service.get_workspace_for_user(
        db, workspace_id, current_user
    )
    content_service.delete_content(db, workspace, content_id)