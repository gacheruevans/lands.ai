from fastapi import APIRouter
from lands_ai_backend.schemas.suggestions import SuggestionResponse
from lands_ai_backend.services.suggestions import SuggestionService

router = APIRouter()

@router.get("", response_model=SuggestionResponse)
async def get_suggestions():
    return SuggestionResponse(suggestions=SuggestionService.get_suggestions())
