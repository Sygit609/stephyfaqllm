#!/usr/bin/env python3
"""
Add missing lessons to Module 1: Craft Offers That Sell Themselves
"""

import requests
import json

BASE_URL = "http://localhost:8001"
COURSE_ID = "233efed3-6f20-4f9c-a15a-1b3ee17118dd"

# Module 1 complete structure from PDF
MODULE1_LESSONS = [
    "Preview",
    "Lesson-1-Identify-Your-Niche",
    "Lesson-2-Market-Research",
    "Lesson-2a-Two-Ways-to-Reach-Your-Audience",
    "Lesson-2b-Craft-Survey-Questions-with-ChatGPT",
    "Lesson-2c-Market-Research-Through-Survey-Form",
    "Lesson-2d-Market-Research-Through-Zoom-Calls",
    "Closing-on-Lesson-2",
    "Lesson-3-Putting-Your-Course-Together",
    "Lesson-3a-Map-Out-Your-Course-Curriculum",
    "Lesson-3b-My-Recording-Gadgets",
    "Lesson-3c-Software-I-Use-To-Record-My-Course",
    "Lesson-3d-Course-Name-and-Price",
    "Lesson-3e-Putting-Your-Course-Together",
    "Closing-on-Lesson-3",
    "Lesson-4-Crafting-an-Irresistible-Offer"
]


def create_subfolder(parent_id, name):
    """Create a subfolder under a parent"""
    url = f"{BASE_URL}/api/admin/folders/{parent_id}/subfolder"
    payload = {
        "name": name,
        "description": "",
        "thumbnail_url": None
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()['id']


def get_course_tree():
    """Get the course tree"""
    url = f"{BASE_URL}/api/admin/courses/{COURSE_ID}/tree"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['course']


def find_module1(node):
    """Recursively find Module-1"""
    if 'Module-1-Craft-Offers-That-Sell-Themselves' in node.get('name', ''):
        return node
    for child in node.get('children', []):
        result = find_module1(child)
        if result:
            return result
    return None


def main():
    print("=" * 70)
    print("ADD MISSING LESSONS TO MODULE 1")
    print("=" * 70)
    print()

    # Get course tree
    print("Fetching course tree...")
    tree = get_course_tree()

    # Find Module-1
    module1 = find_module1(tree)
    if not module1:
        print("❌ Module-1-Craft-Offers-That-Sell-Themselves not found!")
        return 1

    print(f"✓ Found Module 1 (ID: {module1['id']})")
    print(f"  Current children: {len(module1['children'])}")

    # Get existing lesson names
    existing_names = {child['name'] for child in module1['children']}
    print(f"\n  Existing lessons:")
    for name in sorted(existing_names):
        print(f"    - {name}")

    # Find missing lessons
    missing_lessons = [lesson for lesson in MODULE1_LESSONS if lesson not in existing_names]

    if not missing_lessons:
        print("\n✓ All lessons already exist!")
        return 0

    print(f"\n  Missing lessons ({len(missing_lessons)}):")
    for lesson in missing_lessons:
        print(f"    - {lesson}")

    print(f"\nAdding {len(missing_lessons)} missing lessons...")

    for lesson_name in missing_lessons:
        try:
            lesson_id = create_subfolder(module1['id'], lesson_name)
            print(f"  ✓ Created: {lesson_name}")
        except Exception as e:
            print(f"  ❌ Failed to create {lesson_name}: {e}")

    print("\n" + "=" * 70)
    print("✓ DONE!")
    print("=" * 70)
    print(f"\nRefresh the page to see the new lessons")
    print(f"URL: http://localhost:3002/admin/courses/{COURSE_ID}")
    print()

if __name__ == "__main__":
    exit(main())
