import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, func, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class MasteryStatus(str, enum.Enum):
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    MASTERED = "mastered"

class ConceptNode(Base):
    __tablename__ = "concept_nodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    unit_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), default="medium")
    order_hint: Mapped[int] = mapped_column(Integer, default=0)
    # sub_points: list of {"title": str, "description": str} objects extracted during graph generation.
    # Stored per-node so clicking a roadmap node shows immediate rich detail without extra API calls.
    sub_points: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # answer_cache: generated Markdown answer for this concept from reference notes.
    # Generated on first click and cached here to avoid repeated Gemini calls.
    answer_cache: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    edges_out = relationship("ConceptEdge", foreign_keys="[ConceptEdge.from_node_id]", back_populates="from_node", cascade="all, delete-orphan")
    edges_in = relationship("ConceptEdge", foreign_keys="[ConceptEdge.to_node_id]", back_populates="to_node", cascade="all, delete-orphan")
    masteries = relationship("NodeMastery", back_populates="node", cascade="all, delete-orphan")

class ConceptEdge(Base):
    __tablename__ = "concept_edges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concept_nodes.id", ondelete="CASCADE"), nullable=False)
    to_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concept_nodes.id", ondelete="CASCADE"), nullable=False)
    relation: Mapped[str] = mapped_column(String(50), default="prerequisite")

    from_node = relationship("ConceptNode", foreign_keys=[from_node_id], back_populates="edges_out")
    to_node = relationship("ConceptNode", foreign_keys=[to_node_id], back_populates="edges_in")

class NodeMastery(Base):
    __tablename__ = "node_masteries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concept_nodes.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="locked")  # locked / unlocked / mastered
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    node = relationship("ConceptNode", back_populates="masteries")
