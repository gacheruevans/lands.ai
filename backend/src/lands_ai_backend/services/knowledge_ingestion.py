from datetime import datetime, timezone

from lands_ai_backend.schemas.knowledge import (
    IngestDocumentRequest,
    IngestDocumentResponse,
)
from lands_ai_backend.core.config import settings
from lands_ai_backend.services.provider_adapter import ProviderAdapter
from lands_ai_backend.services.retrieval_rag import KnowledgeIngestionRepository
from lands_ai_backend.services.text_processing import semantic_chunk_text


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
                        "chunk_length": str(len(chunk_content)),
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
    def _chunk_text(text: str) -> list[str]:
        return semantic_chunk_text(
            text,
            target_chars=settings.chunk_target_chars,
            max_chars=settings.chunk_max_chars,
            overlap_sentences=settings.chunk_overlap_sentences,
        )

    @staticmethod
    def _vector_literal(embedding: list[float]) -> str:
        return "[" + ",".join(f"{v:.8f}" for v in embedding) + "]"
