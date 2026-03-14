from lands_ai_backend.core.config import settings
from lands_ai_backend.schemas.query import QueryRequest, QueryResponse
from lands_ai_backend.services.audit_logging import AuditLoggingService
from lands_ai_backend.services.online_research import OnlineResearchService
from lands_ai_backend.services.provider_adapter import ProviderAdapter
from lands_ai_backend.services.retrieval_rag import RetrievalRagService


class QueryOrchestrationService:
    """Entry-point service for legal query handling."""

    def __init__(self) -> None:
        self.provider = ProviderAdapter()
        self.retrieval = RetrievalRagService(provider=self.provider)
        self.audit = AuditLoggingService()
        self.online_research = OnlineResearchService()

    def answer(self, payload: QueryRequest) -> QueryResponse:
        online_docs_ingested = 0
        retrieval = self.retrieval.retrieve(
            question=payload.question,
            jurisdiction=payload.jurisdiction,
            k=settings.retrieval_top_k,
            source_types=payload.source_types,
            topics=payload.topics,
        )
        citations = retrieval.citations
        evidence_confidence = retrieval.evidence_confidence

        if self._needs_more_evidence(citations, evidence_confidence):
            online_docs_ingested = self._attempt_online_research(payload)
            if online_docs_ingested > 0:
                refreshed = self.retrieval.retrieve(
                    question=payload.question,
                    jurisdiction=payload.jurisdiction,
                    k=settings.retrieval_top_k,
                    source_types=payload.source_types,
                    topics=payload.topics,
                )
                citations = refreshed.citations
                evidence_confidence = refreshed.evidence_confidence

        if self._needs_more_evidence(citations, evidence_confidence):
            answer = self._low_evidence_answer(payload.question, citations)
            confidence = min(evidence_confidence,
                             settings.min_answer_confidence)
        else:
            generated_answer, model_confidence = self.provider.generate_answer(
                payload.question, citations)
            confidence = min(
                1.0,
                evidence_confidence * 0.72 + model_confidence * 0.28,
            )
            if confidence < settings.min_answer_confidence:
                answer = self._low_evidence_answer(payload.question, citations)
            else:
                answer = generated_answer

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
            evidence_confidence=evidence_confidence,
            confidence=confidence,
            online_research_used=online_docs_ingested > 0,
            online_docs_ingested=online_docs_ingested,
            disclaimer=(
                "Informational guidance only. This is not legal advice. "
                "Consult a qualified advocate for case-specific interpretation."
            ),
            audit_event_id=audit_event_id,
            created_at=created_at,
        )

    @staticmethod
    def _needs_more_evidence(citations: list, evidence_confidence: float) -> bool:
        return (
            len(citations) < settings.min_citations_required
            or evidence_confidence < settings.min_answer_confidence
        )

    def _attempt_online_research(self, payload: QueryRequest) -> int:
        if not settings.enable_online_research:
            return 0

        if payload.source_types and "web_reference" not in payload.source_types:
            # Respect explicit source-type filtering from the user.
            return 0

        return self.online_research.search_and_ingest(
            question=payload.question,
            jurisdiction=payload.jurisdiction,
        )

    @staticmethod
    def _low_evidence_answer(question: str, citations: list) -> str:
        if not citations:
            return (
                f"I do not yet have enough grounded Kenyan legal material to answer '{question}' "
                "with sufficient confidence. Please provide more specifics or consult an advocate "
                "or the relevant public office."
            )

        source_list = "; ".join(citation.title for citation in citations[:2])
        return (
            f"I found partially relevant material for '{question}', but the evidence is not strong "
            f"enough for a confident procedural answer. Review these sources first: {source_list}. "
            "For action on a real transaction, verify details with the land registry, county office, or a qualified advocate."
        )
