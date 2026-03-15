from fastapi import APIRouter, status

from lands_ai_backend.api.errors import ServiceError
from lands_ai_backend.schemas.suggestions import SuggestionResponse
from lands_ai_backend.services.suggestions import SuggestionService

router = APIRouter()

@router.get("", response_model=SuggestionResponse)
async def get_suggestions():
    try:
        return SuggestionResponse(suggestions=SuggestionService.get_suggestions())
    except Exception as exc:
        raise ServiceError(
            code="SUGGESTIONS_FETCH_FAILED",
            message="Unable to fetch suggestions right now.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc
