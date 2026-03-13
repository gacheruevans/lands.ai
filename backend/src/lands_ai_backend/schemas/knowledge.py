from datetime import datetime

from pydantic import BaseModel, Field


class IngestDocumentRequest(BaseModel):
    source_id: str = Field(..., min_length=3,
                           description="Stable unique source ID")
    title: str = Field(..., min_length=3)
    text: str = Field(..., min_length=20)
    jurisdiction: str = Field(default="KE")
    source_type: str = Field(default="law")
    topics: list[str] = Field(default_factory=list)


class IngestDocumentResponse(BaseModel):
    source_id: str
    chunks_created: int
    topics: list[str]
    created_at: datetime


class TopicStat(BaseModel):
    topic: str
    chunk_count: int


class SourceTypeStat(BaseModel):
    source_type: str
    source_count: int


class KnowledgeTopicsResponse(BaseModel):
    jurisdiction: str
    topics: list[TopicStat]
    source_types: list[SourceTypeStat]
