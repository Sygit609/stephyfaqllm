-- Migration: Add native pgvector search functions
-- Replaces manual Python cosine similarity with database-native operations
-- Performance: Leverages IVFFlat indexes for O(sqrt(n)) search vs O(n) table scan

-- Function for OpenAI embeddings (1536-dim)
CREATE OR REPLACE FUNCTION vector_search_openai(
  query_embedding VECTOR(1536),
  match_limit INT DEFAULT 100,
  filter_course_id UUID DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  question TEXT,
  question_raw TEXT,
  question_enriched TEXT,
  answer TEXT,
  category TEXT,
  tags TEXT[],
  date DATE,
  source_url TEXT,
  content_type TEXT,
  media_url TEXT,
  timecode_start INT,
  timecode_end INT,
  course_id UUID,
  module_id UUID,
  lesson_id UUID,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ki.id,
    ki.question,
    ki.question_raw,
    ki.question_enriched,
    ki.answer,
    ki.category,
    ki.tags,
    ki.date,
    ki.source_url,
    ki.content_type,
    ki.media_url,
    ki.timecode_start,
    ki.timecode_end,
    ki.course_id,
    ki.module_id,
    ki.lesson_id,
    1 - (ki.embedding_openai <=> query_embedding) AS similarity
  FROM knowledge_items ki
  WHERE
    ki.embedding_openai IS NOT NULL
    AND (filter_course_id IS NULL OR ki.course_id = filter_course_id OR ki.course_id IS NULL)
  ORDER BY ki.embedding_openai <=> query_embedding
  LIMIT match_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function for Gemini embeddings (768-dim)
CREATE OR REPLACE FUNCTION vector_search_gemini(
  query_embedding VECTOR(768),
  match_limit INT DEFAULT 100,
  filter_course_id UUID DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  question TEXT,
  question_raw TEXT,
  question_enriched TEXT,
  answer TEXT,
  category TEXT,
  tags TEXT[],
  date DATE,
  source_url TEXT,
  content_type TEXT,
  media_url TEXT,
  timecode_start INT,
  timecode_end INT,
  course_id UUID,
  module_id UUID,
  lesson_id UUID,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ki.id,
    ki.question,
    ki.question_raw,
    ki.question_enriched,
    ki.answer,
    ki.category,
    ki.tags,
    ki.date,
    ki.source_url,
    ki.content_type,
    ki.media_url,
    ki.timecode_start,
    ki.timecode_end,
    ki.course_id,
    ki.module_id,
    ki.lesson_id,
    1 - (ki.embedding_gemini <=> query_embedding) AS similarity
  FROM knowledge_items ki
  WHERE
    ki.embedding_gemini IS NOT NULL
    AND (filter_course_id IS NULL OR ki.course_id = filter_course_id OR ki.course_id IS NULL)
  ORDER BY ki.embedding_gemini <=> query_embedding
  LIMIT match_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- Add comments for documentation
COMMENT ON FUNCTION vector_search_openai IS 'Native pgvector similarity search for OpenAI embeddings. Uses IVFFlat index idx_embedding_openai for fast similarity calculations.';
COMMENT ON FUNCTION vector_search_gemini IS 'Native pgvector similarity search for Gemini embeddings. Uses IVFFlat index idx_embedding_gemini for fast similarity calculations.';

-- Document existing indexes
COMMENT ON INDEX idx_embedding_openai IS 'IVFFlat index for OpenAI embeddings (1536-dim). Used by vector_search_openai() function. Tune with ivfflat.probes parameter.';
COMMENT ON INDEX idx_embedding_gemini IS 'IVFFlat index for Gemini embeddings (768-dim). Used by vector_search_gemini() function. Tune with ivfflat.probes parameter.';
