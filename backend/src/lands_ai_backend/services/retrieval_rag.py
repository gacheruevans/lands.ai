from dataclasses import dataclass

from psycopg.types.json import Json

from lands_ai_backend.core.config import settings
from lands_ai_backend.core.db import get_db_connection
from lands_ai_backend.schemas.query import Citation
from lands_ai_backend.services.provider_adapter import ProviderAdapter
from lands_ai_backend.services.text_processing import (
    best_snippet,
    extract_topics,
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

    def retrieve(
        self,
        question: str,
        jurisdiction: str,
        k: int | None = None,
        source_types: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> RetrievalOutcome:
        effective_k = k or settings.retrieval_top_k
        query_embedding = self.provider.embed_text(question)
        vector_literal = self._vector_literal(query_embedding)
        query_terms = tokenize_query_terms(question)
        inferred_topics = extract_topics(question)
        effective_topics = sorted({*(topics or []), *inferred_topics})

        sql_parts = [
            """
            SELECT c.id AS chunk_id, c.source_id, c.title, c.content,
                   c.metadata, s.source_type,
                   (c.embedding <=> %s::vector) AS distance
            FROM kb_chunks c
            JOIN kb_sources s ON s.id = c.source_id
            WHERE s.jurisdiction = %s
            """
        ]
        params: list = [vector_literal, jurisdiction]

        if source_types:
            sql_parts.append("AND s.source_type = ANY(%s)")
            params.append(source_types)

        if effective_topics:
            sql_parts.append(
                """
                AND EXISTS (
                    SELECT 1
                    FROM jsonb_array_elements_text(COALESCE(c.metadata->'topics', '[]'::jsonb)) AS topic(value)
                    WHERE topic.value = ANY(%s)
                )
                """
            )
            params.append(effective_topics)

        sql_parts.append("ORDER BY distance ASC LIMIT %s")
        params.append(settings.retrieval_candidate_pool)
        sql = "\n".join(sql_parts)

        rows: list[dict] = []
        for conn in get_db_connection():
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

        ranked_candidates = []
        for row in rows:
            semantic_score = max(0.0, min(1.0, 1.0 - float(row["distance"])))
            lexical_score, matched_terms = keyword_overlap_score(
                row["content"], query_terms)
            title_bonus = title_relevance_bonus(row["title"], query_terms)

            metadata = row.get("metadata") or {}
            chunk_topics = metadata.get(
                "topics") if isinstance(metadata, dict) else []
            chunk_topics = chunk_topics if isinstance(
                chunk_topics, list) else []
            matched_topics = [
                topic for topic in effective_topics if topic in chunk_topics]
            topic_bonus = min(0.12, len(matched_topics) * 0.04)

            retrieval_score = min(
                1.0,
                semantic_score * 0.62 + lexical_score * 0.24 + title_bonus + topic_bonus,
            )

            ranked_candidates.append(
                {
                    "source_id": row["source_id"],
                    "chunk_id": row["chunk_id"],
                    "title": row["title"],
                    "source_type": row["source_type"],
                    "snippet": best_snippet(row["content"], query_terms),
                    "retrieval_score": retrieval_score,
                    "semantic_score": semantic_score,
                    "lexical_score": lexical_score,
                    "matched_terms": matched_terms,
                    "matched_topics": matched_topics,
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
            adjusted_score = max(
                0.0, item["retrieval_score"] - duplicate_penalty)
            if adjusted_score < settings.min_citation_score:
                continue

            citations.append(
                Citation(
                    source_id=item["source_id"],
                    chunk_id=item["chunk_id"],
                    title=item["title"],
                    source_type=item["source_type"],
                    snippet=item["snippet"],
                    retrieval_score=adjusted_score,
                    semantic_score=item["semantic_score"],
                    lexical_score=item["lexical_score"],
                    matched_terms=item["matched_terms"],
                    matched_topics=item["matched_topics"],
                )
            )
            source_counts[item["source_id"]] = source_counts.get(
                item["source_id"], 0) + 1
            if len(citations) >= effective_k:
                break

        evidence_confidence = self._evidence_confidence(
            citations, query_terms, effective_topics)
        return RetrievalOutcome(
            citations=citations,
            evidence_confidence=evidence_confidence,
            candidate_count=len(ranked_candidates),
        )

    @staticmethod
    def _evidence_confidence(
        citations: list[Citation],
        query_terms: list[str],
        topics: list[str],
    ) -> float:
        if not citations:
            return 0.0

        average_score = sum(
            citation.retrieval_score for citation in citations) / len(citations)
        matched_terms = {
            term for citation in citations for term in citation.matched_terms}
        coverage = len(matched_terms) / max(1, len(set(query_terms)))
        multi_citation_bonus = min(0.12, max(0, len(citations) - 1) * 0.04)
        matched_topics = {
            topic for citation in citations for topic in citation.matched_topics}
        topic_coverage = len(matched_topics) / \
            max(1, len(set(topics))) if topics else 0.0

        return min(
            1.0,
            average_score * 0.66 + coverage * 0.2 +
            topic_coverage * 0.08 + multi_citation_bonus,
        )

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

    @staticmethod
    def list_topic_stats(jurisdiction: str, source_types: list[str] | None = None) -> list[dict]:
        sql_parts = [
            """
            SELECT topic.value AS topic, COUNT(*)::int AS chunk_count
            FROM kb_chunks c
            JOIN kb_sources s ON s.id = c.source_id
            CROSS JOIN LATERAL jsonb_array_elements_text(COALESCE(c.metadata->'topics', '[]'::jsonb)) AS topic(value)
            WHERE s.jurisdiction = %s
            """
        ]
        params: list = [jurisdiction]

        if source_types:
            sql_parts.append("AND s.source_type = ANY(%s)")
            params.append(source_types)

        sql_parts.append(
            "GROUP BY topic.value ORDER BY chunk_count DESC, topic.value ASC")
        sql = "\n".join(sql_parts)

        rows: list[dict] = []
        for conn in get_db_connection():
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        return rows

    @staticmethod
    def list_source_type_stats(jurisdiction: str) -> list[dict]:
        sql = """
            SELECT s.source_type, COUNT(*)::int AS source_count
            FROM kb_sources s
            WHERE s.jurisdiction = %s
            GROUP BY s.source_type
            ORDER BY source_count DESC, s.source_type ASC
        """
        rows: list[dict] = []
        for conn in get_db_connection():
            with conn.cursor() as cur:
                cur.execute(sql, (jurisdiction,))
                rows = cur.fetchall()
        return rows
