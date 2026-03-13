import hashlib
import math
from typing import Any

import httpx

from lands_ai_backend.core.config import settings
from lands_ai_backend.schemas.query import Citation
from lands_ai_backend.services.text_processing import tokenize_query_terms


class ProviderAdapter:
    def __init__(self) -> None:
        self._api_key = settings.openai_api_key or settings.llm_api_key
        self._base_url = settings.llm_base_url.rstrip("/")
        self._chat_model = settings.chat_model
        self._embedding_model = settings.embedding_model

    def embed_text(self, text: str) -> list[float]:
        if self._api_key:
            try:
                return self._embed_with_openai(text)
            except httpx.HTTPError:
                pass
        return self._fallback_embedding(text)

    def generate_answer(self, question: str, citations: list[Citation]) -> tuple[str, float]:
        if self._api_key:
            try:
                return self._chat_with_openai(question, citations)
            except httpx.HTTPError:
                pass
        fallback_confidence = min(0.76, 0.56 + len(citations) * 0.06)
        return self._fallback_answer(question, citations), fallback_confidence

    def _embed_with_openai(self, text: str) -> list[float]:
        response = httpx.post(
            f"{self._base_url}/embeddings",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._embedding_model, "input": text},
            timeout=30.0,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        embedding = payload["data"][0]["embedding"]
        if len(embedding) > settings.embedding_dimensions:
            return embedding[: settings.embedding_dimensions]
        if len(embedding) < settings.embedding_dimensions:
            return embedding + [0.0] * (settings.embedding_dimensions - len(embedding))
        return embedding

    def _chat_with_openai(self, question: str, citations: list[Citation]) -> tuple[str, float]:
        context = "\n\n".join(
            (
                f"[{c.source_id}::{c.chunk_id}] score={c.retrieval_score:.2f} "
                f"source_type={c.source_type} "
                f"matched_terms={','.join(c.matched_terms) or 'none'} "
                f"matched_topics={','.join(c.matched_topics) or 'none'} :: {c.snippet}"
            )
            for c in citations
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a Kenya property legal assistant. Use only the retrieved context. "
                    "Do not invent procedures, fees, timelines, or agencies. "
                    "If the context is incomplete, explicitly say the evidence is insufficient. "
                    "Prefer concise practical steps and mention uncertainty where appropriate."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Retrieved context:\n{context}\n\n"
                    "Answer in concise practical steps. Base each step only on the retrieved context. "
                    "Do not cite laws that are not in the context."
                ),
            },
        ]

        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._chat_model,
                  "messages": messages, "temperature": 0.2},
            timeout=45.0,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        answer: str = payload["choices"][0]["message"]["content"]
        confidence = min(0.86, 0.64 + len(citations) * 0.04)
        return answer.strip(), confidence

    def _fallback_embedding(self, text: str) -> list[float]:
        dimensions = settings.embedding_dimensions
        vector = [0.0] * dimensions
        tokens = tokenize_query_terms(text)

        if not tokens:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            for index, byte in enumerate(digest):
                vector[index % dimensions] += byte / 255.0
        else:
            for token in tokens:
                token_hash = hashlib.sha256(token.encode("utf-8")).digest()
                primary_index = int.from_bytes(
                    token_hash[:4], "big") % dimensions
                secondary_index = int.from_bytes(
                    token_hash[4:8], "big") % dimensions
                sign = 1.0 if token_hash[8] % 2 == 0 else -1.0
                weight = 1.0 + min(len(token), 12) / 12.0
                vector[primary_index] += weight
                vector[secondary_index] += sign * weight * 0.35

        norm = math.sqrt(sum(component * component for component in vector))
        if norm == 0:
            return vector
        return [component / norm for component in vector]

    def _fallback_answer(self, question: str, citations: list[Citation]) -> str:
        if not citations:
            return (
                "I do not have sufficient grounded Kenyan legal sources to answer this reliably. "
                "Please provide more detail or consult a qualified advocate."
            )
        references = "; ".join(f"{c.title}" for c in citations[:3])
        matched_terms = sorted(
            {term for citation in citations for term in citation.matched_terms})
        term_text = f" Relevant issues found: {', '.join(matched_terms)}." if matched_terms else ""
        return (
            f"Based on retrieved Kenyan guidance related to '{question}', begin with an official "
            f"title search, verify encumbrances, and confirm statutory fees and county requirements. "
            f"Key references used: {references}.{term_text}"
        )
