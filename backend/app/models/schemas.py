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


# ============================================================
# Course Transcript Management Models
# ============================================================


class CreateCourseRequest(BaseModel):
    """Request to create a new course"""

    name: str = Field(..., description="Course name")
    description: str = Field(..., description="Course description")
    thumbnail_url: Optional[str] = Field(None, description="Course thumbnail URL")


class CreateModuleRequest(BaseModel):
    """Request to create a new module"""

    name: str = Field(..., description="Module name")
    description: str = Field(..., description="Module description")


class CreateLessonRequest(BaseModel):
    """Request to create a new lesson"""

    name: str = Field(..., description="Lesson name")
    description: str = Field(..., description="Lesson description")
    video_url: Optional[str] = Field(None, description="External video URL")
    video_platform: Optional[str] = Field(None, description="Video platform (vimeo, youtube, etc.)")


class TranscribeRequest(BaseModel):
    """Request to transcribe a video lesson"""

    language: str = Field("en", description="Language code (e.g., en, es, fr)")
    segment_duration: int = Field(45, ge=30, le=60, description="Target segment duration in seconds")


class UploadVideoResponse(BaseModel):
    """Response after uploading video"""

    success: bool
    video_url: str = Field(..., description="URL to uploaded video")
    duration_seconds: Optional[int] = None


class TranscriptionResponse(BaseModel):
    """Response from transcription endpoint"""

    success: bool
    lesson_id: str
    segments_created: int
    segment_ids: List[str]
    cost_usd: float
    duration_seconds: int
    language: str


class UploadTranscriptResponse(BaseModel):
    """Response after uploading transcript file"""

    success: bool
    lesson_id: str
    segments_created: int
    segment_ids: List[str]
    format: str  # srt or vtt


class Segment(BaseModel):
    """Video transcript segment"""

    id: str
    lesson_id: str
    text: str
    timecode_start: int = Field(..., description="Start time in seconds")
    timecode_end: int = Field(..., description="End time in seconds")
    created_at: datetime
    updated_at: datetime


class UpdateSegmentRequest(BaseModel):
    """Request to update a transcript segment"""

    text: str = Field(..., description="Edited transcript text")
    timecode_start: Optional[int] = Field(None, description="Start time in seconds")
    timecode_end: Optional[int] = Field(None, description="End time in seconds")


class CloneCourseRequest(BaseModel):
    """Request to clone a course"""

    new_name: str = Field(..., description="Name for cloned course")
    regenerate_embeddings: bool = Field(
        False,
        description="If True, regenerate embeddings for all segments (slower, more expensive)"
    )


class CloneCourseResponse(BaseModel):
    """Response from clone course endpoint"""

    success: bool
    new_course_id: str
    message: str
    segments_cloned: int
    embeddings_regenerated: bool


class CourseTreeNode(BaseModel):
    """Single node in course tree (recursive)"""

    id: str
    name: str
    description: str
    type: str = Field(..., description="course, module, lesson, or segment")
    hierarchy_level: int
    children: List['CourseTreeNode'] = []
    metadata: Dict[str, Any] = {}


# Enable forward references for recursive model
CourseTreeNode.model_rebuild()


class Course(BaseModel):
    """Course summary for grid view"""

    id: str
    name: str
    description: str
    thumbnail_url: Optional[str] = None
    module_count: int = 0
    lesson_count: int = 0
    segment_count: int = 0
    total_duration_seconds: int = 0
    created_at: datetime
    updated_at: datetime


class CourseListResponse(BaseModel):
    """Response with list of courses"""

    courses: List[Course]
    total_count: int


class CourseTreeResponse(BaseModel):
    """Response with full course tree"""

    course: CourseTreeNode


class Folder(BaseModel):
    """Generic folder (course, module, or lesson)"""

    id: str
    name: str
    description: str
    type: str
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class UpdateFolderRequest(BaseModel):
    """Request to update folder metadata"""

    name: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    video_duration_seconds: Optional[int] = None


class DeleteFolderResponse(BaseModel):
    """Response from delete folder endpoint"""

    success: bool
    deleted_count: int = Field(..., description="Total items deleted (including children)")
    message: str


class CourseStatsResponse(BaseModel):
    """Course statistics"""

    course_id: str
    course_name: str
    module_count: int
    lesson_count: int
    segment_count: int
    total_duration_seconds: int
    last_updated: datetime
