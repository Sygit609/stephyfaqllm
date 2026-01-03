# Transcript Tagging System

## Overview

The transcript tagging system automatically generates AI-powered tags for course transcript segments to improve search accuracy and relevance. Tags help both fulltext search and LLM reranking identify the most relevant content for user queries.

## Why Tags Matter

**Before Tags:**
- Transcript segments have only raw text
- Search relies purely on keyword matching and vector embeddings
- LLM reranking has limited context about segment topics

**After Tags:**
- Each segment has 3-5 AI-generated tags describing main topics, tools, and concepts
- Tags improve fulltext search keyword matching
- LLM reranking uses tags as additional context for better relevance scoring
- Brings coaching transcripts to parity with Facebook posts (which already have tags)

## Features

### 1. Automatic Tag Generation for New Uploads

All future transcript uploads automatically generate AI tags for each segment:
- Tags are generated during the upload process
- Uses LLM to analyze segment content
- Includes tags in embeddings for better vector search
- No manual tagging required

### 2. Batch Tag Generation for Existing Transcripts

Use the batch script to add tags to existing transcript segments:

```bash
# Preview tags without saving (dry run)
PYTHONPATH=backend python3 scripts/generate_transcript_tags.py --dry-run --limit 10

# Generate tags for specific course
PYTHONPATH=backend python3 scripts/generate_transcript_tags.py --course-id a75dc54a-da4b-4229-8699-8a46b2132ef7

# Generate tags for all transcripts using OpenAI
PYTHONPATH=backend python3 scripts/generate_transcript_tags.py --provider openai

# Regenerate embeddings with tags (slower, more expensive)
PYTHONPATH=backend python3 scripts/generate_transcript_tags.py --regenerate-embeddings
```

### Command Options

- `--dry-run`: Preview tags without saving to database
- `--course-id COURSE_ID`: Generate tags for specific course only
- `--limit N`: Limit number of segments to process
- `--provider {gemini|openai}`: LLM provider for tag generation (default: gemini)
- `--regenerate-embeddings`: Regenerate embeddings including tags (recommended but slower)

## Tag Generation Process

1. **AI Analysis**: LLM analyzes the transcript segment text
2. **Context Awareness**: Uses course name and lesson name for better tags
3. **Tag Extraction**: Generates 3-5 relevant tags focusing on:
   - Main topics discussed
   - Tools, platforms, or software mentioned
   - Key concepts or techniques
   - Actionable skills taught
4. **Storage**: Tags saved as array in `knowledge_items.tags` column
5. **Embedding Enhancement**: Tags optionally included in embeddings

## Example Tags

**Coaching Call - DM Automation:**
- `dm automation, messaging, content quality, video hooks, content consistency`

**Coaching Call - Finance Management:**
- `entrepreneur finance, revenue streams, 1099 forms, click funnels, many chat`
- `finance management, entrepreneurship, business expenses, credit cards`

## Cost Estimates

**Per Segment:**
- OpenAI GPT-4: ~$0.0001-0.0002 per segment
- Gemini Flash: ~$0.00001 per segment (when quota available)

**For 1000 Segments:**
- OpenAI: ~$0.10-0.20
- Gemini: ~$0.01

**Recommended**: Use OpenAI for batch processing (more reliable, still cheap)

## Performance Impact

**Search Quality:**
- ✅ Better fulltext search matching (tags provide additional keywords)
- ✅ Improved LLM reranking (more context about segment topics)
- ✅ More accurate results for topic-specific queries

**Upload Time:**
- **Without Tags**: ~2-3 seconds per segment (embeddings only)
- **With Tags**: ~3-5 seconds per segment (tags + embeddings)
- **With Regenerated Embeddings**: ~4-6 seconds per segment

Trade-off is worth it for significantly better search accuracy.

## Implementation Details

### Database Schema

Tags stored in existing `tags` column:
```sql
tags TEXT[] -- Array of tags
```

### Files Modified

**Backend:**
- `backend/app/services/transcription.py` - Added `generate_segment_tags()` method
- `backend/app/services/transcription.py` - Updated `create_transcript_segments()` to auto-generate tags

**Scripts:**
- `scripts/generate_transcript_tags.py` - Batch tag generation script

### Future Enhancements

1. **Tag Analytics**: Track most common tags, create tag clouds
2. **Tag Filtering**: Allow users to filter search results by tag
3. **Tag Hierarchies**: Group related tags (e.g., "instagram" → "social media")
4. **Manual Tag Editing**: Admin UI to edit/add tags manually
5. **Tag-based Recommendations**: "More like this" based on shared tags

## Running Batch Tagging

### For All Coaching Call Replays

```bash
PYTHONPATH=backend python3 scripts/generate_transcript_tags.py \
  --course-id a75dc54a-da4b-4229-8699-8a46b2132ef7 \
  --provider openai
```

### For Online Income Lab

```bash
PYTHONPATH=backend python3 scripts/generate_transcript_tags.py \
  --course-id 233efed3-6f20-4f9c-a15a-1b3ee17118dd \
  --provider openai
```

### For All Transcripts

```bash
PYTHONPATH=backend python3 scripts/generate_transcript_tags.py \
  --provider openai
```

## Testing

The script was tested with 3 sample coaching transcripts and successfully generated relevant tags:
- DM automation segment → `dm automation, messaging, content quality, video hooks, content consistency`
- Finance management segment → `entrepreneur finance, revenue streams, 1099 forms, click funnels, many chat`
- Business expenses segment → `finance management, entrepreneurship, business expenses, credit cards`

## Next Steps

1. Run batch tagging for all existing transcripts
2. Monitor search quality improvements
3. Consider regenerating embeddings with tags for even better search
4. Track user feedback on search relevance

## Support

For issues or questions:
- Check script output for error messages
- Review API quota limits (Gemini free tier has strict limits)
- Use `--dry-run` flag to preview before committing
- Use `--provider openai` if Gemini quota exceeded
