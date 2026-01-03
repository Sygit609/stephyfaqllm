#!/usr/bin/env python3
"""
Batch Tag Generation for Course Transcripts

This script generates AI tags for all existing course transcript segments
to improve search accuracy and LLM reranking performance.

Usage:
    python scripts/generate_transcript_tags.py [--dry-run] [--course-id COURSE_ID] [--limit N]

Examples:
    # Preview tags without saving (dry run)
    python scripts/generate_transcript_tags.py --dry-run --limit 10

    # Generate tags for specific course
    python scripts/generate_transcript_tags.py --course-id a75dc54a-da4b-4229-8699-8a46b2132ef7

    # Generate tags for all transcripts
    python scripts/generate_transcript_tags.py
"""

import asyncio
import argparse
import sys
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_db
from app.services.llm_adapters import get_adapter
from app.services.content_manager import generate_dual_embeddings


async def generate_tags_for_segment(
    segment: Dict[str, Any],
    provider: str = "gemini"
) -> List[str]:
    """
    Generate 3-5 relevant tags for a transcript segment using AI

    Args:
        segment: Segment data with question, answer, metadata
        provider: LLM provider to use

    Returns:
        List of generated tags
    """
    adapter = get_adapter(provider)

    # Build context from segment
    text = segment.get("answer", "")
    lesson_name = segment.get("lesson_name", "")
    course_name = segment.get("course_name", "")

    # Limit text length to avoid token limits
    text_preview = text[:500] if len(text) > 500 else text

    system_prompt = """You are a content tagging expert. Generate 3-5 relevant tags for this course transcript segment.

Focus on:
- Main topics discussed
- Tools, platforms, or software mentioned
- Key concepts or techniques
- Actionable skills taught

Return ONLY comma-separated tags in lowercase, like: facebook ads, targeting, audience building, lookalike audiences

Keep tags concise (1-3 words each) and relevant."""

    user_prompt = f"""Course: {course_name}
Lesson: {lesson_name}

Transcript Segment:
{text_preview}

Generate 3-5 relevant tags:"""

    try:
        # Generate tags using LLM
        response, metadata = await adapter.generate_answer(
            query=user_prompt,
            context="",
            system_prompt=system_prompt,
            max_tokens=50  # Short response
        )

        # Parse tags from response
        tags_text = response.strip().lower()

        # Clean up response (remove any explanations)
        if '\n' in tags_text:
            tags_text = tags_text.split('\n')[0]

        # Split by comma and clean
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]

        # Limit to 5 tags max
        tags = tags[:5]

        return tags

    except Exception as e:
        print(f"Error generating tags: {e}")
        # Return empty tags on error rather than failing
        return []


async def get_transcript_segments(
    course_id: str = None,
    limit: int = None
) -> List[Dict[str, Any]]:
    """
    Fetch transcript segments from database

    Args:
        course_id: Optional course ID to filter by
        limit: Optional limit on number of segments

    Returns:
        List of segment data with metadata
    """
    db = get_db()

    # Build query
    query = db.table("knowledge_items").select(
        "id, question, answer, tags, course_id, module_id, lesson_id, "
        "parent_id, content_type, hierarchy_level"
    )

    # Filter for transcript segments only (hierarchy_level = 4)
    query = query.eq("hierarchy_level", 4)
    query = query.eq("content_type", "video")

    # Optional course filter
    if course_id:
        query = query.eq("course_id", course_id)

    # Optional limit
    if limit:
        query = query.limit(limit)

    response = query.execute()
    segments = response.data

    # Enrich with course/lesson names for better tag generation
    for segment in segments:
        # Get lesson name
        if segment.get("lesson_id"):
            lesson_response = db.table("knowledge_items")\
                .select("question")\
                .eq("id", segment["lesson_id"])\
                .single()\
                .execute()
            segment["lesson_name"] = lesson_response.data.get("question", "") if lesson_response.data else ""

        # Get course name
        if segment.get("course_id"):
            course_response = db.table("knowledge_items")\
                .select("question")\
                .eq("id", segment["course_id"])\
                .single()\
                .execute()
            segment["course_name"] = course_response.data.get("question", "") if course_response.data else ""

    return segments


async def update_segment_tags(
    segment_id: str,
    tags: List[str],
    regenerate_embeddings: bool = False
) -> bool:
    """
    Update tags for a segment in the database

    Args:
        segment_id: Segment UUID
        tags: List of tags to save
        regenerate_embeddings: Whether to regenerate embeddings with new tags

    Returns:
        Success status
    """
    db = get_db()

    try:
        # Update tags
        update_data = {"tags": tags}

        # Optionally regenerate embeddings
        if regenerate_embeddings:
            segment = db.table("knowledge_items")\
                .select("question, answer")\
                .eq("id", segment_id)\
                .single()\
                .execute()

            if segment.data:
                question = segment.data.get("question", "")
                answer = segment.data.get("answer", "")

                # Generate new embeddings with tags included
                tags_text = ", ".join(tags)
                enriched_text = f"{question}. Tags: {tags_text}. {answer}"

                openai_emb, gemini_emb = await generate_dual_embeddings(enriched_text)

                update_data["embedding_openai"] = openai_emb
                update_data["embedding_gemini"] = gemini_emb

        # Save to database
        db.table("knowledge_items")\
            .update(update_data)\
            .eq("id", segment_id)\
            .execute()

        return True

    except Exception as e:
        print(f"Error updating segment {segment_id}: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(
        description="Generate AI tags for course transcript segments"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview tags without saving to database"
    )
    parser.add_argument(
        "--course-id",
        type=str,
        help="Generate tags for specific course only"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of segments to process"
    )
    parser.add_argument(
        "--regenerate-embeddings",
        action="store_true",
        help="Regenerate embeddings with new tags (slower, more expensive)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="gemini",
        choices=["gemini", "openai"],
        help="LLM provider for tag generation"
    )

    args = parser.parse_args()

    print("🏷️  Course Transcript Tag Generator")
    print("=" * 60)

    # Fetch segments
    print(f"\n📚 Fetching transcript segments...")
    if args.course_id:
        print(f"   Filtering by course: {args.course_id}")
    if args.limit:
        print(f"   Limiting to {args.limit} segments")

    segments = await get_transcript_segments(
        course_id=args.course_id,
        limit=args.limit
    )

    print(f"   Found {len(segments)} segments to process")

    if len(segments) == 0:
        print("\n⚠️  No segments found!")
        return

    # Preview mode
    if args.dry_run:
        print(f"\n🔍 DRY RUN MODE - Tags will NOT be saved")

    # Process segments
    print(f"\n🤖 Generating tags using {args.provider}...")

    success_count = 0
    skip_count = 0
    error_count = 0
    total_cost = 0.0

    for idx, segment in enumerate(segments, 1):
        segment_id = segment["id"]
        existing_tags = segment.get("tags") or []

        # Skip if already has tags (unless dry run for preview)
        if existing_tags and not args.dry_run:
            skip_count += 1
            if idx <= 5 or idx % 50 == 0:
                print(f"   [{idx}/{len(segments)}] Skipping (already tagged): {segment.get('lesson_name', 'Unknown')[:50]}")
            continue

        # Generate tags
        tags = await generate_tags_for_segment(segment, provider=args.provider)

        if not tags:
            error_count += 1
            print(f"   [{idx}/{len(segments)}] ❌ Failed: {segment.get('lesson_name', 'Unknown')[:50]}")
            continue

        # Preview or save
        if args.dry_run:
            print(f"\n   [{idx}/{len(segments)}] Preview:")
            print(f"      Course: {segment.get('course_name', 'Unknown')}")
            print(f"      Lesson: {segment.get('lesson_name', 'Unknown')}")
            print(f"      Segment: {segment.get('answer', '')[:100]}...")
            print(f"      📌 Generated Tags: {', '.join(tags)}")
            if existing_tags:
                print(f"      (Existing tags: {', '.join(existing_tags)})")
        else:
            # Save tags
            success = await update_segment_tags(
                segment_id,
                tags,
                regenerate_embeddings=args.regenerate_embeddings
            )

            if success:
                success_count += 1
                if idx <= 5 or idx % 50 == 0:
                    print(f"   [{idx}/{len(segments)}] ✅ {', '.join(tags)} - {segment.get('lesson_name', 'Unknown')[:50]}")
            else:
                error_count += 1

        # Estimate cost (rough approximation)
        # ~500 tokens per segment (input + output)
        total_cost += 0.00001  # Gemini Flash cost

    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"   Total segments: {len(segments)}")

    if args.dry_run:
        print(f"   ✅ Previewed: {len(segments)}")
        print(f"   💡 Run without --dry-run to save tags")
    else:
        print(f"   ✅ Successfully tagged: {success_count}")
        print(f"   ⏭️  Skipped (already tagged): {skip_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   💰 Estimated cost: ${total_cost:.4f}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
