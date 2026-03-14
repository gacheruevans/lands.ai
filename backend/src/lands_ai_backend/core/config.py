from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "lands.ai backend"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    default_llm_provider: str = "openai-compatible"
    llm_api_key: str = ""
    openai_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    chat_model: str = "gpt-4o-mini"

    # Embedding can use a different provider/key than chat (e.g. OpenAI embeddings + Groq chat)
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    embedding_base_url: str = ""  # defaults to llm_base_url when empty
    embedding_api_key: str = ""   # defaults to llm_api_key when empty

    retrieval_top_k: int = 4
    retrieval_candidate_pool: int = 12
    min_citation_score: float = 0.48
    min_answer_confidence: float = 0.60
    min_citations_required: int = 1

    chunk_target_chars: int = 850
    chunk_max_chars: int = 1100
    chunk_overlap_sentences: int = 1

    enable_online_research: bool = True
    online_research_max_docs: int = 3
    online_research_min_chars: int = 180
    online_research_timeout_seconds: float = 15.0
    online_research_min_relevance_score: float = 0.28
    online_research_query_suffix: str = "Kenya land property"
    online_research_search_url: str = "https://en.wikipedia.org/w/api.php"
    online_research_extract_url: str = "https://en.wikipedia.org/w/api.php"
    online_research_user_agent: str = "lands.ai/0.1 (research assistant; contact: dev@lands.ai)"

    database_url: str = "postgresql://postgres:postgres@localhost:5432/lands_ai"
    redis_url: str = "redis://localhost:6379/0"
    cors_allowed_origins: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
