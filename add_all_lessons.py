#!/usr/bin/env python3
"""
Add all missing lessons to all modules based on PDF screenshot
"""

import requests
import time

BASE_URL = "http://localhost:8001"
COURSE_ID = "233efed3-6f20-4f9c-a15a-1b3ee17118dd"

# Complete course structure from PDF (all 4 pages)
ALL_LESSONS = {
    "Module-2-Automation-Alchemy": [
        "Preview",
        "Lesson-1-Building-Your-Sales-Funnel",
        "Lesson-1a-Setting-Up-Payment-with-Stripe",
        "Lesson-1b-How-to-Add-Payment-for-Your-Product",
        "Lesson-1c-Setup-Product-Payment-Inside-Sales-Funnel",
        "Lesson-1d-How-to-Follow-Up-with-Failed-Payment",
        "Lesson-2-Crafting-a-High-Converting-Sales-Page",
        "Lesson-3-Nurture-and-Convert-with-Emails",
        "Lesson-3a-Nurture-Email-Sequence",
        "Lesson-3b-Abandoned-Cart-Email",
        "Lesson-3c-Lining-Up-My-Emails",
        "Lesson-3-c-Bonus",
        "Lesson-4-Creating-a-Lead-Magnet"
    ],
    "Module-3-The-Affiliate-Marketing-Project": [
        "Preview",
        "Lesson-1-Choosing-the-Right-Company-and-Product",
        "Lesson-2-How-To-Earn",
        "Lesson-3-How-To-Scale",
        "Lesson-4-Affiliate-Stacking-Ecosystem"
    ],
    "Module-4-Social-Media-Selling": [
        "Preview",
        "Lesson-1-Optimizing-Your-Instagram-Profile",
        "Lesson-2-Content-That-Converts",
        "Lesson-2a-Content-Strategy-Quadrant",
        "Lesson-2b-Helpful-Tips-for-Growth",
        "Lesson-3-Building-Trust-and-Driving-Sales-with-Stories",
        "Lesson-4-Conversations-to-Conversions",
        "Lesson-4a-Building-DM-Automation",
        "Lesson-4b-DM-Bot-Responder",
        "Lesson-4c-Live-Chat-Tutorial",
        "Lesson-5-All-About-Faceless",
        "Lesson-6-Batching-Content",
        "Lesson-6a-The-Planning",
        "Lesson-6b-Recording-Quick-Reels",
        "Lesson-6c-Recording-Talking-Head",
        "Lesson-6d-Editing-Quick-Reels",
        "Lesson-6e-Editing-Talking-Head",
        "Lesson-6f-Text-On-Screen",
        "Lesson-6g-Caption",
        "Lesson-6h-Schedule-Posting",
        "Lesson-7-Metrics-That-Matter"
    ],
    "Module-5-Launch-with-Masterclass": [
        "Preview",
        "Lesson-1-Create-a-Winning-Outline",
        "Lesson-2-Setting-Up-Your-Masterclass",
        "Lesson-2a-Schedule-Your-Launch-Calendar",
        "Lesson-2b-Masterclass-Email-Sequence",
        "Lesson-2c-High-Converting-Masterclass-Registration-Page",
        "Lesson-2d-How-To-Connect-WebinarJam-to-Zapier",
        "Lesson-2e-Connecting-Funnel-Freedom-Registration-Page-to-Webinar",
        "Lesson-2f-Open-Cart-Audience-Smart-List-Setup",
        "Lesson-2g-WebinarJam-Tutorial",
        "Lesson-3-Building-Buzz-Before-the-Launch"
    ],
    "Module-6-Millionaire-Mentality": [
        "Preview",
        "Lesson-1-Shifting-Your-Identity",
        "Lesson-2-Celebrating-You"
    ]
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
    print("ADD ALL MISSING LESSONS TO ALL MODULES")
    print("=" * 70)
    print()

    # Get course tree
    print("Fetching course tree...")
    tree = get_course_tree()
    print("✓ Course tree loaded\n")

    total_added = 0

    for module_name, lessons in ALL_LESSONS.items():
        print(f"\nProcessing: {module_name}")
        print("-" * 70)

        # Find module
        module = find_node_by_name(tree, module_name)
        if not module:
            print(f"  ❌ Module not found: {module_name}")
            continue

        print(f"  ✓ Found module (ID: {module['id']})")
        print(f"  Current children: {len(module['children'])}")

        # Get existing lesson names
        existing_names = {child['name'] for child in module['children']}

        # Find missing lessons
        missing_lessons = [lesson for lesson in lessons if lesson not in existing_names]

        if not missing_lessons:
            print(f"  ✓ All {len(lessons)} lessons already exist!")
            continue

        print(f"  Adding {len(missing_lessons)} missing lessons...")

        for lesson_name in missing_lessons:
            try:
                lesson_id = create_subfolder(module['id'], lesson_name)
                print(f"    ✓ {lesson_name}")
                total_added += 1
                time.sleep(0.05)  # Small delay to avoid overwhelming server
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
