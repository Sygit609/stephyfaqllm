-- Migration: Add course transcript management with hierarchical folder structure
-- Created: 2025-12-27
-- Phase: Course Transcript Management (Phase 4)

-- Add hierarchy and course tracking fields to knowledge_items table
ALTER TABLE knowledge_items
ADD COLUMN hierarchy_level INTEGER CHECK(hierarchy_level BETWEEN 1 AND 4),
ADD COLUMN course_id UUID REFERENCES knowledge_items(id) ON DELETE CASCADE,
ADD COLUMN module_id UUID REFERENCES knowledge_items(id) ON DELETE CASCADE,
ADD COLUMN lesson_id UUID REFERENCES knowledge_items(id) ON DELETE CASCADE,
ADD COLUMN video_duration_seconds INTEGER,
ADD COLUMN transcript_language VARCHAR(10) DEFAULT 'en',
ADD COLUMN transcript_format VARCHAR(10) CHECK(transcript_format IN ('srt', 'vtt', 'whisper')),
ADD COLUMN video_platform VARCHAR(50);

-- Create indexes for better query performance
CREATE INDEX idx_hierarchy_level ON knowledge_items(hierarchy_level);
CREATE INDEX idx_course_id ON knowledge_items(course_id);
CREATE INDEX idx_module_id ON knowledge_items(module_id);
CREATE INDEX idx_lesson_id ON knowledge_items(lesson_id);
CREATE INDEX idx_timecode_range ON knowledge_items(timecode_start, timecode_end);

-- Add comments to document schema changes
COMMENT ON COLUMN knowledge_items.hierarchy_level IS 'Course structure level: 1=Course, 2=Module, 3=Lesson, 4=Transcript Segment. NULL=not part of course structure';
COMMENT ON COLUMN knowledge_items.course_id IS 'Reference to top-level course (hierarchy_level=1) for quick filtering';
COMMENT ON COLUMN knowledge_items.module_id IS 'Reference to parent module (hierarchy_level=2) for quick filtering';
COMMENT ON COLUMN knowledge_items.lesson_id IS 'Reference to parent lesson (hierarchy_level=3) for quick filtering';
COMMENT ON COLUMN knowledge_items.video_duration_seconds IS 'Total video duration in seconds (for lessons)';
COMMENT ON COLUMN knowledge_items.transcript_language IS 'Language code for transcript (e.g., en, es, fr)';
COMMENT ON COLUMN knowledge_items.transcript_format IS 'Source format of transcript: srt, vtt, or whisper';
COMMENT ON COLUMN knowledge_items.video_platform IS 'Video hosting platform (e.g., vimeo, youtube, custom)';

-- Create helper view for course tree retrieval using recursive CTE
CREATE OR REPLACE VIEW course_hierarchy AS
WITH RECURSIVE course_tree AS (
  -- Base case: Start with top-level courses (hierarchy_level = 1)
  SELECT
    id,
    question as name,
    content_type,
    hierarchy_level,
    1 as level,
    ARRAY[id] as path,
    NULL::uuid as parent_id,
    id as course_id,
    media_url,
    media_thumbnail,
    video_duration_seconds,
    created_at
  FROM knowledge_items
  WHERE content_type = 'video' AND hierarchy_level = 1

  UNION ALL

  -- Recursive case: Get children of previous level
  SELECT
    ki.id,
    ki.question as name,
    ki.content_type,
    ki.hierarchy_level,
    ct.level + 1 as level,
    ct.path || ki.id as path,
    ki.parent_id,
    ct.course_id,
    ki.media_url,
    ki.media_thumbnail,
    ki.video_duration_seconds,
    ki.created_at
  FROM knowledge_items ki
  JOIN course_tree ct ON ki.parent_id = ct.id
  WHERE ki.content_type = 'video' AND ki.hierarchy_level <= 4
)
SELECT * FROM course_tree
ORDER BY path;

COMMENT ON VIEW course_hierarchy IS 'Recursive tree view of all courses with their modules, lessons, and segments';

-- Create helper view for course statistics
CREATE OR REPLACE VIEW course_stats AS
SELECT
  c.id as course_id,
  c.question as course_name,
  COUNT(DISTINCT CASE WHEN ki.hierarchy_level = 2 THEN ki.id END) as module_count,
  COUNT(DISTINCT CASE WHEN ki.hierarchy_level = 3 THEN ki.id END) as lesson_count,
  COUNT(DISTINCT CASE WHEN ki.hierarchy_level = 4 THEN ki.id END) as segment_count,
  SUM(CASE WHEN ki.hierarchy_level = 3 THEN ki.video_duration_seconds ELSE 0 END) as total_duration_seconds,
  MAX(ki.updated_at) as last_updated
FROM knowledge_items c
LEFT JOIN knowledge_items ki ON ki.course_id = c.id
WHERE c.content_type = 'video' AND c.hierarchy_level = 1
GROUP BY c.id, c.question;

COMMENT ON VIEW course_stats IS 'Aggregated statistics for each course (module/lesson/segment counts, total duration)';

-- Create helper function to get full course path for any item
CREATE OR REPLACE FUNCTION get_course_path(item_id UUID)
RETURNS TABLE(
  course_name TEXT,
  module_name TEXT,
  lesson_name TEXT,
  segment_name TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    (SELECT question FROM knowledge_items WHERE id = ki.course_id) as course_name,
    (SELECT question FROM knowledge_items WHERE id = ki.module_id) as module_name,
    (SELECT question FROM knowledge_items WHERE id = ki.lesson_id) as lesson_name,
    ki.question as segment_name
  FROM knowledge_items ki
  WHERE ki.id = item_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_course_path IS 'Returns full course path (Course → Module → Lesson → Segment) for any knowledge item';
