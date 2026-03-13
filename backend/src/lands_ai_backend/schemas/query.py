from datetime import datetime

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_id: str = Field(...,
                           description="Unique source document identifier")
    chunk_id: str = Field(...,
                          description="Chunk identifier used for retrieval")
    title: str = Field(..., description="Human-readable source title")
    snippet: str = Field(..., description="Relevant snippet returned to user")


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3,
                          description="User legal/property question")
    jurisdiction: str = Field(
        default="KE", description="Jurisdiction code (default: KE)")


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float = Field(..., ge=0.0, le=1.0)
    disclaimer: str
    audit_event_id: str
    created_at: datetime
