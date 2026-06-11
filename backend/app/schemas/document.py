# Pydantic schemas for document upload and listing.

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    filename: str
    file_type: str
    file_size: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}
