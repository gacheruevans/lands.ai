from datetime import datetime, timezone
import io
import logging
from pypdf import PdfReader

from lands_ai_backend.schemas.knowledge import (
    IngestDocumentRequest,
    IngestDocumentResponse,
)
from lands_ai_backend.core.config import settings
from lands_ai_backend.services.provider_adapter import ProviderAdapter
from lands_ai_backend.services.retrieval_rag import KnowledgeIngestionRepository
from lands_ai_backend.services.text_processing import extract_topics, semantic_chunk_text


logger = logging.getLogger(__name__)


class KnowledgeIngestionService:
    def __init__(self, provider: ProviderAdapter | None = None) -> None:
        self.provider = provider or ProviderAdapter()

    def ingest(self, payload: IngestDocumentRequest) -> IngestDocumentResponse:
        chunks = self._chunk_text(payload.text)
        resolved_topics = payload.topics or extract_topics(
            payload.text, payload.title)
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
                        "topics": resolved_topics,
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
            topics=resolved_topics,
            created_at=datetime.now(timezone.utc),
        )

    def ingest_file(
        self,
        file_content: bytes,
        source_id: str,
        title: str,
        jurisdiction: str = "KE",
        source_type: str = "law",
        topics: list[str] | None = None,
    ) -> IngestDocumentResponse:
        """
        Extracts text from a PDF file and ingests it.
        """
        try:
            reader = PdfReader(io.BytesIO(file_content))
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            
            if not text.strip():
                raise ValueError("Could not extract any text from the PDF")

            payload = IngestDocumentRequest(
                source_id=source_id,
                title=title,
                text=text,
                jurisdiction=jurisdiction,
                source_type=source_type,
                topics=topics or []
            )
            return self.ingest(payload)
        except Exception as e:
            logger.error(f"Failed to ingest PDF file {title}: {e}")
            raise

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
