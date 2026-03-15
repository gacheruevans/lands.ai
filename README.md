# lands.ai

Kenya land and property legal assistant with grounded retrieval, citations, and admin ingestion tools.

## What the system does today

`lands.ai` is a modular-monolith application with:

- **Backend:** FastAPI (`backend/`) for query orchestration, RAG retrieval, ingestion, calculators, and audit logging.
- **Frontend:** Next.js + Tailwind (`frontend/`) for end-user Q&A and admin operations.
- **Data:** PostgreSQL + `pgvector` for sources/chunks/embeddings and audit events.
- **AI provider adapter:** configurable OpenAI-compatible LLM/embedding providers with deterministic fallback behavior for local development.

## Core capabilities

### Legal Q&A with citations

- Accepts Kenya land/property legal questions.
- Enforces a **domain guardrail** (off-topic questions are declined with guidance).
- Retrieves relevant local evidence from knowledge chunks.
- Applies evidence confidence checks and citation thresholds.
- Generates response with:
    - answer text
    - citations and retrieval metadata
    - evidence confidence + final confidence
    - legal disclaimer
    - audit event ID and timestamp

### Fallback online research (optional)

When local evidence is weak and online fallback is enabled, the backend can:

1. Search online references (Wikipedia API by default)
2. Ingest relevant extracts as `web_reference`
3. Re-run retrieval on expanded local knowledge

Response payload includes:

- `online_research_used`
- `online_docs_ingested`

### Knowledge ingestion (admin)

- Ingests text documents.
- Ingests PDF uploads.
- Uses semantic chunking + topic extraction.
- Queues ingestion work via background tasks and returns immediate acknowledgment.

### Filtered retrieval

- Query supports filters by:
    - `source_types`
    - `topics`
- Frontend persists selected filters in URL params for shareable sessions.

### Legal calculators

- Stamp duty calculator (`urban`, `rural`, `agricultural` rates).
- Land rates estimator (county-based placeholder logic).

### Audit trail

- Persists each query/response event with confidence and citations.
- Admin UI can list recent events.

## API surface

Base API prefix: `/api/v1`

- `POST /query`
- `GET /suggestions`
- `GET /audit/events`
- `POST /knowledge/ingest`
- `POST /knowledge/ingest/file`
- `GET /knowledge/topics`
- `POST /calculators/stamp-duty`
- `POST /calculators/land-rates`

System endpoints:

- `GET /health`
- `GET /docs`

## Graceful error behavior

Backend now exposes a consistent error envelope for validation, service, and unexpected failures:

```json
{
    "error": {
        "code": "SOME_ERROR_CODE",
        "message": "Human-readable message",
        "details": {}
    }
}
```

Notes:

- Validation errors return `422` with structured `details`.
- Known service failures return route-specific codes (e.g., `QUERY_FAILED`, `TOPICS_FETCH_FAILED`).
- Unknown exceptions return `500` with a safe generic message.

## Architecture summary

Current style is **modular monolith** (single FastAPI runtime, modular service boundaries).

Why:

- Faster iteration for MVP/early scale
- Simpler deployment and debugging
- Stronger legal traceability and auditability

See deeper design docs:

- `docs/architecture.md`
- `docs/scaling-triggers.md`
- `docs/compliance-audit.md`

## Project structure

```text
lands.ai/
├── backend/
│   └── src/lands_ai_backend/
│       ├── api/
│       ├── core/
│       ├── schemas/
│       └── services/
├── frontend/
│   ├── app/
│   └── lib/
└── docs/
```

## Local run overview

### Backend

1. Create/activate Python environment.
2. Install dependencies from `backend/pyproject.toml`.
3. Configure `.env` values (database + provider settings).
4. Run FastAPI app (`lands_ai_backend.main:app`).

### Frontend

1. Install dependencies in `frontend/`.
2. Configure `NEXT_PUBLIC_API_BASE_URL`.
3. Run Next.js app.

## Testing

The project now includes automated tests for both backend and frontend.

### Backend tests (pytest)

From `backend/`:

1. Ensure your virtual environment is active.
2. Install backend package with test extras:
    - `python -m pip install -e '.[dev]'`
3. Run tests:
    - `python -m pytest -q`

What is covered:

- Unit tests for calculator logic and error payload formatting
- Integration tests for API routes (success + graceful failure envelopes)

### Frontend tests (Vitest + Testing Library)

From `frontend/`:

1. Install dependencies:
    - `npm install`
2. Run tests once:
    - `npm test`
3. Optional watch mode:
    - `npm run test:watch`

What is covered:

- Unit tests for API client request/response + error parsing behavior
- Integration tests for admin ingestion flow (success + graceful error display)

### Quick run from project root

If you prefer running from repo root:

- Backend: `cd backend && python -m pytest -q`
- Frontend: `cd frontend && npm test`

### Run tests with Docker (build + execute)

The Docker setup now includes dedicated **test build targets** and Compose test services:

- `backend-test` (uses `backend/Dockerfile` target `test`)
- `frontend-test` (uses `frontend/Dockerfile` target `test`)

From repo root:

- Run backend tests in Docker:
    - `docker compose --profile test run --rm backend-test`
- Run frontend tests in Docker:
    - `docker compose --profile test run --rm frontend-test`
- Run both test services via profile:
    - `docker compose --profile test up --build --abort-on-container-exit backend-test frontend-test`

Notes:

- Runtime app services still build with `runtime` targets.
- Test services are isolated behind Compose `test` profile and won’t start during normal `docker compose up`.

### Docker Compose

`docker-compose.yml` provisions:

- `frontend`
- `backend`
- `postgres` (`pgvector/pgvector`)
- `redis`

## Known boundaries

- Legal outputs are **informational guidance**, not legal advice.
- Land rates calculator is currently an estimate model (not county valuation-roll exact).
- Production hardening should include robust async workers for heavy ingestion and stricter operational controls.