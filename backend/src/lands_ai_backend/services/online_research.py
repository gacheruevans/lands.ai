from typing import Any
import re

import httpx

from lands_ai_backend.core.config import settings
from lands_ai_backend.schemas.knowledge import IngestDocumentRequest
from lands_ai_backend.services.knowledge_ingestion import KnowledgeIngestionService
from lands_ai_backend.services.text_processing import (
    extract_topics,
    normalize_text,
    tokenize_query_terms,
)


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
            question,
            settings.online_research_max_docs * 3,
        )
        question_terms = tokenize_query_terms(question)
        ingested_count = 0
        threshold = max(0.05, settings.online_research_min_relevance_score)

        for page in page_candidates:
            page_id = str(page.get("pageid", "")).strip()
            title = str(page.get("title", "")).strip()
            if not page_id or not title:
                continue

            snippet = self._strip_html(str(page.get("snippet", "")))
            if self._relevance_score(f"{title} {snippet}", question_terms) < threshold:
                continue

            extract = self._fetch_wikipedia_extract(page_id)
            cleaned = normalize_text(extract)
            if len(cleaned) < settings.online_research_min_chars:
                continue

            if self._relevance_score(f"{title} {cleaned}", question_terms) < threshold:
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

            if ingested_count >= settings.online_research_max_docs:
                break

        if ingested_count == 0:
            ingested_count += self._ingest_curated_fallback(
                question, jurisdiction)

        return ingested_count

    def _search_wikipedia(self, question: str, limit: int) -> list[dict[str, Any]]:
        query_text = f"{question} {settings.online_research_query_suffix}".strip()
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query_text,
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
            "exlimit": 1,
            "exchars": 3500,
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

    @staticmethod
    def _strip_html(text: str) -> str:
        return re.sub(r"<[^>]+>", " ", text)

    @staticmethod
    def _relevance_score(text: str, question_terms: list[str]) -> float:
        haystack = normalize_text(text).lower()
        if not haystack:
            return 0.0

        question_hits = 0
        for term in set(question_terms):
            if term in haystack:
                question_hits += 1

        domain_terms = {
            "kenya",
            "land",
            "property",
            "ownership",
            "title",
            "lease",
            "freehold",
            "foreign",
            "stamp",
            "duty",
            "transfer",
            "nairobi",
            "valuation",
        }
        domain_hits = sum(1 for term in domain_terms if term in haystack)

        question_score = question_hits / max(1, len(set(question_terms)))
        domain_score = domain_hits / len(domain_terms)
        
        # If we have a good question hit, we are likely on the right track even with lower domain coverage
        if question_score > 0.5:
             return min(1.0, question_score * 0.8 + domain_score * 0.2 + 0.1)
             
        return min(1.0, question_score * 0.75 + domain_score * 0.25)

    def _ingest_curated_fallback(self, question: str, jurisdiction: str) -> int:
        question_lower = normalize_text(question).lower()
        if jurisdiction.upper() != "KE":
            return 0

        if "stamp" not in question_lower or "duty" not in question_lower:
            return 0

        payload = IngestDocumentRequest(
            source_id="seed:ke:stamp-duty:urban-rural-guidance",
            title="Kenya property transfer guidance: stamp duty baseline rates",
            text=(
                "For Kenya property transfers, stamp duty is commonly charged as a percentage "
                "of the dutiable value after valuation. A commonly used baseline is 4% for urban "
                "property transfers (including Nairobi) and 2% for rural property transfers. "
                "The payable amount is calculated against the dutiable value confirmed during valuation, "
                "and can change based on exemptions, policy updates, or transaction type. "
                "Always verify current rates and process requirements through KRA/eCitizen and the lands registry "
                "before filing instruments for registration."
            ),
            jurisdiction="KE",
            source_type="procedure",
            topics=["stamp-duty", "registration", "county-rates"],
        )
        self.ingestion.ingest(payload)
        return 1
