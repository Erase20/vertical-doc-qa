from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Vertical Document QA"
    app_env: str = "development"
    app_api_key: str = ""
    app_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    demo_mode: bool = False

    database_url: str = "postgresql+asyncpg://docqa:docqa@localhost:5432/docqa"
    redis_url: str = "redis://localhost:6379/0"
    upload_dir: Path = Path("./data/uploads")
    max_upload_mb: int = Field(default=50, ge=1, le=1024)

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = Field(default=1536, ge=1)
    embedding_batch_size: int = Field(default=25, ge=1, le=256)

    retrieval_top_k: int = Field(default=5, ge=1, le=50)
    retrieval_min_similarity: float = Field(default=0.25, ge=-1.0, le=1.0)
    chunk_target_tokens: int = Field(default=500, ge=50)
    chunk_max_tokens: int = Field(default=800, ge=100)
    chunk_overlap_tokens: int = Field(default=80, ge=0)

    vector_store: Literal["pgvector", "chroma"] = "pgvector"
    chroma_url: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.app_cors_origins.split(",") if item.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
