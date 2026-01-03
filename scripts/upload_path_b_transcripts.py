#!/usr/bin/env python3
"""
Upload Path B SRT transcripts to Online Income Lab course

This script:
1. Creates modules (M1-M6) under Path-B-Owner-Mode
2. Creates lessons for each module based on SRT filenames
3. Uploads and processes each SRT file with auto-tagging
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from datetime import date
from functools import partial

# Force unbuffered output
print = partial(print, flush=True)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import get_db
from app.services.transcription import TranscriptionService
from app.services.content_manager import generate_dual_embeddings

# Configuration
SRT_FOLDER = "/Users/chenweisun/Documents/Stephy OIL Path B subtitles"
COURSE_ID = "233efed3-6f20-4f9c-a15a-1b3ee17118dd"
COURSE_NAME = "Online Income Lab"

# Module names based on typical course structure
MODULE_NAMES = {
    1: "Module 1 - Course Creation",
    2: "Module 2 - Automation Alchemy",
    3: "Module 3 - Traffic Generation",
    4: "Module 4 - Content Creation",
    5: "Module 5 - Launch Strategy",
    6: "Module 6 - Mindset & Growth"
}


def parse_srt_filename(filename: str) -> dict:
    """
    Parse SRT filename to extract module number, video number, and lesson name.
    Example: BM1_02_Lesson 1.srt -> {module: 1, video: 2, name: "Lesson 1"}
    """
    match = re.match(r'BM(\d+)_(\d+)_(.+)\.srt', filename)
    if match:
        return {
            "module": int(match.group(1)),
            "video": int(match.group(2)),
            "name": match.group(3).strip()
        }
    return None


def get_srt_files_by_module(folder: str) -> dict:
    """
    Get all SRT files organized by module number.
    Returns: {1: [file1, file2, ...], 2: [...], ...}
    """
    modules = {}

    for filename in sorted(os.listdir(folder)):
        if not filename.endswith('.srt'):
            continue

        parsed = parse_srt_filename(filename)
        if not parsed:
            print(f"  Warning: Could not parse filename: {filename}")
            continue

        module_num = parsed["module"]
        if module_num not in modules:
            modules[module_num] = []

        modules[module_num].append({
            "filename": filename,
            "filepath": os.path.join(folder, filename),
            "video_num": parsed["video"],
            "lesson_name": parsed["name"]
        })

    # Sort each module's files by video number
    for module_num in modules:
        modules[module_num].sort(key=lambda x: x["video_num"])

    return modules


async def create_module(db, course_id: str, module_num: int) -> str:
    """Create a module in the database and return its ID."""
    module_name = MODULE_NAMES.get(module_num, f"Module {module_num}")

    # Generate embeddings for module
    openai_emb, gemini_emb = await generate_dual_embeddings(f"{COURSE_NAME} - {module_name}")

    module_data = {
        "content_type": "video",
        "hierarchy_level": 2,  # Module level
        "course_id": course_id,
        "question": module_name,
        "answer": f"Module {module_num} of {COURSE_NAME} Path B",
        "date": date.today().isoformat(),
        "embedding_openai": openai_emb,
        "embedding_gemini": gemini_emb,
    }

    result = db.table("knowledge_items").insert(module_data).execute()
    return result.data[0]["id"]


async def create_lesson(db, course_id: str, module_id: str, lesson_name: str, video_num: int) -> str:
    """Create a lesson in the database and return its ID."""
    full_name = f"{video_num:02d} - {lesson_name}"

    # Generate embeddings for lesson
    openai_emb, gemini_emb = await generate_dual_embeddings(f"{COURSE_NAME} - {full_name}")

    lesson_data = {
        "content_type": "video",
        "hierarchy_level": 3,  # Lesson level
        "course_id": course_id,
        "module_id": module_id,
        "parent_id": module_id,
        "question": full_name,
        "answer": "",
        "date": date.today().isoformat(),
        "embedding_openai": openai_emb,
        "embedding_gemini": gemini_emb,
    }

    result = db.table("knowledge_items").insert(lesson_data).execute()
    return result.data[0]["id"]


async def upload_transcript(
    db,
    transcription_service: TranscriptionService,
    course_id: str,
    module_id: str,
    lesson_id: str,
    srt_filepath: str,
    lesson_name: str,
    module_name: str
) -> int:
    """Upload and process an SRT transcript file. Returns segment count."""

    # Read SRT file
    with open(srt_filepath, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    # Parse SRT into segments
    segments = transcription_service.parse_srt_to_segments(srt_content)

    if not segments:
        print(f"    Warning: No segments found in {srt_filepath}")
        return 0

    # Create transcript segments with auto-tagging
    created_ids = await transcription_service.create_transcript_segments(
        lesson_id=lesson_id,
        course_id=course_id,
        module_id=module_id,
        segments=segments,
        video_url=None,  # No video URL for now
        db=db,
        lesson_name=lesson_name,
        module_name=module_name,
        course_name=COURSE_NAME
    )

    return len(created_ids)


async def main():
    print("=" * 60)
    print("Path B Transcript Uploader")
    print("=" * 60)

    # Initialize services
    db = get_db()
    transcription_service = TranscriptionService()

    # Get SRT files organized by module
    print(f"\n📁 Scanning folder: {SRT_FOLDER}")
    modules = get_srt_files_by_module(SRT_FOLDER)

    total_files = sum(len(files) for files in modules.values())
    print(f"   Found {total_files} SRT files across {len(modules)} modules")

    for module_num in sorted(modules.keys()):
        print(f"   Module {module_num}: {len(modules[module_num])} videos")

    # Process each module
    total_segments = 0
    total_lessons = 0

    for module_num in sorted(modules.keys()):
        module_files = modules[module_num]
        module_name = MODULE_NAMES.get(module_num, f"Module {module_num}")

        print(f"\n📚 Creating Module {module_num}: {module_name}")

        # Create module
        module_id = await create_module(db, COURSE_ID, module_num)
        print(f"   Module ID: {module_id}")

        # Process each video/lesson in the module
        for file_info in module_files:
            lesson_name = file_info["lesson_name"]
            video_num = file_info["video_num"]
            filepath = file_info["filepath"]

            print(f"\n   📝 Lesson {video_num}: {lesson_name[:50]}...")

            # Create lesson
            lesson_id = await create_lesson(db, COURSE_ID, module_id, lesson_name, video_num)

            # Upload transcript with auto-tagging
            segment_count = await upload_transcript(
                db=db,
                transcription_service=transcription_service,
                course_id=COURSE_ID,
                module_id=module_id,
                lesson_id=lesson_id,
                srt_filepath=filepath,
                lesson_name=lesson_name,
                module_name=module_name
            )

            print(f"      ✅ Created {segment_count} segments (with AI tags)")
            total_segments += segment_count
            total_lessons += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 Upload Complete!")
    print(f"   Modules created: {len(modules)}")
    print(f"   Lessons created: {total_lessons}")
    print(f"   Segments created: {total_segments}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
