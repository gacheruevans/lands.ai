from fastapi import APIRouter, Depends

from lands_ai_backend.schemas.knowledge import (
    IngestDocumentRequest,
    IngestDocumentResponse,
)
from lands_ai_backend.services.knowledge_ingestion import KnowledgeIngestionService

router = APIRouter()


def get_ingestion_service() -> KnowledgeIngestionService:
    return KnowledgeIngestionService()


@router.post("/ingest", response_model=IngestDocumentResponse)
def ingest_document(
    payload: IngestDocumentRequest,
    service: KnowledgeIngestionService = Depends(get_ingestion_service),
) -> IngestDocumentResponse:
    return service.ingest(payload)
