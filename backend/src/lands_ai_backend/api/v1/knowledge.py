from fastapi import APIRouter, Depends, Query

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
    service: KnowledgeIngestionService = Depends(get_ingestion_service),
) -> IngestDocumentResponse:
    return service.ingest(payload)


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
