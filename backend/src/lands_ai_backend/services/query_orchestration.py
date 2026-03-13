from lands_ai_backend.schemas.query import QueryRequest, QueryResponse
from lands_ai_backend.services.audit_logging import AuditLoggingService
from lands_ai_backend.services.provider_adapter import ProviderAdapter
from lands_ai_backend.services.retrieval_rag import RetrievalRagService


class QueryOrchestrationService:
    """Entry-point service for legal query handling."""

    def __init__(self) -> None:
        self.provider = ProviderAdapter()
        self.retrieval = RetrievalRagService(provider=self.provider)
        self.audit = AuditLoggingService()

    def answer(self, payload: QueryRequest) -> QueryResponse:
        citations = self.retrieval.retrieve(
            question=payload.question,
            jurisdiction=payload.jurisdiction,
            k=4,
        )

        answer, confidence = self.provider.generate_answer(
            payload.question, citations)
        audit_event_id, created_at = self.audit.log_event(
            question=payload.question,
            jurisdiction=payload.jurisdiction,
            answer=answer,
            citations=citations,
            confidence=confidence,
        )

        return QueryResponse(
            answer=answer,
            citations=citations,
            confidence=confidence,
            disclaimer=(
                "Informational guidance only. This is not legal advice. "
                "Consult a qualified advocate for case-specific interpretation."
            ),
            audit_event_id=audit_event_id,
            created_at=created_at,
        )
