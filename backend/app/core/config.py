"""
Configuration Management
Loads and validates environment variables
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")
    tavily_api_key: Optional[str] = Field(None, env="TAVILY_API_KEY")

    # Application Config
    default_model_provider: str = Field("gemini", env="DEFAULT_MODEL_PROVIDER")
    environment: str = Field("development", env="ENVIRONMENT")

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

    # API Configuration
    cors_origins: list = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        case_sensitive = False


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
