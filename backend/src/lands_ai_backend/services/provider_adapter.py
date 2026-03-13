import hashlib
import random
from typing import Any

import httpx

from lands_ai_backend.core.config import settings
from lands_ai_backend.schemas.query import Citation


class ProviderAdapter:
    def __init__(self) -> None:
        self._api_key = settings.openai_api_key or settings.llm_api_key
        self._base_url = settings.llm_base_url.rstrip("/")
        self._chat_model = settings.chat_model
        self._embedding_model = settings.embedding_model

    def embed_text(self, text: str) -> list[float]:
        if self._api_key:
            return self._embed_with_openai(text)
        return self._fallback_embedding(text)

    def generate_answer(self, question: str, citations: list[Citation]) -> tuple[str, float]:
        if self._api_key:
            return self._chat_with_openai(question, citations)
        return self._fallback_answer(question, citations), 0.58

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
            f"[{c.source_id}::{c.chunk_id}] {c.snippet}" for c in citations
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a Kenya property legal assistant. Use only retrieved context. "
                    "If context is insufficient, say so explicitly."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Retrieved context:\n{context}\n\n"
                    "Answer in concise practical steps and avoid legal overclaims."
                ),
            },
        ]

        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={"model": self._chat_model, "messages": messages, "temperature": 0.2},
            timeout=45.0,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        answer: str = payload["choices"][0]["message"]["content"]
        return answer.strip(), 0.78

    def _fallback_embedding(self, text: str) -> list[float]:
        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
        rnd = random.Random(seed)
        return [rnd.uniform(-1.0, 1.0) for _ in range(settings.embedding_dimensions)]

    def _fallback_answer(self, question: str, citations: list[Citation]) -> str:
        if not citations:
            return (
                "I do not have sufficient grounded Kenyan legal sources to answer this reliably. "
                "Please provide more detail or consult a qualified advocate."
            )
        references = "; ".join(f"{c.title}" for c in citations[:3])
        return (
            f"Based on retrieved Kenyan guidance related to '{question}', begin with an official "
            f"title search, verify encumbrances, and confirm statutory fees and county requirements. "
            f"Key references used: {references}."
        )
