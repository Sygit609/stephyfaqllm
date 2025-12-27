"""
Pydantic Models for API Request/Response Schemas
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
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


# ============================================================
# Admin - Content Ingestion Models
# ============================================================


class ExtractScreenshotRequest(BaseModel):
    """Request to extract Q&A from screenshot"""

    image_data: str = Field(..., description="Base64-encoded image data")
    source_url: str = Field(..., description="Facebook post URL or source")
    provider: Optional[str] = Field(
        "gemini", description="Preferred model: 'gemini' or 'openai'"
    )
    use_fallback: Optional[bool] = Field(
        True, description="Use GPT-4 fallback if primary fails"
    )


class QAPair(BaseModel):
    """Single Q&A pair with metadata"""

    question: str
    answer: str
    tags: List[str] = []


class ExtractScreenshotResponse(BaseModel):
    """Response with extracted Q&A preview"""

    qa_pairs: List[QAPair]
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    model_used: str = Field(..., description="Model that performed extraction")
    used_fallback: bool = Field(False, description="Whether fallback was used")
    warnings: List[str] = []
    metadata: Dict[str, Any] = Field(
        ..., description="Extraction metadata: tokens, cost, latency"
    )


class SaveContentRequest(BaseModel):
    """Request to save extracted (and possibly edited) content"""

    qa_pairs: List[QAPair] = Field(..., description="Q&A pairs to save (user may have edited)")
    media_url: str = Field(..., description="URL to uploaded screenshot")
    source_url: str = Field(..., description="Facebook post URL")
    extracted_by: str = Field(..., description="Model used: gemini-vision or gpt4-vision")
    confidence: float = Field(..., ge=0.0, le=1.0)
    raw_extraction: Optional[Dict[str, Any]] = Field(
        None, description="Original extraction response"
    )
    content_type: Optional[str] = Field("screenshot", description="Content type")


class SaveContentResponse(BaseModel):
    """Response after saving content"""

    success: bool
    parent_id: str = Field(..., description="ID of parent screenshot entry")
    child_ids: List[str] = Field(..., description="IDs of saved Q&A entries")
    total_saved: int


class ContentListFilter(BaseModel):
    """Filters for content list"""

    content_type: Optional[str] = None
    extracted_by: Optional[str] = None
    min_confidence: Optional[float] = None
    has_parent: Optional[bool] = None
    parent_id: Optional[str] = None


class ContentItem(BaseModel):
    """Single content item"""

    id: str
    content_type: str
    question: str
    answer: str
    source_url: Optional[str] = None
    media_url: Optional[str] = None
    tags: Optional[Union[str, List[str]]] = None
    extracted_by: Optional[str] = None
    extraction_confidence: Optional[float] = None
    parent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @validator('tags', pre=True)
    def convert_tags_to_string(cls, v):
        """Convert list tags to comma-separated string"""
        if isinstance(v, list):
            return ', '.join(v)
        return v


class ContentListResponse(BaseModel):
    """Paginated content list response"""

    items: List[ContentItem]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class UpdateContentRequest(BaseModel):
    """Request to update a knowledge item"""

    question: Optional[str] = None
    answer: Optional[str] = None
    tags: Optional[str] = None
    source_url: Optional[str] = None
    content_type: Optional[str] = None
    regenerate_embeddings: Optional[bool] = Field(
        False, description="Regenerate embeddings if question/answer changed"
    )


class UpdateContentResponse(BaseModel):
    """Response from update endpoint"""

    success: bool
    message: str
    updated_item: ContentItem
