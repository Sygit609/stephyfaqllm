/**
 * TypeScript type definitions matching backend Pydantic schemas
 * Source: backend/app/models/schemas.py
 */

// ============================================================================
// Source and Search Types
// ============================================================================

export interface SourceMatch {
  id: string
  question: string
  answer: string
  category: string | null
  tags: string[]
  date: string | null
  source_url: string | null
  score: number
  match_type: "vector" | "fulltext" | "hybrid"
}

export interface SearchRequest {
  query: string
  provider?: "gemini" | "openai"
  limit?: number
}

export interface SearchResponse {
  query: string
  sources: SourceMatch[]
  total_found: number
  provider: string
  intent: string
  recency_required: boolean
}

// ============================================================================
// Answer Generation Types
// ============================================================================

export interface AnswerRequest {
  query: string
  sources: Record<string, any>[]
  provider?: "gemini" | "openai"
}

export interface AnswerMetadata {
  model: string
  tokens_input: number
  tokens_output: number
  latency_ms: number
  cost_usd: number
}

export interface AnswerResponse {
  query: string
  answer: string
  sources_used: SourceMatch[]
  provider: string
  metadata: AnswerMetadata
}

// ============================================================================
// Query (Main Endpoint) Types
// ============================================================================

export interface WebResult {
  title: string
  url: string
  content: string
  score: number
}

export interface QueryRequest {
  query: string
  provider?: "gemini" | "openai"
  search_limit?: number
  use_web_search?: boolean
}

export interface QueryResponse {
  query: string
  answer: string
  sources: SourceMatch[]
  web_search_used: boolean
  web_results: WebResult[] | null
  intent: string
  recency_required: boolean
  provider: string
  metadata: AnswerMetadata
  query_id: string
}

// ============================================================================
// Feedback Types
// ============================================================================

export interface FeedbackRequest {
  query_id: string
  rating?: number  // 1-5
  was_edited: boolean
  staff_notes?: string
}

export interface FeedbackResponse {
  success: boolean
  query_id: string
  message: string
}

// ============================================================================
// Metrics Types
// ============================================================================

export interface ModelMetrics {
  provider: string
  total_queries: number
  avg_latency_ms: number | null
  total_cost_usd: number
  avg_cost_per_query: number
  avg_rating: number | null
  edit_rate: number | null
  web_searches: number
}

export interface MetricsResponse {
  period_days: number
  models: ModelMetrics[]
  total_queries: number
}

// ============================================================================
// Query History Types
// ============================================================================

export interface QueryLogEntry {
  id: string
  query_text: string
  model_provider: string
  intent_type: string | null
  latency_ms: number | null
  cost_usd: number | null
  staff_rating: number | null
  was_edited: boolean
  created_at: string
}

export interface RecentQueriesResponse {
  queries: QueryLogEntry[]
  total: number
}

// ============================================================================
// Health Check Types
// ============================================================================

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy"
  database_connected: boolean
  api_keys_valid: {
    openai: boolean
    google: boolean
    tavily: boolean
  }
  environment: string
}

// ============================================================================
// UI State Types (Frontend-only)
// ============================================================================

export type ModelProvider = "gemini" | "openai"

export interface UIState {
  selectedProvider: ModelProvider
  searchLimit: number
  useWebSearch: boolean
}

export interface QuerySessionState {
  queryText: string
  answer: string
  originalAnswer: string
  sources: SourceMatch[]
  webResults: WebResult[] | null
  queryId: string | null
  isEditMode: boolean
  rating: number | null
  intent: string | null
  recency_required: boolean
  provider: ModelProvider
  metadata: AnswerMetadata | null
}

// ============================================================================
// API Error Types
// ============================================================================

export interface APIError {
  detail: string
  status_code?: number
}

export interface ValidationError {
  loc: (string | number)[]
  msg: string
  type: string
}

export interface HTTPValidationError {
  detail: ValidationError[]
}

// ============================================================================
// Admin - Content Ingestion Types
// ============================================================================

export interface QAPair {
  question: string
  answer: string
  tags: string[]
}

export interface ExtractScreenshotRequest {
  image_data: string  // Base64-encoded image
  source_url: string
  provider?: "gemini" | "openai"
  use_fallback?: boolean
}

export interface ExtractScreenshotResponse {
  qa_pairs: QAPair[]
  confidence: number  // 0.0 to 1.0
  model_used: string
  used_fallback: boolean
  warnings: string[]
  metadata: {
    model: string
    tokens_input?: number
    tokens_output?: number
    latency_ms: number
    cost_usd: number
    source_url: string
    raw_response?: string
  }
}

export interface SaveContentRequest {
  qa_pairs: QAPair[]
  media_url: string
  source_url: string
  extracted_by: string  // gemini-vision or gpt4-vision
  confidence: number
  raw_extraction?: Record<string, any>
  content_type?: string
}

export interface SaveContentResponse {
  success: boolean
  parent_id: string
  child_ids: string[]
  total_saved: number
}

export interface ContentItem {
  id: string
  content_type: string
  question: string
  answer: string
  source_url: string | null
  media_url: string | null
  tags: string | null
  extracted_by: string | null
  extraction_confidence: number | null
  parent_id: string | null
  created_at: string
  updated_at: string
}

export interface ContentListResponse {
  items: ContentItem[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
}
