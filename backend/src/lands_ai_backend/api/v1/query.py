from fastapi import APIRouter, Depends, status

from lands_ai_backend.api.errors import ServiceError
from lands_ai_backend.schemas.query import QueryRequest, QueryResponse
from lands_ai_backend.services.query_orchestration import QueryOrchestrationService

router = APIRouter()


def get_query_service() -> QueryOrchestrationService:
    return QueryOrchestrationService()


@router.post("", response_model=QueryResponse)
def ask_legal_query(
    payload: QueryRequest,
    service: QueryOrchestrationService = Depends(get_query_service),
) -> QueryResponse:
    try:
        return service.answer(payload)
    except Exception as exc:
        raise ServiceError(
            code="QUERY_FAILED",
            message="Unable to process the legal query right now.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc
