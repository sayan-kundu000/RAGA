"""Application settings and configuration management."""

import os
from functools import lru_cache
from typing import Optional, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for RAGA agent pipeline."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    COHERE_API_KEY: Optional[str] = os.getenv("COHERE_API_KEY", "")

    # Vector DB
    QDRANT_URL: str = os.getenv("QDRANT_URL", ":memory:")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    COLLECTION_NAME: str = "raga_child_chunks"

    # Chunking & Parent-Child Mapping
    PARENT_CHUNK_SIZE: int = int(os.getenv("PARENT_CHUNK_SIZE", 1000))
    PARENT_CHUNK_OVERLAP: int = int(os.getenv("PARENT_CHUNK_OVERLAP", 100))
    CHILD_CHUNK_SIZE: int = int(os.getenv("CHILD_CHUNK_SIZE", 200))
    CHILD_CHUNK_OVERLAP: int = int(os.getenv("CHILD_CHUNK_OVERLAP", 50))

    # Hybrid Search & RRF Parameters
    HYBRID_RETRIEVAL_CANDIDATES: int = int(os.getenv("HYBRID_RETRIEVAL_CANDIDATES", 20))
    RRF_K: int = int(os.getenv("RRF_K", 60))

    # Cohere ReRank Context Compression
    RERANK_MODEL: str = os.getenv("RERANK_MODEL", "rerank-english-v3.0")
    RERANK_TOP_N: int = int(os.getenv("RERANK_TOP_N", 5))
    RERANK_SCORE_THRESHOLD: float = float(os.getenv("RERANK_SCORE_THRESHOLD", 0.3))

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on", "debug")
        return False


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached application settings singleton."""
    return Settings()
