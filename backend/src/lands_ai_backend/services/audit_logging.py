import uuid
from datetime import datetime, timezone

from psycopg.types.json import Json

from lands_ai_backend.core.db import get_db_connection
from lands_ai_backend.schemas.query import Citation


class AuditLoggingService:
    def log_event(
        self,
        question: str,
        jurisdiction: str,
        answer: str,
        citations: list[Citation],
        confidence: float,
    ) -> tuple[str, datetime]:
        event_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)

        sql = """
            INSERT INTO audit_events (id, question, jurisdiction, answer, citations, confidence, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        payload = [c.model_dump() for c in citations]

        for conn in get_db_connection():
            with conn.cursor() as cur:
                cur.execute(
                    sql,
                    (event_id, question, jurisdiction, answer,
                     Json(payload), confidence, created_at),
                )
            conn.commit()

        return event_id, created_at

    def list_events(self, limit: int = 50) -> list[dict]:
        sql = """
            SELECT id, question, jurisdiction, answer, citations, confidence, created_at
            FROM audit_events
            ORDER BY created_at DESC
            LIMIT %s
        """
        events: list[dict] = []
        for conn in get_db_connection():
            with conn.cursor() as cur:
                cur.execute(sql, (limit,))
                events = cur.fetchall()
        return events
