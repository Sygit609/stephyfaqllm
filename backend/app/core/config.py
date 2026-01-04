"""
Configuration Management
Loads and validates environment variables
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Keys
    openai_api_key: str
    google_api_key: str
    supabase_url: str
    supabase_key: str
    tavily_api_key: Optional[str] = None

    # Application Config
    default_model_provider: str = "gemini"
    environment: str = "development"

    # Model Specifications
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dims: int = 1536
    openai_generation_model: str = "gpt-4o"

    gemini_embedding_model: str = "models/text-embedding-004"
    gemini_embedding_dims: int = 768
    gemini_generation_model: str = "gemini-2.0-flash-exp"

    # Cost per 1K tokens (USD)
    openai_input_cost: float = 0.0025  # gpt-4o
    openai_output_cost: float = 0.01  # gpt-4o
    openai_embedding_cost: float = 0.00002  # text-embedding-3-small

    # Search Configuration
    hybrid_search_vector_weight: float = 0.7
    hybrid_search_fulltext_weight: float = 0.3
    web_search_threshold: float = 0.7  # Use web search if best score < this
    default_search_limit: int = 5
    vector_search_batch_limit: int = 100  # Max results per vector search
    ivfflat_probes: int = 10  # IVFFlat accuracy tuning (1-100, higher = more accurate)
    enable_llm_reranking: bool = True

    # API Configuration - CORS origins from env or defaults
    cors_origins: list = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:8000"]


# Global settings instance
settings = Settings()


def validate_api_keys() -> dict:
    """
    Validate that all required API keys are present
    Returns dict with validation status
    """
    validation = {
        "openai": bool(settings.openai_api_key and len(settings.openai_api_key) > 20),
        "google": bool(settings.google_api_key and len(settings.google_api_key) > 20),
        "supabase": bool(settings.supabase_url and settings.supabase_key),
        "tavily": bool(settings.tavily_api_key and len(settings.tavily_api_key) > 10)
        if settings.tavily_api_key
        else False,
    }
    return validation
