from uuid import UUID
from pydantic import BaseModel

class RoadmapGenerateRequest(BaseModel):
    document_id: UUID | None = None
