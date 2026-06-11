# Workspace chat API routes.

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.chat import ChatMessageResponse, ChatReplyResponse, ChatRequest
from app.services import chat_service, workspace_service
from app.utils.security import get_current_user

router = APIRouter(tags=["Chat"])


@router.get(
    "/workspaces/{workspace_id}/chat",
    response_model=list[ChatMessageResponse],
)
def get_chat_history(
    workspace_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Return the full chat history for a workspace."""
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    return chat_service.get_chat_history(db, workspace)


@router.post(
    "/workspaces/{workspace_id}/chat",
    response_model=ChatReplyResponse,
    status_code=201,
)
def send_chat_message(
    workspace_id: UUID,
    data: ChatRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Send a message to the workspace chat.
    Phase 2 saves the message and returns a placeholder assistant reply.
    """
    workspace = workspace_service.get_workspace_for_user(db, workspace_id, current_user)
    user_msg, assistant_msg = chat_service.send_message(db, workspace, data.message)
    return ChatReplyResponse(user_message=user_msg, assistant_message=assistant_msg)
