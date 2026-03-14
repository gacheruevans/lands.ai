from fastapi import APIRouter, Depends, Query, BackgroundTasks

from lands_ai_backend.schemas.knowledge import (
    IngestDocumentRequest,
    IngestDocumentResponse,
    KnowledgeTopicsResponse,
)
from lands_ai_backend.services.knowledge_catalog import KnowledgeCatalogService
from lands_ai_backend.services.knowledge_ingestion import KnowledgeIngestionService

router = APIRouter()


def get_ingestion_service() -> KnowledgeIngestionService:
    return KnowledgeIngestionService()


def get_catalog_service() -> KnowledgeCatalogService:
    return KnowledgeCatalogService()


@router.post("/ingest", response_model=IngestDocumentResponse)
def ingest_document(
    payload: IngestDocumentRequest,
    background_tasks: BackgroundTasks,
    service: KnowledgeIngestionService = Depends(get_ingestion_service),
) -> IngestDocumentResponse:
    # Use background tasks to handle ingestion asynchronously
    background_tasks.add_task(service.ingest, payload)
    
    # Return intermediate response immediately
    from datetime import datetime, timezone
    return IngestDocumentResponse(
        source_id=payload.source_id,
        chunks_created=0, # Will be updated in background
        topics=payload.topics or [],
        created_at=datetime.now(timezone.utc),
    )


@router.get("/topics", response_model=KnowledgeTopicsResponse)
def list_topics(
    jurisdiction: str = "KE",
    source_types: list[str] = Query(default_factory=list),
    service: KnowledgeCatalogService = Depends(get_catalog_service),
) -> KnowledgeTopicsResponse:
    effective_source_types = source_types or None
    return service.get_topics(
        jurisdiction=jurisdiction,
        source_types=effective_source_types,
    )
