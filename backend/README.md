# lands.ai backend

FastAPI modular monolith application.

## Run (development)

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies from `pyproject.toml`.
3. Copy `.env.example` to `.env` and set values.
4. Start server using module path `lands_ai_backend.main:app`.

Health endpoint: `/health`
API docs: `/docs`

## RAG Endpoints

- `POST /api/v1/knowledge/ingest`
- `POST /api/v1/query`
- `GET /api/v1/audit/events`

Database initialization (including pgvector extension + tables) runs on app startup.

## Docker

From project root, use the compose stack to run backend with Postgres/pgvector:
- backend exposed on `http://localhost:8000`
