import re
from collections.abc import Iterable

STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'before', 'by', 'for', 'from',
    'how', 'i', 'in', 'into', 'is', 'it', 'of', 'on', 'or', 'should', 'that',
    'the', 'their', 'this', 'to', 'what', 'when', 'where', 'which', 'with', 'you',
}

TOPIC_KEYWORDS: dict[str, set[str]] = {
    "title-search": {"title search", "official search", "encumbrance", "caution", "restriction"},
    "ownership": {"owner", "ownership", "proprietor", "certificate of title", "title deed"},
    "stamp-duty": {"stamp duty", "duty", "valuation", "rate of duty"},
    "registration": {"registration", "transfer", "land registry", "register", "instrument"},
    "leasehold": {"leasehold", "ground rent", "unexpired term", "lease"},
    "county-rates": {"county", "rates", "land rates", "approvals", "change of use"},
    "land-control-board": {"land control board", "lcb", "consent"},
    "dispute-risk": {"dispute", "caveat", "fraud", "inconsistent", "conflict"},
    "foreign-ownership": {"foreigners", "foreigner", "non-citizen", "non citizen", "alien", "foreign ownership"},
    "land-tenure": {"tenure", "freehold", "leasehold", "usufruct", "land rights"},
}


def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def split_sentences(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', cleaned)
    return [normalize_text(part) for part in parts if normalize_text(part)]


def tokenize_query_terms(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9'-]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 2]


def semantic_chunk_text(
    text: str,
    target_chars: int = 850,
    max_chars: int = 1100,
    overlap_sentences: int = 1,
) -> list[str]:
    paragraphs = [normalize_text(part) for part in re.split(
        r'\n\s*\n', text) if normalize_text(part)]
    if not paragraphs:
        normalized = normalize_text(text)
        return [normalized] if normalized else []

    chunks: list[str] = []
    buffer: list[str] = []

    for paragraph in paragraphs:
        sentences = split_sentences(paragraph) or [paragraph]
        for sentence in sentences:
            tentative = ' '.join(buffer + [sentence]).strip()
            if buffer and len(tentative) > max_chars:
                chunks.append(' '.join(buffer).strip())
                overlap = buffer[-overlap_sentences:] if overlap_sentences > 0 else []
                buffer = [*overlap, sentence]
                continue

            buffer.append(sentence)
            if len(' '.join(buffer)) >= target_chars:
                chunks.append(' '.join(buffer).strip())
                overlap = buffer[-overlap_sentences:] if overlap_sentences > 0 else []
                buffer = overlap.copy()

    if buffer:
        final_chunk = ' '.join(buffer).strip()
        if not chunks or final_chunk != chunks[-1]:
            chunks.append(final_chunk)

    return [chunk for chunk in chunks if chunk]


def keyword_overlap_terms(text: str, query_terms: Iterable[str]) -> list[str]:
    haystack = normalize_text(text).lower()
    return [term for term in dict.fromkeys(query_terms) if term in haystack]


def keyword_overlap_score(text: str, query_terms: list[str]) -> tuple[float, list[str]]:
    if not query_terms:
        return 0.0, []
    matches = keyword_overlap_terms(text, query_terms)
    return len(matches) / len(set(query_terms)), matches


def title_relevance_bonus(title: str, query_terms: list[str]) -> float:
    if not query_terms:
        return 0.0
    matches = keyword_overlap_terms(title, query_terms)
    return min(0.12, len(matches) * 0.04)


def best_snippet(text: str, query_terms: list[str], max_chars: int = 280) -> str:
    normalized = normalize_text(text)
    if len(normalized) <= max_chars:
        return normalized

    lowered = normalized.lower()
    best_index = 0
    for term in query_terms:
        found = lowered.find(term.lower())
        if found != -1:
            best_index = found
            break

    start = max(0, best_index - max_chars // 4)
    end = min(len(normalized), start + max_chars)
    snippet = normalized[start:end].strip()
    if start > 0:
        snippet = f"…{snippet}"
    if end < len(normalized):
        snippet = f"{snippet}…"
    return snippet


def extract_topics(text: str, title: str | None = None) -> list[str]:
    corpus = normalize_text(f"{title or ''} {text}").lower()
    found: list[str] = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in corpus for keyword in keywords):
            found.append(topic)

    if not found:
        terms = tokenize_query_terms(corpus)
        if "leasehold" in terms:
            found.append("leasehold")
        if "registry" in terms or "registration" in terms:
            found.append("registration")
        if "duty" in terms:
            found.append("stamp-duty")
        if "foreigner" in terms or "foreigners" in terms or "alien" in terms:
            found.append("foreign-ownership")

    return found
