-- Migration: Add 'whisper' to extracted_by constraint
-- Created: 2025-12-28
-- Purpose: Allow transcript segments to use 'whisper' as extracted_by value

-- Drop the old constraint
ALTER TABLE knowledge_items
DROP CONSTRAINT IF EXISTS extracted_by_check;

-- Add updated constraint with 'whisper' included
ALTER TABLE knowledge_items
ADD CONSTRAINT extracted_by_check
CHECK (extracted_by IS NULL OR extracted_by IN ('manual', 'gemini-vision', 'gpt4-vision', 'whisper'));

-- Update comment
COMMENT ON COLUMN knowledge_items.extracted_by IS 'Extraction method: manual, gemini-vision, gpt4-vision, whisper';
