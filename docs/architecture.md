# lands.ai Architecture (MVP to Early Scale)

## Goal
Deliver a legally grounded Kenya property assistant with high accuracy, citation traceability, and low operational complexity.

## Chosen Style: Modular Monolith

A single FastAPI runtime hosts clearly separated modules:

1. `query_orchestration`
   - Accept user query
   - Route through retrieval and answer synthesis
   - Enforce response contract (answer + citations + disclaimer)

2. `retrieval_rag`
   - Embed query
   - Retrieve top-k legal/procedural chunks via pgvector
   - Return ranked evidence set

3. `legal_calculators`
   - Stamp duty calculations
   - Property rates helper logic

4. `knowledge_ingestion`
   - Import legal source documents
   - Chunk, normalize, tag by jurisdiction/topic
   - Generate and upsert embeddings

5. `audit_logging`
   - Record query, retrieved sources, model used, output hash, timestamps
   - Preserve immutable audit event records

6. `provider_adapter`
   - Unified interface for Gemini/OpenAI/Claude
   - Retry and timeout policy per provider

7. `jobs`
   - Background tasks for ingestion/OCR/scheduled refreshes
   - Queue via Redis-backed workers

## Request Flow

1. Frontend submits question to backend.
2. Backend retrieves relevant legal/procedural evidence.
3. LLM generates response constrained by evidence.
4. Backend validates citations and response schema.
5. Response returned with citations and legal-use disclaimer.
6. Audit event is persisted.

## Data Model Essentials

- `sources`: canonical documents and metadata
- `chunks`: chunked source text with provenance
- `embeddings`: vector representation references
- `citations`: mapping answer spans to source chunks
- `audit_events`: immutable record of each query/response cycle

## Engineering Rules

- Business/legal reasoning remains in backend only.
- Frontend is presentation and interaction only.
- Every substantive legal answer must include citations.
- If evidence is insufficient, return explicit uncertainty and escalation advice.
- Prefer internal module boundaries over network boundaries until scaling triggers fire.

## Extraction Readiness

Code should be written so each module can later be extracted with minimal refactor:
- clear interfaces
- no hidden cross-module side effects
- shared schemas/contracts defined once

See `docs/scaling-triggers.md` for extraction gates.