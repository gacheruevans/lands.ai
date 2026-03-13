from dataclasses import dataclass

from psycopg.types.json import Json

from lands_ai_backend.core.db import get_db_connection
from lands_ai_backend.core.config import settings
from lands_ai_backend.schemas.query import Citation
from lands_ai_backend.services.provider_adapter import ProviderAdapter
from lands_ai_backend.services.text_processing import (
    best_snippet,
    keyword_overlap_score,
    title_relevance_bonus,
    tokenize_query_terms,
)


@dataclass
class RetrievalOutcome:
    citations: list[Citation]
    evidence_confidence: float
    candidate_count: int


class RetrievalRagService:
    def __init__(self, provider: ProviderAdapter | None = None) -> None:
        self.provider = provider or ProviderAdapter()

    def retrieve(self, question: str, jurisdiction: str, k: int | None = None) -> RetrievalOutcome:
        effective_k = k or settings.retrieval_top_k
        query_embedding = self.provider.embed_text(question)
        vector_literal = self._vector_literal(query_embedding)
        query_terms = tokenize_query_terms(question)

        sql = """
            SELECT c.id AS chunk_id, c.source_id, c.title, c.content,
                   (c.embedding <=> %s::vector) AS distance
            FROM kb_chunks c
            JOIN kb_sources s ON s.id = c.source_id
            WHERE s.jurisdiction = %s
            ORDER BY distance ASC
            LIMIT %s
        """

        rows: list[dict] = []
        for conn in get_db_connection():
            with conn.cursor() as cur:
                cur.execute(sql, (vector_literal, jurisdiction, settings.retrieval_candidate_pool))
                rows = cur.fetchall()

        ranked_candidates = []
        for row in rows:
            semantic_score = max(0.0, min(1.0, 1.0 - float(row["distance"])))
            lexical_score, matched_terms = keyword_overlap_score(row["content"], query_terms)
            title_bonus = title_relevance_bonus(row["title"], query_terms)
            retrieval_score = min(1.0, semantic_score * 0.68 + lexical_score * 0.24 + title_bonus)

            ranked_candidates.append(
                {
                    "source_id": row["source_id"],
                    "chunk_id": row["chunk_id"],
                    "title": row["title"],
                    "snippet": best_snippet(row["content"], query_terms),
                    "retrieval_score": retrieval_score,
                    "semantic_score": semantic_score,
                    "lexical_score": lexical_score,
                    "matched_terms": matched_terms,
                }
            )

        ranked_candidates.sort(
            key=lambda item: (
                item["retrieval_score"],
                item["semantic_score"],
                item["lexical_score"],
            ),
            reverse=True,
        )

        citations: list[Citation] = []
        source_counts: dict[str, int] = {}
        for item in ranked_candidates:
            duplicate_penalty = source_counts.get(item["source_id"], 0) * 0.08
            adjusted_score = max(0.0, item["retrieval_score"] - duplicate_penalty)
            if adjusted_score < settings.min_citation_score:
                continue

            citations.append(
                Citation(
                    source_id=item["source_id"],
                    chunk_id=item["chunk_id"],
                    title=item["title"],
                    snippet=item["snippet"],
                    retrieval_score=adjusted_score,
                    semantic_score=item["semantic_score"],
                    lexical_score=item["lexical_score"],
                    matched_terms=item["matched_terms"],
                )
            )
            source_counts[item["source_id"]] = source_counts.get(item["source_id"], 0) + 1
            if len(citations) >= effective_k:
                break

        evidence_confidence = self._evidence_confidence(citations, query_terms)
        return RetrievalOutcome(
            citations=citations,
            evidence_confidence=evidence_confidence,
            candidate_count=len(ranked_candidates),
        )

    @staticmethod
    def _evidence_confidence(citations: list[Citation], query_terms: list[str]) -> float:
        if not citations:
            return 0.0

        average_score = sum(citation.retrieval_score for citation in citations) / len(citations)
        matched_terms = {term for citation in citations for term in citation.matched_terms}
        coverage = len(matched_terms) / max(1, len(set(query_terms)))
        multi_citation_bonus = min(0.12, max(0, len(citations) - 1) * 0.04)

        return min(1.0, average_score * 0.72 + coverage * 0.2 + multi_citation_bonus)

    @staticmethod
    def _vector_literal(embedding: list[float]) -> str:
        return "[" + ",".join(f"{v:.8f}" for v in embedding) + "]"


class KnowledgeIngestionRepository:
    @staticmethod
    def upsert_source(
        source_id: str,
        title: str,
        jurisdiction: str,
        source_type: str,
    ) -> None:
        sql = """
            INSERT INTO kb_sources (id, title, jurisdiction, source_type)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET title = EXCLUDED.title,
                          jurisdiction = EXCLUDED.jurisdiction,
                          source_type = EXCLUDED.source_type
        """
        for conn in get_db_connection():
            with conn.cursor() as cur:
                cur.execute(sql, (source_id, title, jurisdiction, source_type))
            conn.commit()

    @staticmethod
    def replace_chunks(source_id: str, chunks: list[dict[str, str | list[float]]]) -> None:
        delete_sql = "DELETE FROM kb_chunks WHERE source_id = %s"
        insert_sql = """
            INSERT INTO kb_chunks (id, source_id, title, content, metadata, embedding)
            VALUES (%s, %s, %s, %s, %s, %s::vector)
        """

        for conn in get_db_connection():
            with conn.cursor() as cur:
                cur.execute(delete_sql, (source_id,))
                for chunk in chunks:
                    cur.execute(
                        insert_sql,
                        (
                            chunk["id"],
                            source_id,
                            chunk["title"],
                            chunk["content"],
                            Json(chunk["metadata"]),
                            chunk["vector_literal"],
                        ),
                    )
            conn.commit()
