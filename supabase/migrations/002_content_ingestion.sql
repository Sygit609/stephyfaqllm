-- Migration: Add content ingestion fields for screenshots and video transcripts
-- Created: 2025-12-22
-- Phase: 3 - Content Ingestion Enhancement

-- Add new columns to knowledge_items table
ALTER TABLE knowledge_items
ADD COLUMN content_type VARCHAR(50) DEFAULT 'manual',
ADD COLUMN media_url TEXT,
ADD COLUMN media_thumbnail TEXT,
ADD COLUMN timecode_start INTEGER,
ADD COLUMN timecode_end INTEGER,
ADD COLUMN extracted_by VARCHAR(50),
ADD COLUMN extraction_confidence DECIMAL(3,2),
ADD COLUMN raw_content JSONB,
ADD COLUMN parent_id UUID REFERENCES knowledge_items(id) ON DELETE CASCADE;

-- Add check constraint for content_type
ALTER TABLE knowledge_items
ADD CONSTRAINT content_type_check
CHECK (content_type IN ('manual', 'csv', 'screenshot', 'facebook', 'video'));

-- Add check constraint for extracted_by
ALTER TABLE knowledge_items
ADD CONSTRAINT extracted_by_check
CHECK (extracted_by IS NULL OR extracted_by IN ('manual', 'gemini-vision', 'gpt4-vision'));

-- Add check constraint for confidence score
ALTER TABLE knowledge_items
ADD CONSTRAINT confidence_check
CHECK (extraction_confidence IS NULL OR (extraction_confidence >= 0 AND extraction_confidence <= 1));

-- Create indexes for better query performance
CREATE INDEX idx_content_type ON knowledge_items(content_type);
CREATE INDEX idx_parent_id ON knowledge_items(parent_id);
CREATE INDEX idx_extracted_by ON knowledge_items(extracted_by);
CREATE INDEX idx_extraction_confidence ON knowledge_items(extraction_confidence);
CREATE INDEX idx_media_url ON knowledge_items(media_url) WHERE media_url IS NOT NULL;

-- Add comment to document schema changes
COMMENT ON COLUMN knowledge_items.content_type IS 'Type of content: manual, csv, screenshot, facebook, video';
COMMENT ON COLUMN knowledge_items.media_url IS 'URL to screenshot image or video';
COMMENT ON COLUMN knowledge_items.media_thumbnail IS 'Thumbnail URL for display';
COMMENT ON COLUMN knowledge_items.timecode_start IS 'Video start time in seconds';
COMMENT ON COLUMN knowledge_items.timecode_end IS 'Video end time in seconds';
COMMENT ON COLUMN knowledge_items.extracted_by IS 'Extraction method: manual, gemini-vision, gpt4-vision';
COMMENT ON COLUMN knowledge_items.extraction_confidence IS 'AI extraction confidence score (0.0 to 1.0)';
COMMENT ON COLUMN knowledge_items.raw_content IS 'Original extraction response from vision API';
COMMENT ON COLUMN knowledge_items.parent_id IS 'Links child Q&As to parent screenshot/video entry';

-- Create helper view for content with children
CREATE OR REPLACE VIEW knowledge_items_with_children AS
SELECT
    parent.*,
    COUNT(child.id) as child_count
FROM knowledge_items parent
LEFT JOIN knowledge_items child ON child.parent_id = parent.id
GROUP BY parent.id;

-- Create helper view for extraction analytics
CREATE OR REPLACE VIEW extraction_analytics AS
SELECT
    extracted_by,
    content_type,
    COUNT(*) as total_items,
    AVG(extraction_confidence) as avg_confidence,
    MIN(extraction_confidence) as min_confidence,
    MAX(extraction_confidence) as max_confidence,
    COUNT(CASE WHEN extraction_confidence >= 0.8 THEN 1 END) as high_confidence_count,
    COUNT(CASE WHEN extraction_confidence < 0.8 THEN 1 END) as low_confidence_count
FROM knowledge_items
WHERE extracted_by IS NOT NULL
GROUP BY extracted_by, content_type;

COMMENT ON VIEW knowledge_items_with_children IS 'Shows parent items with count of linked children';
COMMENT ON VIEW extraction_analytics IS 'Analytics on extraction quality by method and content type';
