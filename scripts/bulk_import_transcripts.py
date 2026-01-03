"""
Bulk Import SRT Transcripts
Matches SRT files from a directory to lesson names in a course and uploads them
"""

import os
import asyncio
import sys
import requests
from pathlib import Path
from typing import List, Dict, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import get_db


def get_course_lessons(course_id: str) -> List[Dict]:
    """Get all lessons in a course with their IDs and names"""
    db = get_db()

    # Get the course and all its descendants
    # Start by getting course itself
    course_response = db.table("knowledge_items")\
        .select("id, question")\
        .eq("id", course_id)\
        .single()\
        .execute()

    if not course_response.data:
        print(f"Warning: Course {course_id} not found")
        return []

    # Get ALL items (not just folders) that could be children/descendants
    all_items_response = db.table("knowledge_items")\
        .select("id, question, content_type, hierarchy_level, parent_id")\
        .execute()

    # Build a tree structure to find all descendants
    all_items = all_items_response.data

    # Find all descendants of the course recursively
    def find_descendants(parent_id, all_items):
        descendants = []
        for item in all_items:
            if item.get("parent_id") == parent_id:
                descendants.append(item)
                # Recursively find children of this item
                descendants.extend(find_descendants(item["id"], all_items))
        return descendants

    course_descendants = find_descendants(course_id, all_items)

    # Return descendants that are likely lessons (content_type='video' and hierarchy_level == 3)
    lessons = []
    for item in course_descendants:
        # Only include items that look like lessons (not modules or transcript segments)
        # Lessons are hierarchy_level 3 (course=0, module=2, lesson=3, segment=4)
        if item.get("content_type") == "video" and item.get("hierarchy_level") == 3:
            lessons.append({
                "id": item["id"],
                "name": item["question"]
            })

    return lessons


def find_srt_files(directory: str) -> List[Tuple[str, str]]:
    """Find all SRT files in directory and return (filename_without_ext, full_path)"""
    srt_files = []
    for filename in os.listdir(directory):
        # Skip macOS hidden files (start with ._)
        if filename.startswith('._'):
            continue

        if filename.endswith('.srt'):
            name_without_ext = filename[:-4]  # Remove .srt extension
            full_path = os.path.join(directory, filename)
            srt_files.append((name_without_ext, full_path))

    return sorted(srt_files)


def match_files_to_lessons(srt_files: List[Tuple[str, str]], lessons: List[Dict]) -> Tuple[List[Dict], List[Tuple], List[Dict]]:
    """Match SRT files to lessons by name similarity"""
    matches = []
    unmatched_files = []
    unmatched_lessons = []

    for filename, filepath in srt_files:
        # Try exact match first
        matched = False
        for lesson in lessons:
            if filename == lesson["name"]:
                matches.append({
                    "lesson_id": lesson["id"],
                    "lesson_name": lesson["name"],
                    "srt_path": filepath,
                    "match_type": "exact"
                })
                matched = True
                break

        if not matched:
            # Try case-insensitive match
            for lesson in lessons:
                if filename.lower() == lesson["name"].lower():
                    matches.append({
                        "lesson_id": lesson["id"],
                        "lesson_name": lesson["name"],
                        "srt_path": filepath,
                        "match_type": "case_insensitive"
                    })
                    matched = True
                    break

        if not matched:
            # Try fuzzy match (similarity > 90%)
            # Normalize: remove brackets, underscores, extra spaces
            def normalize_name(name):
                return name.replace('[', '').replace(']', '').replace('_', ' ').strip().lower()

            filename_normalized = normalize_name(filename)
            for lesson in lessons:
                lesson_normalized = normalize_name(lesson["name"])

                # Calculate similarity (simple approach: count matching words)
                filename_words = set(filename_normalized.split())
                lesson_words = set(lesson_normalized.split())

                if filename_words and lesson_words:
                    common_words = filename_words & lesson_words
                    similarity = len(common_words) / max(len(filename_words), len(lesson_words))

                    if similarity > 0.90:  # 90% word match
                        matches.append({
                            "lesson_id": lesson["id"],
                            "lesson_name": lesson["name"],
                            "srt_path": filepath,
                            "match_type": f"fuzzy ({int(similarity*100)}%)"
                        })
                        matched = True
                        break

        if not matched:
            unmatched_files.append((filename, filepath))

    # Find lessons without matches
    matched_lesson_ids = {m["lesson_id"] for m in matches}
    unmatched_lessons = [l for l in lessons if l["id"] not in matched_lesson_ids]

    return matches, unmatched_files, unmatched_lessons


def upload_transcript(lesson_id: str, srt_path: str, api_base_url: str = "http://localhost:8001") -> Dict:
    """Upload SRT file to a lesson via API"""
    try:
        url = f"{api_base_url}/api/admin/lessons/{lesson_id}/upload-transcript"

        with open(srt_path, 'rb') as f:
            files = {'file': (os.path.basename(srt_path), f, 'text/plain')}
            response = requests.post(url, files=files)

        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "segments_created": result.get("segments_created", 0),
                "segment_ids": result.get("segment_ids", [])
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def bulk_import(course_id: str, srt_directory: str, dry_run: bool = True, api_base_url: str = "http://localhost:8001"):
    """
    Bulk import SRT files to course lessons

    Args:
        course_id: UUID of the course
        srt_directory: Path to directory containing SRT files
        dry_run: If True, only show what would be imported (don't actually import)
        api_base_url: Base URL of the API
    """
    print(f"\n{'='*60}")
    print(f"Bulk Import SRT Transcripts")
    print(f"{'='*60}\n")

    print(f"Course ID: {course_id}")
    print(f"SRT Directory: {srt_directory}")
    print(f"API Base URL: {api_base_url}")
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'LIVE IMPORT'}\n")

    # Step 1: Get all lessons in course
    print("Step 1: Fetching course lessons...")
    lessons = get_course_lessons(course_id)
    print(f"Found {len(lessons)} lessons in course\n")

    # Step 2: Find all SRT files
    print("Step 2: Finding SRT files...")
    srt_files = find_srt_files(srt_directory)
    print(f"Found {len(srt_files)} SRT files\n")

    # Step 3: Match files to lessons
    print("Step 3: Matching files to lessons...")
    matches, unmatched_files, unmatched_lessons = match_files_to_lessons(srt_files, lessons)
    print(f"Matched: {len(matches)}")
    print(f"Unmatched files: {len(unmatched_files)}")
    print(f"Unmatched lessons: {len(unmatched_lessons)}\n")

    # Show matches
    if matches:
        print(f"\n{'='*60}")
        print(f"MATCHES ({len(matches)})")
        print(f"{'='*60}\n")
        for i, match in enumerate(matches, 1):
            print(f"{i}. {match['lesson_name']}")
            print(f"   Match type: {match['match_type']}")
            print(f"   SRT file: {os.path.basename(match['srt_path'])}")
            print()

    # Show unmatched files
    if unmatched_files:
        print(f"\n{'='*60}")
        print(f"UNMATCHED FILES ({len(unmatched_files)})")
        print(f"{'='*60}\n")
        for filename, filepath in unmatched_files:
            print(f"- {filename}")
        print()

    # Show unmatched lessons
    if unmatched_lessons:
        print(f"\n{'='*60}")
        print(f"UNMATCHED LESSONS ({len(unmatched_lessons)})")
        print(f"{'='*60}\n")
        for lesson in unmatched_lessons:
            print(f"- {lesson['name']}")
        print()

    # If dry run, stop here
    if dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN COMPLETE - No files were imported")
        print("Run with --live to actually import")
        print(f"{'='*60}\n")
        return

    # Step 4: Import matched files
    if not matches:
        print("No matches to import!")
        return

    print(f"\n{'='*60}")
    print(f"IMPORTING {len(matches)} TRANSCRIPTS")
    print(f"{'='*60}\n")

    results = []
    for i, match in enumerate(matches, 1):
        print(f"[{i}/{len(matches)}] Uploading: {match['lesson_name']}")

        result = upload_transcript(match["lesson_id"], match["srt_path"], api_base_url)
        results.append({
            **match,
            **result
        })

        if result["success"]:
            print(f"   ✅ Success - {result['segments_created']} segments created")
        else:
            print(f"   ❌ Failed - {result['error']}")
        print()

    # Summary
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    total_segments = sum(r.get("segments_created", 0) for r in results if r["success"])

    print(f"\n{'='*60}")
    print("IMPORT COMPLETE")
    print(f"{'='*60}\n")
    print(f"Successful: {successful}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print(f"Total segments created: {total_segments}")
    print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Bulk import SRT transcripts to course lessons")
    parser.add_argument("course_id", help="UUID of the course")
    parser.add_argument("srt_directory", help="Path to directory containing SRT files")
    parser.add_argument("--live", action="store_true", help="Actually import (default is dry run)")
    parser.add_argument("--api-url", default="http://localhost:8001", help="API base URL")

    args = parser.parse_args()

    # Validate directory exists
    if not os.path.isdir(args.srt_directory):
        print(f"Error: Directory not found: {args.srt_directory}")
        sys.exit(1)

    # Run import
    dry_run = not args.live
    bulk_import(args.course_id, args.srt_directory, dry_run=dry_run, api_base_url=args.api_url)


if __name__ == "__main__":
    main()
