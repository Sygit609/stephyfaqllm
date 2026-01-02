#!/usr/bin/env python3
"""
Create Online Income Lab Course Structure
Automatically builds the entire course hierarchy via API calls
"""

import requests
import json
import time

# API Configuration
BASE_URL = "http://localhost:8001"
COURSE_NAME = "Online Income Lab"
COURSE_DESCRIPTION = "Complete course structure for Online Income Lab"

# Course Structure from PDF
COURSE_STRUCTURE = {
    "START-HERE": {
        "children": [
            "Welcome",
            {
                "How-to-Navigate-Online-Income-Lab": {
                    "children": [
                        "Navigating-Courses-Lessons-and-Categories",
                        "Community-Access",
                        "Coaching-Calls-and-Support",
                        "Enable-Closed-Caption"
                    ]
                }
            },
            "A-Letter-to-Your-Future-Self",
            "Tax-Saving-Secrets-and-LLC-Setup"
        ]
    },
    "Path-A-Affiliate-Path": {
        "children": [
            "Affiliate-Marketing-Intro",
            "Affiliate-Program-Signup",
            {
                "Option-1-Funnel-Freedom": {
                    "children": [
                        "Step-1-Sign-Up-for-Funnel-Freedom",
                        "Step-2-Sign-Up-for-Domain",
                        "Step-3-Access-Affiliate-Funnel-Template",
                        "Step-4-Update-Bridge-Page",
                        "Step-5-Setup-Workflow"
                    ]
                }
            },
            {
                "Option-2-Systeme-io": {
                    "children": [
                        "Step-1-Sign-Up-for-Systeme-io",
                        "Step-2-Sign-Up-for-Domain",
                        "Step-3-Connect-Domain",
                        "Step-4-Check-DNS-Status",
                        "Step-5-Access-Affiliate-Funnel-Template",
                        "Step-6-Update-Bridge-Page",
                        "Step-7-Setup-Workflow"
                    ]
                }
            },
            "Access-Affiliate-Links",
            "Affiliate-Resources",
            "Top-Affiliates"
        ]
    },
    "Path-B-Owner-Mode": {
        "children": [
            {
                "Module-1-Craft-Offers-That-Sell-Themselves": {
                    "children": [
                        "Preview",
                        "Lesson-1-Identify-Your-Niche",
                        "Lesson-2-Market-Research",
                        "Lesson-2a-Two-Ways-to-Reach-Your-Audience",
                        "Lesson-2b-Craft-Survey-Questions-with-ChatGPT",
                        "Closing"
                    ]
                }
            },
            "Module-2-Automation-Alchemy",
            "Module-3-The-Affiliate-Marketing-Project",
            "Module-4-Social-Media-Selling",
            "Module-5-Launch-with-Masterclass",
            "Module-6-Millionaire-Mentality"
        ]
    },
    "File-Resources": {
        "children": []
    },
    "Materials": {
        "children": [
            "Download-Here"
        ]
    }
}


def create_course(name, description):
    """Create the main course"""
    url = f"{BASE_URL}/api/admin/courses"
    payload = {
        "name": name,
        "description": description,
        "thumbnail_url": None
    }

    print(f"Creating course: {name}")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    course_data = response.json()
    print(f"✓ Course created with ID: {course_data['id']}\n")
    return course_data['id']


def create_subfolder(parent_id, name, description=""):
    """Create a subfolder under a parent"""
    url = f"{BASE_URL}/api/admin/folders/{parent_id}/subfolder"
    payload = {
        "name": name,
        "description": description,
        "thumbnail_url": None
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()
    folder_data = response.json()
    return folder_data['id']


def create_structure_recursive(parent_id, structure, indent=0):
    """Recursively create folder structure"""
    prefix = "  " * indent

    if isinstance(structure, str):
        # Simple leaf node
        folder_id = create_subfolder(parent_id, structure)
        print(f"{prefix}✓ Created: {structure}")
        return

    if isinstance(structure, dict):
        # Node with children
        for name, content in structure.items():
            folder_id = create_subfolder(parent_id, name)
            print(f"{prefix}✓ Created: {name}")

            if "children" in content:
                for child in content["children"]:
                    create_structure_recursive(folder_id, child, indent + 1)

    if isinstance(structure, list):
        # List of children
        for item in structure:
            create_structure_recursive(parent_id, item, indent)


def main():
    print("=" * 70)
    print("ONLINE INCOME LAB - COURSE STRUCTURE BUILDER")
    print("=" * 70)
    print()

    try:
        # Step 1: Create the main course
        course_id = create_course(COURSE_NAME, COURSE_DESCRIPTION)

        # Step 2: Create all top-level modules and their nested structure
        for module_name, module_data in COURSE_STRUCTURE.items():
            print(f"Creating module: {module_name}")
            module_id = create_subfolder(course_id, module_name)
            print(f"  ✓ Created: {module_name}")

            # Create children if any
            if "children" in module_data:
                for child in module_data["children"]:
                    create_structure_recursive(module_id, child, indent=2)

            print()
            time.sleep(0.1)  # Small delay to avoid overwhelming the server

        print("=" * 70)
        print("✓ COURSE STRUCTURE CREATED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nCourse ID: {course_id}")
        print(f"Course Name: {COURSE_NAME}")
        print(f"\nView at: http://localhost:3002/admin/courses/{course_id}")
        print()

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
