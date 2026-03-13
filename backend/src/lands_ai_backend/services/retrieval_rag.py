from psycopg.types.json import Json

from lands_ai_backend.core.db import get_db_connection
from lands_ai_backend.schemas.query import Citation
from lands_ai_backend.services.provider_adapter import ProviderAdapter


class RetrievalRagService:
    def __init__(self, provider: ProviderAdapter | None = None) -> None:
        self.provider = provider or ProviderAdapter()

    def retrieve(self, question: str, jurisdiction: str, k: int = 4) -> list[Citation]:
        query_embedding = self.provider.embed_text(question)
        vector_literal = self._vector_literal(query_embedding)

        sql = """
            SELECT c.id AS chunk_id, c.source_id, c.title, c.content
            FROM kb_chunks c
            JOIN kb_sources s ON s.id = c.source_id
            WHERE s.jurisdiction = %s
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
        """

        citations: list[Citation] = []
        for conn in get_db_connection():
            with conn.cursor() as cur:
                cur.execute(sql, (jurisdiction, vector_literal, k))
                rows = cur.fetchall()

        for row in rows:
            citations.append(
                Citation(
                    source_id=row["source_id"],
                    chunk_id=row["chunk_id"],
                    title=row["title"],
                    snippet=row["content"][:280],
                )
            )
        return citations

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
