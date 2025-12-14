-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pg_trgm for better text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================
-- Table: knowledge_items
-- Stores Q&As and announcements from the Facebook group
-- ============================================================
CREATE TABLE knowledge_items (
  -- Primary key
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Content fields
  content_type TEXT NOT NULL CHECK(content_type IN ('qa', 'announcement')) DEFAULT 'qa',
  thread_id TEXT,  -- Groups related Q&As from same Facebook thread

  question_raw TEXT,  -- Original messy question from Facebook
  question_enriched TEXT,  -- Cleaned-up version for better matching
  answer TEXT NOT NULL,

  -- Metadata
  answered_by TEXT,
  category TEXT,  -- 'internal', 'instagram', 'funnel_freedom', 'email_marketing', etc.
  tags TEXT[],  -- Array: ['instagram', 'follow_block', 'dm_block']

  -- Recency tracking
  date DATE NOT NULL,
  is_time_sensitive BOOLEAN DEFAULT false,
  valid_until TIMESTAMP,  -- For time-sensitive announcements (e.g., "This week's zoom link")

  -- Source attribution
  source TEXT DEFAULT 'fb_group',  -- 'fb_group', 'manual', 'screenshot'
  source_url TEXT,

  -- Search optimization
  embedding_openai VECTOR(1536),  -- OpenAI text-embedding-3-small (1536 dimensions)
  embedding_gemini VECTOR(768),   -- Gemini text-embedding-004 (768 dimensions)
  search_vector tsvector,  -- Postgres full-text search

  -- Audit
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  embedding_generated_at TIMESTAMP
);

-- Indexes for efficient queries
CREATE INDEX idx_content_type ON knowledge_items(content_type);
CREATE INDEX idx_category ON knowledge_items(category);
CREATE INDEX idx_date ON knowledge_items(date DESC);
CREATE INDEX idx_is_time_sensitive ON knowledge_items(is_time_sensitive);
CREATE INDEX idx_tags ON knowledge_items USING GIN(tags);
CREATE INDEX idx_search_vector ON knowledge_items USING GIN(search_vector);
CREATE INDEX idx_thread_id ON knowledge_items(thread_id);

-- Vector indexes for semantic search (using IVFFlat algorithm)
-- Note: These indexes will be created after data is inserted (need at least 1000 rows for optimal performance)
-- For now, we'll create them anyway for the MVP
CREATE INDEX idx_embedding_openai ON knowledge_items
  USING ivfflat(embedding_openai vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_embedding_gemini ON knowledge_items
  USING ivfflat(embedding_gemini vector_cosine_ops) WITH (lists = 100);

-- Trigger to update search_vector automatically
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.question_raw, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.question_enriched, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.answer, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_search_vector
  BEFORE INSERT OR UPDATE ON knowledge_items
  FOR EACH ROW
  EXECUTE FUNCTION update_search_vector();

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_updated_at
  BEFORE UPDATE ON knowledge_items
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Table: query_logs
-- Tracks all queries for metrics and comparison
-- ============================================================
CREATE TABLE query_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Query info
  query_text TEXT NOT NULL,
  model_provider TEXT NOT NULL CHECK(model_provider IN ('gemini', 'openai')),

  -- Classification results
  intent_type TEXT,  -- 'internal', 'external', 'both'
  recency_required BOOLEAN DEFAULT false,
  extracted_entities JSONB,  -- Store any extracted dates, tool names, etc.

  -- Search results
  sources_found JSONB,  -- Array of matched sources with scores
  web_search_used BOOLEAN DEFAULT false,
  web_search_results JSONB,  -- Tavily results if used

  -- Generation
  answer_generated TEXT,

  -- Performance metrics
  latency_ms INTEGER,
  tokens_input INTEGER,
  tokens_output INTEGER,
  cost_usd DECIMAL(10, 6),

  -- User feedback (optional for later)
  staff_rating INTEGER CHECK(staff_rating >= 1 AND staff_rating <= 5),
  was_edited BOOLEAN DEFAULT false,
  staff_notes TEXT,

  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for query logs
CREATE INDEX idx_query_logs_provider ON query_logs(model_provider);
CREATE INDEX idx_query_logs_created ON query_logs(created_at DESC);
CREATE INDEX idx_query_logs_intent ON query_logs(intent_type);

-- ============================================================
-- Table: model_metrics
-- Aggregate stats per model per day
-- ============================================================
CREATE TABLE model_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  model_provider TEXT NOT NULL CHECK(model_provider IN ('gemini', 'openai')),
  date DATE NOT NULL,

  -- Usage stats
  total_queries INTEGER DEFAULT 0,
  avg_latency_ms INTEGER,
  total_cost_usd DECIMAL(10, 4),
  total_tokens_input BIGINT DEFAULT 0,
  total_tokens_output BIGINT DEFAULT 0,

  -- Quality metrics (from staff feedback)
  avg_rating DECIMAL(3, 2),
  edit_rate DECIMAL(3, 2),  -- % of answers that needed editing (0.00 to 1.00)
  total_ratings INTEGER DEFAULT 0,

  updated_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(model_provider, date)
);

CREATE INDEX idx_model_metrics_date ON model_metrics(date DESC);
CREATE INDEX idx_model_metrics_provider ON model_metrics(model_provider);

-- Function to aggregate metrics from query_logs
CREATE OR REPLACE FUNCTION aggregate_model_metrics(target_date DATE DEFAULT CURRENT_DATE)
RETURNS void AS $$
BEGIN
  INSERT INTO model_metrics (
    model_provider,
    date,
    total_queries,
    avg_latency_ms,
    total_cost_usd,
    total_tokens_input,
    total_tokens_output,
    avg_rating,
    edit_rate,
    total_ratings
  )
  SELECT
    model_provider,
    target_date,
    COUNT(*) as total_queries,
    AVG(latency_ms)::INTEGER as avg_latency_ms,
    SUM(cost_usd) as total_cost_usd,
    SUM(tokens_input) as total_tokens_input,
    SUM(tokens_output) as total_tokens_output,
    AVG(staff_rating) as avg_rating,
    AVG(CASE WHEN was_edited THEN 1.0 ELSE 0.0 END) as edit_rate,
    COUNT(staff_rating) as total_ratings
  FROM query_logs
  WHERE DATE(created_at) = target_date
  GROUP BY model_provider
  ON CONFLICT (model_provider, date)
  DO UPDATE SET
    total_queries = EXCLUDED.total_queries,
    avg_latency_ms = EXCLUDED.avg_latency_ms,
    total_cost_usd = EXCLUDED.total_cost_usd,
    total_tokens_input = EXCLUDED.total_tokens_input,
    total_tokens_output = EXCLUDED.total_tokens_output,
    avg_rating = EXCLUDED.avg_rating,
    edit_rate = EXCLUDED.edit_rate,
    total_ratings = EXCLUDED.total_ratings,
    updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Helpful views for quick analysis
-- ============================================================

-- View: Recent queries with performance
CREATE VIEW recent_queries AS
SELECT
  id,
  query_text,
  model_provider,
  intent_type,
  latency_ms,
  cost_usd,
  staff_rating,
  was_edited,
  created_at
FROM query_logs
ORDER BY created_at DESC
LIMIT 100;

-- View: Model comparison
CREATE VIEW model_comparison AS
SELECT
  model_provider,
  COUNT(*) as total_queries,
  AVG(latency_ms)::INTEGER as avg_latency_ms,
  SUM(cost_usd) as total_cost_usd,
  AVG(cost_usd) as avg_cost_per_query,
  AVG(staff_rating) as avg_rating,
  AVG(CASE WHEN was_edited THEN 1.0 ELSE 0.0 END) as edit_rate,
  COUNT(CASE WHEN web_search_used THEN 1 END) as web_searches
FROM query_logs
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY model_provider;

-- ============================================================
-- Sample data for testing (optional - remove if not needed)
-- ============================================================
-- This will be populated by the import script
