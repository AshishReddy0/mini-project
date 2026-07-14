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
    active_node_title: str | None = None,
    active_node_summary: str | None = None,
) -> tuple[ChatHistory, ChatHistory]:
    """
    Save user message and generate workspace-aware AI reply.
    """

    user_message = ChatHistory(
        workspace_id=workspace.id,
        role=ChatRole.USER,
        message=message,
    )

    workspace_context = build_workspace_context(workspace).strip()

    # If no study materials are uploaded or provided in the workspace, prevent long generic essays
    if not workspace_context:
        prompt = f"""
        The user is asking: "{message}".
        There are currently NO study materials, files, or syllabus uploaded to this workspace.
        State this clearly and concisely in 1-2 sentences. Tell them to upload study materials in the left sidebar or create a roadmap to get started. Do not explain general definitions of the words in the query unless they explicitly asked you to "explain the word X generally".
        """
    else:
        context_scope = f"Using this study material:\n{workspace_context}"
        if active_node_title and active_node_summary:
            context_scope = (
                f"You are currently assisting the student on the active concept:\n"
                f"Concept: {active_node_title}\n"
                f"Summary: {active_node_summary}\n\n"
                f"Scope your answer to prioritize explaining this concept. Connect it to the broader workspace study materials when helpful:\n"
                f"{workspace_context}"
            )

        prompt = f"""
        You are an expert study assistant helping a student understand their course materials.

        {context_scope}

        Student Question:
        {message}

        Rules:
        - Be concise and direct. Match the length of your response to the user's query intent. If they ask a quick question, give a short, straight-to-the-point answer. Do not write unnecessarily long essays.
        - Stay within the context of the provided materials. If the answer cannot be found in the documents, state that clearly and briefly.
        - Format your response beautifully using Markdown. Use headings, bold text, bullet points, tables, and code blocks where appropriate.
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