# ChatHistory model — workspace-specific conversation messages.

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from app.database import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace


class ChatRole(str, enum.Enum):
    # Member names uppercase so ChatRole.USER / ChatRole.ASSISTANT resolve correctly
    # Values uppercase to match PostgreSQL chat_role_enum (USER, ASSISTANT)
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[ChatRole] = mapped_column(
        Enum(ChatRole, name="chat_role_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="chat_messages"
    )
