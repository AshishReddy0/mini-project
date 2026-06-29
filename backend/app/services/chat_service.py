# Workspace-aware AI chat service using Gemini + extracted documents.

from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory, ChatRole
from app.models.workspace import Workspace
from app.services.gemini_service import generate_content


def get_chat_history(db: Session, workspace: Workspace) -> list[ChatHistory]:
    """Return all chat messages for a workspace."""
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.workspace_id == workspace.id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )


def build_workspace_context(workspace: Workspace) -> str:
    """
    Collect extracted text from all workspace documents.
    """
    text = ""

    for document in workspace.documents:
        if document.extracted_text:
            text += document.extracted_text.content + "\n"

    return text


def send_message(
    db: Session,
    workspace: Workspace,
    message: str,
) -> tuple[ChatHistory, ChatHistory]:
    """
    Save user message and generate workspace-aware AI reply.
    """

    user_message = ChatHistory(
        workspace_id=workspace.id,
        role=ChatRole.USER,
        message=message,
    )

    workspace_context = build_workspace_context(workspace)

    prompt = f"""
    You are a study assistant.

    Answer ONLY using this study material:

    {workspace_context}

    Student Question:
    {message}

    Rules:
    - Be accurate
    - Be simple
    - Stay within provided content
    """

    ai_response = generate_content(prompt)

    assistant_message = ChatHistory(
        workspace_id=workspace.id,
        role=ChatRole.ASSISTANT,
        message=ai_response,
    )

    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)

    return user_message, assistant_message