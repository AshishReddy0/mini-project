# Workspace chat service — stores messages and returns placeholder replies.
# Phase 3 will replace the stub assistant response with Gemini API output.

from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory, ChatRole
from app.models.workspace import Workspace

PHASE_3_CHAT_PLACEHOLDER = (
    "AI chat is not yet connected. "
    "Your message was saved. Phase 3 will enable workspace-aware answers "
    "using the Gemini API and your uploaded study materials."
)


def get_chat_history(db: Session, workspace: Workspace) -> list[ChatHistory]:
    """Return all chat messages for a workspace, oldest first."""
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.workspace_id == workspace.id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )


def send_message(
    db: Session, workspace: Workspace, message: str
) -> tuple[ChatHistory, ChatHistory]:
    """
    Save the user's message and a placeholder assistant reply.
    Returns both messages so the client can display the exchange.
    """
    user_message = ChatHistory(
        workspace_id=workspace.id,
        role=ChatRole.USER,
        message=message,
    )
    assistant_message = ChatHistory(
        workspace_id=workspace.id,
        role=ChatRole.ASSISTANT,
        message=PHASE_3_CHAT_PLACEHOLDER,
    )

    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)

    return user_message, assistant_message
