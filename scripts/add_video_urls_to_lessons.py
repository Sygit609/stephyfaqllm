#!/usr/bin/env python3
"""
Add Video URLs to Path B Course Lessons

This script updates the media_url field for all Path B lessons
based on the SRT filename to URL mapping from the course platform.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import get_db

# Module IDs from the Path B upload
MODULE_IDS = {
    1: "12cfb10f-8443-4e90-ae38-1fa1bb8ca271",
    2: "ebe8c103-8a89-4696-8dcf-70e9d4730cc4",
    3: "9f1c13e8-f22a-4915-841f-99f14dfb35d7",
    4: "7eba1cb3-326a-4834-ac8f-7b818a518c53",
    5: "9b512d90-257c-4b80-9e0c-084c0114fe41",
    6: "82432e48-8d4d-4a42-85cd-08fd7fb3f209",
}

# URL mappings: (module_num, video_num) -> URL
# Extracted from the PDF provided by user
URL_MAPPINGS = {
    # Module 1 - Course Creation (16 videos)
    (1, 1): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/dff8638d-a7cc-4378-9874-71c39e10fbae?source=courses",
    (1, 2): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/e404002e-d3b4-41a0-8526-c5ef43304b8a?source=courses",
    (1, 3): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/e097619c-63d1-4d68-afce-5397852526dc?source=courses",
    (1, 4): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/8a9e3ec1-f02d-48e0-8809-0d558d0e60d0?source=courses",
    (1, 5): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/0b757316-6660-4f40-b160-a2eb9f392f55?source=courses",
    (1, 6): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/2ee5ee6f-9e8c-4b65-9723-548c45573eb8?source=courses",
    (1, 7): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/1f9e2a65-ffd5-476c-9f6e-01b1f3f53cce?source=courses",
    (1, 8): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/1b8441f7-b651-4272-9e9c-aba73f52531b?source=courses",
    (1, 9): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/61bbf6ae-e846-4942-833e-8e81575cc968?source=courses",
    (1, 10): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/379a7f09-a18e-4035-a8bf-bde0b97cda21?source=courses",
    (1, 11): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/230d392a-e86d-4bb5-858d-4ae1d1bbec99?source=courses",
    (1, 12): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/29698ff1-6e30-4c26-8377-9b95e250d1b6?source=courses",
    (1, 13): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/3f92f01c-bd24-4c49-92c2-5ac19be9ad0d?source=courses",
    (1, 14): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/3e88c3ee-fa16-49be-82d5-bd792f420137?source=courses",
    (1, 15): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/94dfb1eb-1eb7-428c-bb6b-6c62c59f1dc7?source=courses",
    (1, 16): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/3e2c8482-2b62-4f2d-aab5-aac92c1073ea?source=courses",

    # Module 2 - Automation Alchemy (13 videos)
    (2, 1): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/fed765fa-651a-4a23-8260-dc9b6a604ab9?source=courses",
    (2, 2): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/56589352-145c-4e52-9395-8d672cdeeed6?source=courses",
    (2, 3): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/c30339ad-b629-4eee-af05-64e132ad0671?source=courses",
    (2, 4): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/ad544cb5-87ce-4044-b73d-1b19482b838c?source=courses",
    (2, 5): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/ac350491-d73c-48db-9286-62fa62b3ee5c?source=courses",
    (2, 6): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/1dce0609-8e8a-4667-8da1-7531c6c8ffb1?source=courses",
    (2, 7): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/c646f91b-ba5a-413e-ad79-5bf49fa2cd8b?source=courses",
    (2, 8): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/969e37f5-b3e3-402c-a9d2-e37f947a5246?source=courses",
    (2, 9): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/0ea93d89-1696-4229-bbfb-858cde60b8a7?source=courses",
    (2, 10): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/e1710dd0-44c2-4825-94ca-3ea84a1489d8?source=courses",
    (2, 11): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/d7af3bbf-e8bc-43f9-81f8-d0bddde5d759?source=courses",
    (2, 12): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/98a2e792-32fd-4f8b-b7bd-14ba97da7668?source=courses",
    (2, 13): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/0286d41c-8df9-4dbc-965f-d39da0f0fd7e/posts/0187042a-134a-484a-838a-6e23bb2996ae?source=courses",

    # Module 3 - Traffic Generation (5 videos)
    (3, 1): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3b2ebbc0-f9f3-43b5-baf9-96d4201cb5b2/posts/9d5ed210-e8cc-4b60-a4fa-e3e5711aca47?source=courses",
    (3, 2): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3b2ebbc0-f9f3-43b5-baf9-96d4201cb5b2/posts/34d92d76-9f06-41b8-83b4-419b3a255c7b?source=courses",
    (3, 3): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3b2ebbc0-f9f3-43b5-baf9-96d4201cb5b2/posts/d4595f5e-83d6-4299-8a86-55c6ec69fc28?source=courses",
    (3, 4): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3b2ebbc0-f9f3-43b5-baf9-96d4201cb5b2/posts/5467f7c5-03ac-49bc-8831-8f7e24fe7e90?source=courses",
    (3, 5): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3b2ebbc0-f9f3-43b5-baf9-96d4201cb5b2/posts/1b208c05-c30e-457b-8f6d-38c6d9cd6322?source=courses",

    # Module 4 - Content Creation (22 videos)
    (4, 1): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/5038e83f-b508-4bce-b054-7f55d811a931?source=courses",
    (4, 2): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/0ae5060c-3049-49c3-af3d-cfb8122d31ed?source=courses",
    (4, 3): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/c78a6d94-40e4-4f61-b73b-fab652e78058a?source=courses",
    (4, 4): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/6313b554-e8d3-4525-86dd-1c8684266366?source=courses",
    (4, 5): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/3bd8d3d0-3a94-4a47-a0a8-a067ae953db0?source=courses",
    (4, 6): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/1685cac5-254d-43ea-89fa-22fc7705c84a?source=courses",
    (4, 7): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/dc775ef2-0379-42ac-92bf-819c83eb9e28?source=courses",
    (4, 8): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/41cdc369-ab9c-42a0-ba43-0c6d9bc3b07e?source=courses",
    (4, 9): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/fb6fa479-a7ed-4172-8543-49d3f4cf1c10?source=courses",
    (4, 10): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/941fb45e-6427-480d-b392-c72299a98efa?source=courses",
    (4, 11): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/2d8b2bc7-e43d-4087-867e-ea9b22a18c01?source=courses",
    (4, 12): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/9bffcc03-827f-41ac-af17-26383253b037?source=courses",
    (4, 13): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/9d75817a-5d4a-42e4-97a5-22ef6e2415aa?source=courses",
    (4, 14): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/3614c2ef-5435-48fe-8909-529209062c26?source=courses",
    (4, 15): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/16319919-fc9c-43b0-80d5-aa203fbf5a1f?source=courses",
    (4, 16): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/faf4f47a-cf96-4042-a82d-64a25ae6324c?source=courses",
    (4, 17): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/196a7957-2d5b-470d-99b3-53ba74697b53?source=courses",
    (4, 18): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/62a80c04-6dae-4991-9551-54455fed60e1?source=courses",
    (4, 19): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/708c21bc-889a-4c26-adeb-598859abe01a?source=courses",
    (4, 20): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/b8ff6b24-1d9d-429c-83c9-bc33d169ee6e?source=courses",
    (4, 21): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/20415f52-b98b-4736-a48c-db470406a830/posts/a8dba678-ea21-4883-9d89-0f495b10f602?source=courses",
    # Note: Module 4 has 22 lessons in upload but only 21 URLs in PDF - will check if BM4_17 has duplicate

    # Module 5 - Launch Strategy (11 videos)
    (5, 1): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/24459428-f077-46ce-a7ab-4265404ef56d?source=courses",
    (5, 2): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/331dd9d2-3f29-41f4-a22a-a5ccaf6c6247?source=courses",
    (5, 3): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/5e0bdaa3-2c72-49a6-b982-7dd2c85e70ae?source=courses",
    (5, 4): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/51cb8f26-c270-45e2-abf7-4d04ac9e66b9?source=courses",
    (5, 5): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/59ffe69b-ac13-41a1-b711-a318c808b9cf?source=courses",
    (5, 6): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/1987fc38-7a78-49de-be1d-68446d0c69e1?source=courses",
    (5, 7): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/d7768b16-d07e-4d71-ba75-a1a78cfeded7?source=courses",
    (5, 8): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/46e13509-b3de-48fb-8e40-d7089e019429?source=courses",
    (5, 9): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/13b52a8d-2f02-4108-a3f4-cf872a5d87e2?source=courses",
    (5, 10): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/964137b3-1fd7-425d-81e1-9a7e5e5f7545?source=courses",
    (5, 11): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/cc9d28ec-9b41-4d1b-8a47-174294961400/posts/61d94fa7-4ca3-476f-8cb3-ef596ea322b6?source=courses",

    # Module 6 - Mindset & Growth (3 videos)
    (6, 1): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/eea35126-79fd-4d4c-b949-fd565fc5306a/posts/eac48253-741b-4237-bdeb-34cee9bd1cba?source=courses",
    (6, 2): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/eea35126-79fd-4d4c-b949-fd565fc5306a/posts/54589d2a-b3da-41b8-b385-7624087cc5b5?source=courses",
    (6, 3): "https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/eea35126-79fd-4d4c-b949-fd565fc5306a/posts/1bc84030-bac9-470c-8db0-bc6f6e181495?source=courses",
}


def main():
    print("=" * 60)
    print("Adding Video URLs to Path B Lessons")
    print("=" * 60)

    db = get_db()
    updated_count = 0
    not_found = []

    for module_num, module_id in MODULE_IDS.items():
        print(f"\n📚 Module {module_num} ({module_id})")

        # Get all lessons for this module
        lessons = db.table("knowledge_items")\
            .select("id, question")\
            .eq("parent_id", module_id)\
            .eq("hierarchy_level", 4)\
            .execute()

        print(f"   Found {len(lessons.data)} lessons")

        for lesson in lessons.data:
            # Extract video number from lesson name (e.g., "01 - Module 1 Preview" -> 1)
            question = lesson["question"]
            try:
                video_num = int(question.split(" - ")[0])
            except (ValueError, IndexError):
                print(f"   ⚠️  Could not parse video number from: {question}")
                continue

            # Look up URL
            url = URL_MAPPINGS.get((module_num, video_num))

            if url:
                # Update the lesson with the video URL
                db.table("knowledge_items")\
                    .update({"media_url": url})\
                    .eq("id", lesson["id"])\
                    .execute()
                print(f"   ✅ Updated: {question[:50]}...")
                updated_count += 1
            else:
                print(f"   ❌ No URL for: {question}")
                not_found.append((module_num, video_num, question))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print(f"   Updated: {updated_count} lessons")
    print(f"   Not found: {len(not_found)} lessons")

    if not_found:
        print("\n   Missing URLs for:")
        for mod, vid, name in not_found:
            print(f"     Module {mod}, Video {vid}: {name}")

    print("=" * 60)


if __name__ == "__main__":
    main()
