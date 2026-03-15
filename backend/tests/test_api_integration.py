from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI

from lands_ai_backend.api.v1.calculators import get_calculator_service
from lands_ai_backend.api.v1.knowledge import get_catalog_service, get_ingestion_service
from lands_ai_backend.api.v1.query import get_query_service
from lands_ai_backend.api.v1.audit import AuditLoggingService
from lands_ai_backend.api.v1.suggestions import SuggestionService
from lands_ai_backend.schemas.knowledge import KnowledgeTopicsResponse, SourceTypeStat, TopicStat
from lands_ai_backend.schemas.query import QueryResponse


def test_query_success_returns_response(client, app: FastAPI) -> None:
    class QueryServiceOk:
        def answer(self, _payload):
            return QueryResponse(
                answer="Use an advocate and perform title search.",
                citations=[],
                evidence_confidence=0.7,
                confidence=0.72,
                disclaimer="Informational guidance only.",
                audit_event_id="evt-123",
                created_at=datetime.now(timezone.utc),
            )

    app.dependency_overrides[get_query_service] = lambda: QueryServiceOk()

    response = client.post(
        "/api/v1/query",
        json={"question": "How do I transfer land in Kenya?", "jurisdiction": "KE"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("Use an advocate")
    assert body["confidence"] == 0.72


def test_query_service_failure_returns_graceful_error(client, app: FastAPI) -> None:
    class QueryServiceFail:
        def answer(self, _payload):
            raise RuntimeError("db offline")

    app.dependency_overrides[get_query_service] = lambda: QueryServiceFail()

    response = client.post(
        "/api/v1/query",
        json={"question": "How do I transfer land in Kenya?", "jurisdiction": "KE"},
    )

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "QUERY_FAILED"
    assert "Unable to process" in body["error"]["message"]


def test_query_validation_error_uses_standard_envelope(client) -> None:
    response = client.post("/api/v1/query", json={"question": "hi", "jurisdiction": "KE"})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(body["error"].get("details"), list)


def test_topics_success(client, app: FastAPI) -> None:
    class CatalogServiceOk:
        def get_topics(self, jurisdiction: str, source_types=None):
            assert jurisdiction == "KE"
            _ = source_types
            return KnowledgeTopicsResponse(
                jurisdiction="KE",
                topics=[TopicStat(topic="transfer", chunk_count=3)],
                source_types=[SourceTypeStat(source_type="law", source_count=1)],
            )

    app.dependency_overrides[get_catalog_service] = lambda: CatalogServiceOk()

    response = client.get("/api/v1/knowledge/topics?jurisdiction=KE")

    assert response.status_code == 200
    body = response.json()
    assert body["topics"][0]["topic"] == "transfer"


def test_topics_service_failure_returns_graceful_error(client, app: FastAPI) -> None:
    class CatalogServiceFail:
        def get_topics(self, jurisdiction: str, source_types=None):
            raise RuntimeError("catalog unavailable")

    app.dependency_overrides[get_catalog_service] = lambda: CatalogServiceFail()

    response = client.get("/api/v1/knowledge/topics?jurisdiction=KE")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "TOPICS_FETCH_FAILED"


def test_ingest_file_invalid_topics_json(client, app: FastAPI) -> None:
    class IngestionServiceNoop:
        def ingest_file(self, *_args, **_kwargs):
            return None

    app.dependency_overrides[get_ingestion_service] = lambda: IngestionServiceNoop()

    response = client.post(
        "/api/v1/knowledge/ingest/file",
        data={
            "source_id": "ke:source:1",
            "title": "Land Registration Act",
            "jurisdiction": "KE",
            "source_type": "law",
            "topics_json": "not-json",
        },
        files={"file": ("sample.pdf", b"%PDF-1.4 test", "application/pdf")},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "INVALID_TOPICS_JSON"


def test_calculators_failure_returns_graceful_error(client, app: FastAPI) -> None:
    class CalculatorServiceFail:
        def calculate_stamp_duty(self, payload):
            _ = payload
            raise RuntimeError("calculator down")

        def calculate_land_rates(self, payload):
            _ = payload
            raise RuntimeError("calculator down")

    app.dependency_overrides[get_calculator_service] = lambda: CalculatorServiceFail()

    response = client.post(
        "/api/v1/calculators/stamp-duty",
        json={"property_value": 100000, "property_type": "urban"},
    )

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "STAMP_DUTY_CALCULATION_FAILED"


def test_suggestions_success(client) -> None:
    response = client.get("/api/v1/suggestions")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["suggestions"], list)
    assert len(body["suggestions"]) > 0


def test_suggestions_failure_returns_graceful_error(client, monkeypatch) -> None:
    monkeypatch.setattr(SuggestionService, "get_suggestions", staticmethod(lambda: (_ for _ in ()).throw(RuntimeError("down"))))

    response = client.get("/api/v1/suggestions")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "SUGGESTIONS_FETCH_FAILED"


def test_audit_failure_returns_graceful_error(client, monkeypatch) -> None:
    def _boom(self, limit: int = 50):
        _ = limit
        raise RuntimeError("audit db unavailable")

    monkeypatch.setattr(AuditLoggingService, "list_events", _boom)

    response = client.get("/api/v1/audit/events?limit=10")

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "AUDIT_EVENTS_FETCH_FAILED"
