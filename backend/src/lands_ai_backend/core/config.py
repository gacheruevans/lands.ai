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
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    retrieval_top_k: int = 4
    retrieval_candidate_pool: int = 12
    min_citation_score: float = 0.48
    min_answer_confidence: float = 0.60
    min_citations_required: int = 1

    chunk_target_chars: int = 850
    chunk_max_chars: int = 1100
    chunk_overlap_sentences: int = 1

    database_url: str = "postgresql://postgres:postgres@localhost:5432/lands_ai"
    redis_url: str = "redis://localhost:6379/0"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
