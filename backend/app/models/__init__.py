# Import all models so they are registered with SQLAlchemy metadata.

from app.models.chat_history import ChatHistory
from app.models.document import Document
from app.models.extracted_text import ExtractedText
from app.models.generated_content import GeneratedContent
from app.models.user import User
from app.models.workspace import Workspace

__all__ = [
    "User",
    "Workspace",
    "Document",
    "ExtractedText",
    "GeneratedContent",
    "ChatHistory",
]
