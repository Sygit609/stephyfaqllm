#!/usr/bin/env python3
"""
Add missing lessons to START-HERE and Path-A sections
"""

import requests
import time

BASE_URL = "http://localhost:8001"
COURSE_ID = "233efed3-6f20-4f9c-a15a-1b3ee17118dd"

# Lessons based on PDF screenshots
LESSONS_TO_ADD = {
    # START HERE section - already has structure, just missing items under How-to-Navigate
    "How-to-Navigate-Online-Income-Lab": [
        "Navigating-Courses-Lessons-and-Categories",
        "Community-Access",
        "Coaching-Calls-and-Support",
        "Enable-Closed-Caption"
    ],

    # Welcome lesson (from PDF page 1)
    "Welcome": [],  # This is a single video, no sub-lessons

    # Path A - Affiliate Path
    "Online-Income-Lab-Affiliate-Marketing-Intro": [],  # Single video
    "Signup-for-OIL-Affiliate-Program": [],  # Single video

    # Option 1: Funnel Freedom - already has 5 steps
    "Option-1-Funnel-Freedom": [
        "Step-1-Sign-Up-for-Funnel-Freedom",
        "Step-2-Sign-Up-for-your-Domain",
        "Step-3-Access-Your-Affiliate-Funnel-Template",
        "Step-4-Update-Your-Bridge-Page",
        "Step-5-Setup-Your-Workflow"
    ],

    # Option 2: Systeme.io - already has 7 steps
    "Option-2-Systeme-io": [
        "Step-1-Sign-Up-for-Systeme-io",
        "Step-2-Sign-Up-for-Your-Domain",
        "Step-3-Connect-Domain-to-Systeme-io",
        "Step-4-Check-DNS-Status",
        "Step-5-Access-Your-Affiliate-Funnel-Template",
        "Step-6-Update-Your-Bridge-Page",
        "Step-7-Setup-Your-Workflow"
    ],

    # Other Path A items
    "How-to-access-your-affiliate-links": [],
    "Affiliate-resources": [],
    "Top-Affiliate": []
}


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


def find_node_by_name(node, name_fragment):
    """Recursively find a node by name fragment"""
    if name_fragment in node.get('name', ''):
        return node
    for child in node.get('children', []):
        result = find_node_by_name(child, name_fragment)
        if result:
            return result
    return None


def main():
    print("=" * 70)
    print("ADD MISSING LESSONS TO START-HERE AND PATH-A")
    print("=" * 70)
    print()

    # Get course tree
    print("Fetching course tree...")
    tree = get_course_tree()
    print("✓ Course tree loaded\n")

    total_added = 0

    for folder_name, lessons in LESSONS_TO_ADD.items():
        if not lessons:  # Skip empty lesson lists
            continue

        print(f"\nProcessing: {folder_name}")
        print("-" * 70)

        # Find folder
        folder = find_node_by_name(tree, folder_name)
        if not folder:
            print(f"  ❌ Folder not found: {folder_name}")
            continue

        print(f"  ✓ Found folder (ID: {folder['id']})")
        print(f"  Current children: {len(folder['children'])}")

        # Get existing lesson names
        existing_names = {child['name'] for child in folder['children']}

        # Find missing lessons
        missing_lessons = [lesson for lesson in lessons if lesson not in existing_names]

        if not missing_lessons:
            print(f"  ✓ All {len(lessons)} lessons already exist!")
            continue

        print(f"  Adding {len(missing_lessons)} missing lessons...")

        for lesson_name in missing_lessons:
            try:
                lesson_id = create_subfolder(folder['id'], lesson_name)
                print(f"    ✓ {lesson_name}")
                total_added += 1
                time.sleep(0.05)
            except Exception as e:
                print(f"    ❌ Failed: {lesson_name} - {e}")

    print("\n" + "=" * 70)
    print(f"✓ COMPLETE! Added {total_added} lessons total")
    print("=" * 70)
    print(f"\nRefresh the page to see all new lessons")
    print(f"URL: http://localhost:3002/admin/courses/{COURSE_ID}")
    print()

if __name__ == "__main__":
    exit(main())
