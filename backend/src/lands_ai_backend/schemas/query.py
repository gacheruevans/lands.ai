from datetime import datetime

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_id: str = Field(...,
                           description="Unique source document identifier")
    chunk_id: str = Field(...,
                          description="Chunk identifier used for retrieval")
    title: str = Field(..., description="Human-readable source title")
    source_type: str = Field(...,
                             description="Origin classification (law/procedure/regulation)")
    snippet: str = Field(..., description="Relevant snippet returned to user")
    retrieval_score: float = Field(..., ge=0.0, le=1.0)
    semantic_score: float = Field(..., ge=0.0, le=1.0)
    lexical_score: float = Field(..., ge=0.0, le=1.0)
    matched_terms: list[str] = Field(default_factory=list)
    matched_topics: list[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3,
                          description="User legal/property question")
    jurisdiction: str = Field(
        default="KE", description="Jurisdiction code (default: KE)")
    source_types: list[str] = Field(
        default_factory=list,
        description="Optional source type filter, e.g. ['law','procedure']",
    )
    topics: list[str] = Field(
        default_factory=list,
        description="Optional topic filter, e.g. ['leasehold','stamp-duty']",
    )


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    evidence_confidence: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    online_research_used: bool = False
    online_docs_ingested: int = 0
    suggestions: list[str] = Field(default_factory=list)
    disclaimer: str
    audit_event_id: str
    created_at: datetime
