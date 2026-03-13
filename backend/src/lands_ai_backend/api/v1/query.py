from fastapi import APIRouter, Depends

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
    return service.answer(payload)
