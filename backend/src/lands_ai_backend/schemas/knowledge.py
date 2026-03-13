from datetime import datetime

from pydantic import BaseModel, Field


class IngestDocumentRequest(BaseModel):
    source_id: str = Field(..., min_length=3,
                           description="Stable unique source ID")
    title: str = Field(..., min_length=3)
    text: str = Field(..., min_length=20)
    jurisdiction: str = Field(default="KE")
    source_type: str = Field(default="law")


class IngestDocumentResponse(BaseModel):
    source_id: str
    chunks_created: int
    created_at: datetime
