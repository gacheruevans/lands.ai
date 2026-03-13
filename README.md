# lands.ai

Kenya Land Search & Property Legal AI Agent.

- Backend: Python + FastAPI
- Frontend: Next.js + TailwindCSS
- AI Layer: LLM API (Gemini / OpenAI / Claude)
- Data Layer: PostgreSQL + pgvector
- Knowledge Sources: Kenyan land law, eCitizen procedures, county building permits, property rates, stamp duty, land registry rules

## Architecture Decision

For MVP and early scale, lands.ai adopts a **modular monolith** architecture.

Why this approach:
- Faster to ship and iterate
- Lower infrastructure and operations complexity
- Easier legal traceability and auditability
- Better debugging for RAG and citation quality

Microservices are deferred until objective scaling triggers are met.

## System Architecture (Current Target)

```text
User (Browser)
    │
    ▼
Next.js Frontend (TailwindCSS UI)
    │
    ▼
FastAPI Backend (Modular Monolith)
    ├── Query Orchestration
    ├── Retrieval / RAG Service
    ├── Legal Calculators (stamp duty, rates)
    ├── Knowledge Base Admin / Ingestion
    ├── Audit + Citation Logging
    ├── LLM Provider Adapter
    └── Async Jobs Interface
          │
          ├── PostgreSQL (source docs, metadata, audit events)
          ├── pgvector (embeddings + similarity search)
          ├── Redis (queue/cache)
          └── External APIs (LLM provider, eCitizen integrations)
```

## AI Pattern

RAG (Retrieval-Augmented Generation) is the core pattern.

This ensures:
- Answers are grounded in Kenyan legal and procedural sources
- Hallucination risk is reduced through retrieval + citations
- Knowledge can be updated without retraining a model

## Implementation Roadmap

### Phase 1 (Now)
- Build modular monolith structure
- Implement core query endpoint with citation-required responses
- Add ingestion pipeline for legal knowledge documents
- Persist audit trail for every legal answer

### Phase 2 (Growth)
- Introduce async workers for heavy ingestion/OCR tasks
- Add admin workflows for curated legal updates
- Add reliability patterns (retry, timeout, fallback provider)

### Phase 3 (Only if Triggered)
- Extract document-processing workload into separate service
- Consider regional deployment splits for compliance/data residency
- Split control-plane/admin services only when team and traffic justify

## Scaling Triggers (Service Extraction Gate)

Do **not** split into microservices unless one or more are true:
- Sustained workload where ingestion jobs degrade interactive query latency
- Team size and ownership boundaries require independent deploy units
- Regional regulatory requirements demand isolated runtime/data boundaries
- Traffic profile demonstrates clear independent scaling needs

See supporting docs:
- `docs/architecture.md`
- `docs/scaling-triggers.md`
- `docs/compliance-audit.md`

## Project Architecture

```text
lands.ai/
├── backend/                 # FastAPI modular monolith 
│   ├── src/lands_ai_backend/
│   │   ├── api/             # HTTP routes
│   │   ├── core/            # Settings/config
│   │   ├── schemas/         # Request/response contracts
│   │   └── services/        # Domain services
│   └── .env.example
├── frontend/                # Next.js + Tailwind
│   ├── app/                 # App router pages/layout
│   ├── lib/                 # API client
│   └── .env.example
└── docs/                    # Architecture and governance docs
```

## Quick Start

### Backend (FastAPI)

1. Create Python 3.11+ virtual environment.
2. Install backend dependencies from `backend/pyproject.toml`.
3. Copy `backend/.env.example` to `backend/.env` and set values.
4. Start backend app with `lands_ai_backend.main:app`.

Backend endpoints:
- Health: `/health`
- API docs: `/docs`
- Query endpoint: `/api/v1/query`

### Frontend (Next.js)

1. Install dependencies in `frontend/`.
2. Copy `frontend/.env.example` to `frontend/.env.local`.
3. Ensure `NEXT_PUBLIC_API_BASE_URL` points to backend.
4. Start frontend development server.

## RAG API (Implemented)

- `POST /api/v1/knowledge/ingest` to ingest source documents into pgvector-backed chunks
- `GET /api/v1/knowledge/topics` to discover available topic/source filters
- `POST /api/v1/query` to run retrieval + grounded answer generation
- `GET /api/v1/audit/events` to inspect persisted audit trails

The query flow now performs:
1. Embed question
2. Retrieve candidate chunks from Postgres + pgvector
3. Hybrid rerank using vector similarity + lexical query overlap + title relevance
4. Apply citation and evidence-confidence thresholds
5. Generate grounded answer only when evidence is strong enough (OpenAI-compatible provider when configured; deterministic fallback otherwise)
6. Persist audit event with citations and confidence

Quality upgrades now included:
- sentence/paragraph-aware semantic chunking during ingestion
- hybrid reranking for stronger relevance than raw vector search alone
- citation-level retrieval scores and matched query terms
- optional query-time metadata filters (`source_types`, `topics`)
- evidence confidence thresholds to suppress weak legal answers

## Dockerized Deployment (Isolated)

This repository includes `docker-compose.yml` for isolated local deployment with dedicated containers and network:
- `frontend` (Next.js)
- `backend` (FastAPI)
- `postgres` (`pgvector/pgvector` image)
- `redis` (reserved for async workloads)

Isolation design:
- Private compose network `lands_ai_net`
- Dedicated named volume `lands_ai_pgdata`
- Service names used internally (`postgres`, `backend`, `redis`) to avoid interference with other projects

## Container Quick Start

1. Ensure Docker Desktop is running.
2. (Optional) set provider keys in root `.env`.
3. Build and run compose stack.
4. Open frontend at `http://localhost:3000`.
5. Backend docs available at `http://localhost:8000/docs`.

## Notes

- Root `.env` has placeholders for shared local setup.
- If no provider API key is configured, fallback generation/embeddings are used for local development.