from fastapi import APIRouter

from lands_ai_backend.api.v1.audit import router as audit_router
from lands_ai_backend.api.v1.calculators import router as calculators_router
from lands_ai_backend.api.v1.knowledge import router as knowledge_router
from lands_ai_backend.api.v1.query import router as query_router
from lands_ai_backend.api.v1.suggestions import router as suggestions_router

api_router = APIRouter()
api_router.include_router(query_router, prefix="/query", tags=["query"])
api_router.include_router(audit_router, prefix="/audit", tags=["audit"])
api_router.include_router(
    knowledge_router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(
    suggestions_router, prefix="/suggestions", tags=["suggestions"])
api_router.include_router(
    calculators_router, prefix="/calculators", tags=["calculators"])
