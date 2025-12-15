"""
Pydantic Models for API Request/Response Schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


# ============================================================
# Search Models
# ============================================================


class SearchRequest(BaseModel):
    """Request to search the knowledge base"""

    query: str = Field(..., description="The search query text")
    provider: Optional[str] = Field(
        "gemini", description="Model provider: 'gemini' or 'openai'"
    )
    limit: Optional[int] = Field(5, description="Maximum number of results")


class SourceMatch(BaseModel):
    """A single matched source from the knowledge base"""

    id: str
    question: str
    answer: str
    category: Optional[str] = None
    tags: List[str] = []
    date: Optional[str] = None
    source_url: Optional[str] = None
    score: float = Field(..., description="Relevance score (0-1)")
    match_type: str = Field(..., description="'vector', 'fulltext', or 'hybrid'")


class SearchResponse(BaseModel):
    """Response from search endpoint"""

    query: str
    sources: List[SourceMatch]
    total_found: int
    provider: str
    intent: Optional[str] = None  # internal/external/both
    recency_required: bool = False


# ============================================================
# Answer Generation Models
# ============================================================


class AnswerRequest(BaseModel):
    """Request to generate an answer from sources"""

    query: str
    sources: List[Dict[str, Any]] = Field(
        ..., description="Matched sources to use for generation"
    )
    provider: Optional[str] = Field("gemini", description="Model provider")


class AnswerResponse(BaseModel):
    """Response with generated answer"""

    query: str
    answer: str
    sources_used: List[SourceMatch]
    provider: str
    metadata: Dict[str, Any] = Field(
        ...,
        description="Metadata: tokens, cost, latency, model",
    )


# ============================================================
# Combined Query Model (Search + Generation)
# ============================================================


class QueryRequest(BaseModel):
    """Combined request for search + answer generation"""

    query: str = Field(..., description="The user's question")
    provider: Optional[str] = Field(
        "gemini", description="Model provider: 'gemini' or 'openai'"
    )
    search_limit: Optional[int] = Field(5, description="Number of sources to find")
    use_web_search: Optional[bool] = Field(
        True, description="Allow web search if needed"
    )


class QueryResponse(BaseModel):
    """Complete response with search results and generated answer"""

    query: str
    answer: str
    sources: List[SourceMatch]
    web_search_used: bool = False
    web_results: Optional[List[Dict[str, Any]]] = None
    intent: str  # internal/external/both
    recency_required: bool
    provider: str
    metadata: Dict[str, Any]  # tokens, cost, latency
    query_id: str  # For feedback tracking


# ============================================================
# Feedback Models
# ============================================================


class FeedbackRequest(BaseModel):
    """Staff feedback on a generated answer"""

    query_id: str = Field(..., description="UUID of the query from query_logs")
    rating: Optional[int] = Field(
        None, ge=1, le=5, description="Staff rating (1-5 stars)"
    )
    was_edited: bool = Field(False, description="Did staff edit the answer?")
    staff_notes: Optional[str] = Field(None, description="Optional feedback notes")


class FeedbackResponse(BaseModel):
    """Confirmation of feedback submission"""

    success: bool
    query_id: str
    message: str


# ============================================================
# Metrics Models
# ============================================================


class ModelMetrics(BaseModel):
    """Metrics for a single model provider"""

    provider: str
    total_queries: int
    avg_latency_ms: Optional[int] = None
    total_cost_usd: Optional[float] = None
    avg_cost_per_query: Optional[float] = None
    avg_rating: Optional[float] = None
    edit_rate: Optional[float] = None
    web_searches: int


class MetricsResponse(BaseModel):
    """Model comparison metrics"""

    period_days: int
    models: List[ModelMetrics]
    total_queries: int


class QueryLogEntry(BaseModel):
    """A single entry from query history"""

    id: str
    query_text: str
    model_provider: str
    intent_type: Optional[str] = None
    latency_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    staff_rating: Optional[int] = None
    was_edited: bool
    created_at: datetime


class RecentQueriesResponse(BaseModel):
    """Recent query history"""

    queries: List[QueryLogEntry]
    total: int


# ============================================================
# Health Check Model
# ============================================================


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    database_connected: bool
    api_keys_valid: Dict[str, bool]
    environment: str
