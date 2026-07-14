from typing import Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class GraphGenerateRequest(BaseModel):
    document_id: UUID | None = None
    # Format options chosen in the roadmap setup step
    answer_formats: list[str] | None = None   # e.g. ["meaning", "types", "application"]
    custom_format: str | None = None          # free-text format instructions
    portion_text: str | None = None           # pasted syllabus/portion text from the UI

class NodeAttemptRequest(BaseModel):
    explain_mode: bool
    score: int | None = None
    explanation: str | None = None

class ConceptNodeResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    summary: str
    difficulty: str
    unit_ref: str | None
    order_hint: int
    sub_points: list[Any] | None = None

    class Config:
        from_attributes = True

class ConceptEdgeResponse(BaseModel):
    id: UUID
    from_node_id: UUID
    to_node_id: UUID
    relation: str

    class Config:
        from_attributes = True

class NodeMasteryResponse(BaseModel):
    status: str
    attempts: int
    last_score: int | None
    feedback: str | None
    updated_at: datetime

    class Config:
        from_attributes = True

class ConceptGraphResponse(BaseModel):
    nodes: list[ConceptNodeResponse]
    edges: list[ConceptEdgeResponse]
    masteries: dict[str, NodeMasteryResponse]  # node_id string mapping
