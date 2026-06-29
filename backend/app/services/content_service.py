# Generated content service — revision, exam, and quiz records.
# Phase 2 stores placeholder content; Phase 3 connects Gemini API.

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.generated_content import ContentType, GeneratedContent
from app.models.workspace import Workspace
from app.schemas.content import ContentGenerateRequest
from app.services.gemini_service import generate_content
from app.models.document import Document


def build_workspace_text(workspace: Workspace) -> str:
    text = ""

    for document in workspace.documents:
        if document.extracted_text:
            text += document.extracted_text.content + "\n"

    return text

# Shown until Phase 3 AI generation is implemented



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


def create_content(
    db: Session,
    workspace: Workspace,
    content_type: ContentType,
    data: ContentGenerateRequest,
) -> GeneratedContent:

    document_text = ""

    if data.document_id:
        selected_document = None

        for document in workspace.documents:
            if str(document.id) == str(data.document_id):
                selected_document = document
                break

        if not selected_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Selected document not found",
        )

        if selected_document.extracted_text:
           document_text = selected_document.extracted_text.content

    else:
       document_text = build_workspace_text(workspace)

    if not document_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No extracted study material found in workspace",
        )

    if content_type == ContentType.REVISION:
        prompt = f"""
        Create revision notes from:

        {document_text}

        Rules:
        - Easy language
        - Bullet points
        - Important concepts
        - Definitions
        """

    elif content_type == ContentType.EXAM:
        prompt = f"""
        Generate exam preparation material.

        Text:

        {document_text}

        Include:
        1. 2 mark questions
        2. 5 mark questions
        3. Long questions
        4. Important topics
        """

    elif content_type == ContentType.QUIZ:
        question_count = data.question_count or 10
        
        prompt = f"""
        Generate {question_count} MCQs.

        Text:

        {document_text}

        Return ONLY valid JSON.
        Do not add explanation, headings, markdown, or extra text.
        Format:
        [
            {{
                "question": "...",
                "options": {{"
                "A": "...",
                "B": "...",
                "C": "...",
                "D": "..."
               }},
               "answer": "A"
            }}
        ]
        """

    generated_text = generate_content(prompt)

    default_titles = {
        ContentType.REVISION: "Revision Notes",
        ContentType.EXAM: "Exam Preparation",
        ContentType.QUIZ: "Practice Quiz",
    }

    title = data.title or default_titles[content_type]

    item = GeneratedContent(
        workspace_id=workspace.id,
        content_type=content_type,
        title=title,
        content=generated_text,
        metadata_json={
            "topic": data.topic,
            "phase": 3,
            "generated_by": "gemini"
        },
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item
def delete_content(db: Session, workspace, content_id):
    content = get_content(db, workspace, content_id)
    db.delete(content)
    db.commit()