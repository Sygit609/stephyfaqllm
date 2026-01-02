#!/usr/bin/env python3
"""
Diagnostic Script: Find Missing Knowledge Items
Identifies transcript segments in course_folders that are missing from knowledge_items
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8001"
COURSE_ID = "233efed3-6f20-4f9c-a15a-1b3ee17118dd"  # Online Income Lab


def count_segments_in_node(node):
    """Recursively count segments in a node"""
    count = 0
    if node.get("type") == "segment":
        count = 1
    for child in node.get("children", []):
        count += count_segments_in_node(child)
    return count


def find_lessons_with_segments(node, lessons=None):
    """Recursively find all lessons that have segment children"""
    if lessons is None:
        lessons = []

    # If this node is a folder with segment children, it's a lesson
    if node.get("type") == "folder":
        has_segments = any(child.get("type") == "segment" for child in node.get("children", []))
        if has_segments:
            segment_count = sum(1 for child in node.get("children", []) if child.get("type") == "segment")
            lessons.append({
                "id": node["id"],
                "name": node["name"],
                "segment_count": segment_count,
                "children": [child for child in node.get("children", []) if child.get("type") == "segment"]
            })

    # Recurse into children
    for child in node.get("children", []):
        find_lessons_with_segments(child, lessons)

    return lessons


def main():
    print("=" * 80)
    print("DIAGNOSTIC: MISSING KNOWLEDGE ITEMS")
    print("=" * 80)
    print()

    # Get course tree
    print("📊 Fetching course tree...")
    try:
        response = requests.get(f"{BASE_URL}/api/admin/courses/{COURSE_ID}/tree")
        response.raise_for_status()
        data = response.json()
        course = data["course"]
        print(f"   ✓ Loaded course: {course['name']}")
    except Exception as e:
        print(f"   ❌ Failed to fetch course tree: {e}")
        sys.exit(1)

    print()

    # Find all lessons with segments
    print("🔍 Analyzing lessons with transcripts...")
    lessons = find_lessons_with_segments(course)
    total_segments = sum(lesson["segment_count"] for lesson in lessons)
    print(f"   Found {len(lessons)} lessons with transcripts")
    print(f"   Total segments in course_folders: {total_segments}")
    print()

    # For each lesson, count knowledge_items
    print("🔍 Checking knowledge_items database...")
    lessons_with_issues = []
    total_knowledge_items = 0

    for lesson in lessons:
        # Count knowledge items by searching
        try:
            # Use search API to check if items exist
            # We'll use a more direct approach - check if lesson appears in search
            search_response = requests.post(
                f"{BASE_URL}/api/search",
                json={"query": lesson["name"], "provider": "openai", "limit": 100}
            )

            if search_response.status_code == 200:
                search_data = search_response.json()
                # Count how many results match this lesson by checking source_url or question
                knowledge_count = len([
                    s for s in search_data.get("sources", [])
                    if lesson["name"] in s.get("question", "")
                ])
                total_knowledge_items += knowledge_count
            else:
                knowledge_count = 0

        except Exception as e:
            print(f"   ⚠️  Error checking lesson {lesson['name']}: {e}")
            knowledge_count = 0

        if knowledge_count < lesson["segment_count"]:
            missing = lesson["segment_count"] - knowledge_count
            lessons_with_issues.append({
                **lesson,
                "knowledge_count": knowledge_count,
                "missing": missing
            })

    print(f"   Total knowledge_items found: {total_knowledge_items}")
    print()

    # Report results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    total_missing = sum(lesson["missing"] for lesson in lessons_with_issues)

    if total_missing == 0:
        print("✅ ALL GOOD! No obvious missing knowledge items found.")
        print(f"   All {len(lessons)} lessons appear to have knowledge items.")
        print()
        print("   Note: This script uses search API which may not be 100% accurate.")
        print("   If you're still having issues, the segments may have failed to generate embeddings.")
    else:
        print(f"⚠️  FOUND POTENTIAL ISSUES!")
        print(f"   Lessons analyzed: {len(lessons)}")
        print(f"   Lessons with issues: {len(lessons_with_issues)}")
        print(f"   Estimated missing knowledge items: {total_missing}")
        print()
        print("=" * 80)
        print("LESSONS WITH POTENTIAL MISSING KNOWLEDGE ITEMS")
        print("=" * 80)
        print()

        for issue in lessons_with_issues:
            print(f"📝 Lesson: {issue['name']}")
            print(f"   Lesson ID: {issue['id']}")
            print(f"   Segments in course_folders: {issue['segment_count']}")
            print(f"   Knowledge items found in search: {issue['knowledge_count']}")
            print(f"   Status: ❌ MISSING ~{issue['missing']} items")

            # Show first segment preview
            if issue['children']:
                first_segment = issue['children'][0]
                desc = first_segment.get('description', '')
                preview = desc[:100] + "..." if len(desc) > 100 else desc
                print(f"   Preview: {preview}")
            print()

        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print()
        print("To fix missing knowledge items, run:")
        print()
        for issue in lessons_with_issues:
            lesson_id = issue["id"]
            print(f"  python3 regenerate_embeddings.py --lesson-id {lesson_id}")
        print()
        print("Or regenerate all at once:")
        print("  python3 regenerate_embeddings.py --all")
        print()


if __name__ == "__main__":
    main()
