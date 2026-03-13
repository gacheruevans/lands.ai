from datetime import datetime, timezone

from lands_ai_backend.schemas.knowledge import (
    IngestDocumentRequest,
    IngestDocumentResponse,
)
from lands_ai_backend.services.provider_adapter import ProviderAdapter
from lands_ai_backend.services.retrieval_rag import KnowledgeIngestionRepository


class KnowledgeIngestionService:
    def __init__(self, provider: ProviderAdapter | None = None) -> None:
        self.provider = provider or ProviderAdapter()

    def ingest(self, payload: IngestDocumentRequest) -> IngestDocumentResponse:
        chunks = self._chunk_text(payload.text)
        upserts: list[dict[str, str | list[float] | dict[str, str]]] = []

        for index, chunk_content in enumerate(chunks, start=1):
            embedding = self.provider.embed_text(chunk_content)
            upserts.append(
                {
                    "id": f"{payload.source_id}:chunk:{index}",
                    "title": payload.title,
                    "content": chunk_content,
                    "metadata": {
                        "chunk_index": str(index),
                        "jurisdiction": payload.jurisdiction,
                        "source_type": payload.source_type,
                    },
                    "vector_literal": self._vector_literal(embedding),
                }
            )

        KnowledgeIngestionRepository.upsert_source(
            source_id=payload.source_id,
            title=payload.title,
            jurisdiction=payload.jurisdiction,
            source_type=payload.source_type,
        )
        KnowledgeIngestionRepository.replace_chunks(payload.source_id, upserts)

        return IngestDocumentResponse(
            source_id=payload.source_id,
            chunks_created=len(upserts),
            created_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _chunk_text(text: str, max_chars: int = 900, overlap: int = 150) -> list[str]:
        cleaned = " ".join(text.split())
        if len(cleaned) <= max_chars:
            return [cleaned]

        chunks: list[str] = []
        start = 0
        while start < len(cleaned):
            end = min(len(cleaned), start + max_chars)
            chunks.append(cleaned[start:end])
            if end == len(cleaned):
                break
            start = max(0, end - overlap)
        return chunks

    @staticmethod
    def _vector_literal(embedding: list[float]) -> str:
        return "[" + ",".join(f"{v:.8f}" for v in embedding) + "]"
