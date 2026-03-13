from lands_ai_backend.schemas.knowledge import (
    KnowledgeTopicsResponse,
    SourceTypeStat,
    TopicStat,
)
from lands_ai_backend.services.retrieval_rag import KnowledgeIngestionRepository


class KnowledgeCatalogService:
    def get_topics(
        self,
        jurisdiction: str,
        source_types: list[str] | None = None,
    ) -> KnowledgeTopicsResponse:
        topic_rows = KnowledgeIngestionRepository.list_topic_stats(
            jurisdiction=jurisdiction,
            source_types=source_types,
        )
        source_type_rows = KnowledgeIngestionRepository.list_source_type_stats(
            jurisdiction=jurisdiction,
        )

        return KnowledgeTopicsResponse(
            jurisdiction=jurisdiction,
            topics=[
                TopicStat(topic=row["topic"], chunk_count=int(row["chunk_count"]))
                for row in topic_rows
            ],
            source_types=[
                SourceTypeStat(
                    source_type=row["source_type"],
                    source_count=int(row["source_count"]),
                )
                for row in source_type_rows
            ],
        )
