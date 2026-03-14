from pydantic import BaseModel, Field

class SuggestionResponse(BaseModel):
    suggestions: list[str] = Field(..., description="List of suggested questions")
