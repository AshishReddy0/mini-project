# Pydantic schemas for workspace chat.

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.chat_history import ChatRole


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    active_node_title: str | None = None
    active_node_summary: str | None = None


class ChatMessageResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    role: ChatRole
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatReplyResponse(BaseModel):
    """Returned after sending a chat message (user + assistant pair)."""
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
