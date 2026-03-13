from typing import Any

import httpx

from lands_ai_backend.core.config import settings
from lands_ai_backend.schemas.knowledge import IngestDocumentRequest
from lands_ai_backend.services.knowledge_ingestion import KnowledgeIngestionService
from lands_ai_backend.services.text_processing import extract_topics, normalize_text


class OnlineResearchService:
    """Online fallback research for sparse-knowledge queries.

    Current provider: Wikipedia API (no API key required).
    Retrieved pages are ingested into Postgres for future retrieval cycles.
    """

    def __init__(self, ingestion_service: KnowledgeIngestionService | None = None) -> None:
        self.ingestion = ingestion_service or KnowledgeIngestionService()
        self.timeout = settings.online_research_timeout_seconds
        self.headers = {"User-Agent": settings.online_research_user_agent}

    def search_and_ingest(self, question: str, jurisdiction: str) -> int:
        if not settings.enable_online_research:
            return 0

        page_candidates = self._search_wikipedia(
            question, settings.online_research_max_docs)
        ingested_count = 0

        for page in page_candidates:
            page_id = str(page.get("pageid", "")).strip()
            title = str(page.get("title", "")).strip()
            if not page_id or not title:
                continue

            extract = self._fetch_wikipedia_extract(page_id)
            cleaned = normalize_text(extract)
            if len(cleaned) < settings.online_research_min_chars:
                continue

            source_id = f"web:wikipedia:{page_id}"
            topics = extract_topics(cleaned, title)
            payload = IngestDocumentRequest(
                source_id=source_id,
                title=title,
                text=cleaned,
                jurisdiction=jurisdiction,
                source_type="web_reference",
                topics=topics,
            )
            self.ingestion.ingest(payload)
            ingested_count += 1

        return ingested_count

    def _search_wikipedia(self, question: str, limit: int) -> list[dict[str, Any]]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{question} Kenya land law property",
            "utf8": 1,
            "format": "json",
            "srlimit": max(1, min(limit, 10)),
        }
        try:
            response = httpx.get(
                settings.online_research_search_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return payload.get("query", {}).get("search", [])
        except httpx.HTTPError:
            return []

    def _fetch_wikipedia_extract(self, page_id: str) -> str:
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": 1,
            "exintro": 1,
            "exlimit": 1,
            "pageids": page_id,
            "format": "json",
        }
        try:
            response = httpx.get(
                settings.online_research_extract_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            pages = payload.get("query", {}).get("pages", {})
            page = pages.get(page_id) or next(iter(pages.values()), {})
            return str(page.get("extract", ""))
        except httpx.HTTPError:
            return ""
