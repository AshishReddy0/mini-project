# Pydantic schemas for generated content (revision, exam, quiz).

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.generated_content import ContentType


class ContentGenerateRequest(BaseModel):
    """Optional topic or prompt — full AI generation comes in Phase 3."""
    topic: str | None = Field(default=None, max_length=500)
    title: str | None = Field(default=None, max_length=255)
    document_id: UUID | None = None
    question_count: int | None = Field(default=10, ge=1, le=20)


class GeneratedContentResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    content_type: ContentType
    title: str
    content: str
    metadata_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
