#!/usr/bin/env python3
"""
Regenerate Embeddings Script
Generates embeddings for segments that exist in course_folders but not in knowledge_items
"""

import requests
import json
import sys
import time
import argparse

BASE_URL = "http://localhost:8001"
COURSE_ID = "233efed3-6f20-4f9c-a15a-1b3ee17118dd"  # Online Income Lab


def find_lessons_with_segments(node, lessons=None):
    """Recursively find all lessons that have segment children"""
    if lessons is None:
        lessons = []

    if node.get("type") == "folder":
        has_segments = any(child.get("type") == "segment" for child in node.get("children", []))
        if has_segments:
            lessons.append({
                "id": node["id"],
                "name": node["name"],
                "segments": [child for child in node.get("children", []) if child.get("type") == "segment"]
            })

    for child in node.get("children", []):
        find_lessons_with_segments(child, lessons)

    return lessons


def regenerate_lesson_embeddings(lesson, course_name, dry_run=False):
    """Regenerate embeddings for all segments in a lesson"""
    lesson_id = lesson["id"]
    lesson_name = lesson["name"]
    segments = lesson["segments"]

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing: {lesson_name}")
    print(f"  Lesson ID: {lesson_id}")
    print(f"  Segments to process: {len(segments)}")
    print()

    if dry_run:
        print(f"  [DRY RUN] Would call API to regenerate {len(segments)} embeddings")
        return len(segments), 0

    print(f"  Calling regeneration API...")

    try:
        response = requests.post(
            f"{BASE_URL}/api/admin/lessons/{lesson_id}/regenerate-embeddings",
            timeout=120  # Allow 2 minutes for embedding generation
        )

        if response.status_code == 200:
            data = response.json()
            success_count = data.get("segments_created", 0)
            message = data.get("message", "")
            print(f"  ✓ {message}")
            print(f"  Created {success_count} knowledge items")
            return success_count, 0
        else:
            error_msg = response.json().get("detail", "Unknown error")
            print(f"  ❌ API Error: {error_msg}")
            return 0, len(segments)

    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout: Embedding generation took too long")
        print(f"     This may happen with many segments. Try smaller batches.")
        return 0, len(segments)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return 0, len(segments)


def main():
    parser = argparse.ArgumentParser(description="Regenerate embeddings for missing knowledge items")
    parser.add_argument("--lesson-id", help="Specific lesson ID to process")
    parser.add_argument("--all", action="store_true", help="Process all lessons with missing items")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without doing it")
    args = parser.parse_args()

    if not args.lesson_id and not args.all:
        print("Error: Must specify either --lesson-id or --all")
        parser.print_help()
        sys.exit(1)

    print("=" * 80)
    print(f"{'[DRY RUN] ' if args.dry_run else ''}REGENERATE EMBEDDINGS FOR MISSING KNOWLEDGE ITEMS")
    print("=" * 80)
    print()

    # Get course tree
    print("📊 Fetching course tree...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/courses/{COURSE_ID}/tree")
        response.raise_for_status()
        data = response.json()
        course = data["course"]
        course_name = course["name"]
        print(f"   ✓ Loaded course: {course_name}")
    except Exception as e:
        print(f"   ❌ Failed to fetch course tree: {e}")
        sys.exit(1)

    # Find lessons with segments
    lessons = find_lessons_with_segments(course)

    if args.lesson_id:
        # Filter to specific lesson
        lessons = [l for l in lessons if l["id"] == args.lesson_id]
        if not lessons:
            print(f"\n❌ Lesson ID {args.lesson_id} not found or has no segments")
            sys.exit(1)

    print(f"\n📝 Found {len(lessons)} lesson(s) to process")

    # Process each lesson
    total_success = 0
    total_fail = 0

    for lesson in lessons:
        success, fail = regenerate_lesson_embeddings(lesson, course_name, args.dry_run)
        total_success += success
        total_fail += fail

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Lessons processed: {len(lessons)}")
    print(f"✓ Knowledge items created: {total_success}")
    print(f"❌ Failed: {total_fail}")
    print()

    if total_success > 0:
        print("✅ SUCCESS! Embeddings have been regenerated.")
        print("   You can now search for these lessons in the Q&A tool.")
        print()

    if total_fail > 0:
        print("⚠️  Some lessons failed to process. Check the errors above for details.")
        print("   You may need to check the backend logs for more information.")


if __name__ == "__main__":
    main()
