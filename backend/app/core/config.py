"""
Configuration Management
Loads and validates environment variables
"""

import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables"""

    def __init__(self):
        # API Keys - read directly from os.environ
        self.openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
        self.google_api_key: str = os.environ.get("GOOGLE_API_KEY", "")
        self.supabase_url: str = os.environ.get("SUPABASE_URL", "")
        self.supabase_key: str = os.environ.get("SUPABASE_KEY", "")
        self.tavily_api_key: Optional[str] = os.environ.get("TAVILY_API_KEY")

        # Validate required keys
        missing = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.google_api_key:
            missing.append("GOOGLE_API_KEY")
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_key:
            missing.append("SUPABASE_KEY")

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Application Config
        self.default_model_provider: str = os.environ.get("DEFAULT_MODEL_PROVIDER", "gemini")
        self.environment: str = os.environ.get("ENVIRONMENT", "development")

        # Model Specifications
        self.openai_embedding_model: str = "text-embedding-3-small"
        self.openai_embedding_dims: int = 1536
        self.openai_generation_model: str = "gpt-4o"

        self.gemini_embedding_model: str = "models/text-embedding-004"
        self.gemini_embedding_dims: int = 768
        self.gemini_generation_model: str = "gemini-2.0-flash-exp"

        # Cost per 1K tokens (USD)
        self.openai_input_cost: float = 0.0025  # gpt-4o
        self.openai_output_cost: float = 0.01  # gpt-4o
        self.openai_embedding_cost: float = 0.00002  # text-embedding-3-small

        # Search Configuration
        self.hybrid_search_vector_weight: float = 0.7
        self.hybrid_search_fulltext_weight: float = 0.3
        self.web_search_threshold: float = 0.7  # Use web search if best score < this
        self.default_search_limit: int = 5
        self.vector_search_batch_limit: int = int(os.environ.get("VECTOR_SEARCH_BATCH_LIMIT", "100"))
        self.ivfflat_probes: int = int(os.environ.get("IVFFLAT_PROBES", "10"))
        self.enable_llm_reranking: bool = os.environ.get("ENABLE_LLM_RERANKING", "true").lower() == "true"

        # API Configuration - CORS origins from env or defaults
        cors_env = os.environ.get("CORS_ORIGINS", "")
        if cors_env:
            self.cors_origins: list = [x.strip() for x in cors_env.split(",")]
        else:
            self.cors_origins: list = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:8000"]


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
