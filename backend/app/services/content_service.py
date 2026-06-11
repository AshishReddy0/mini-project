# Generated content service — revision, exam, and quiz records.
# Phase 2 stores placeholder content; Phase 3 connects Gemini API.

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.generated_content import ContentType, GeneratedContent
from app.models.workspace import Workspace
from app.schemas.content import ContentGenerateRequest

# Shown until Phase 3 AI generation is implemented
PHASE_3_PLACEHOLDER = (
    "AI generation is not yet connected. "
    "This record was created in Phase 2 as a placeholder. "
    "Phase 3 will generate real content using the Gemini API."
)


def list_content(db: Session, workspace: Workspace) -> list[GeneratedContent]:
    """Return all generated content for a workspace."""
    return (
        db.query(GeneratedContent)
        .filter(GeneratedContent.workspace_id == workspace.id)
        .order_by(GeneratedContent.created_at.desc())
        .all()
    )


def get_content(
    db: Session, workspace: Workspace, content_id: UUID
) -> GeneratedContent:
    """Fetch a single generated content item."""
    item = (
        db.query(GeneratedContent)
        .filter(
            GeneratedContent.id == content_id,
            GeneratedContent.workspace_id == workspace.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated content not found",
        )
    return item


def create_placeholder_content(
    db: Session,
    workspace: Workspace,
    content_type: ContentType,
    data: ContentGenerateRequest,
) -> GeneratedContent:
    """
    Create a generated content record with placeholder text.
    Accepts an optional topic/title so the API shape matches Phase 3.
    """
    default_titles = {
        ContentType.REVISION: "Revision Notes",
        ContentType.EXAM: "Exam Answer",
        ContentType.QUIZ: "Practice Quiz",
    }

    title = data.title or default_titles[content_type]
    if data.topic:
        title = f"{title}: {data.topic}"

    item = GeneratedContent(
        workspace_id=workspace.id,
        content_type=content_type,
        title=title,
        content=PHASE_3_PLACEHOLDER,
        metadata_json={"topic": data.topic, "phase": 2, "status": "placeholder"},
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
