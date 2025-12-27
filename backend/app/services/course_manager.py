"""
Course Management Service
Handles CRUD operations for 4-level course hierarchy
"""

from typing import Optional, Dict, List
from uuid import uuid4
from datetime import date
from supabase import Client
from app.services.content_manager import generate_dual_embeddings


class CourseManagerService:
    """Service for managing course hierarchy (Course → Module → Lesson → Segments)"""

    async def create_course(
        self,
        name: str,
        description: str,
        thumbnail_url: Optional[str],
        db: Client
    ) -> str:
        """
        Create a new course (Level 1)

        Args:
            name: Course name
            description: Course description
            thumbnail_url: Optional thumbnail image URL
            db: Supabase client

        Returns:
            Created course ID
        """
        course_data = {
            "content_type": "video",
            "hierarchy_level": 1,
            "question": name,
            "answer": description,
            "media_thumbnail": thumbnail_url,
            "parent_id": None,
            "date": date.today().isoformat(),  # Required field from original schema
            # No embeddings for course level (only segments have embeddings)
        }

        result = db.table("knowledge_items").insert(course_data).execute()
        course_id = result.data[0]["id"]

        # Set course_id to self for quick filtering
        db.table("knowledge_items").update({"course_id": course_id}).eq("id", course_id).execute()

        return course_id

    async def create_module(
        self,
        course_id: str,
        name: str,
        description: str,
        db: Client
    ) -> str:
        """
        Create a new module (Level 2) under a course

        Args:
            course_id: Parent course UUID
            name: Module name
            description: Module description
            db: Supabase client

        Returns:
            Created module ID
        """
        module_data = {
            "content_type": "video",
            "hierarchy_level": 2,
            "parent_id": course_id,
            "course_id": course_id,
            "question": name,
            "answer": description,
            "date": date.today().isoformat(),  # Required field from original schema
            # No embeddings for module level
        }

        result = db.table("knowledge_items").insert(module_data).execute()
        module_id = result.data[0]["id"]

        # Set module_id to self
        db.table("knowledge_items").update({"module_id": module_id}).eq("id", module_id).execute()

        return module_id

    async def create_lesson(
        self,
        module_id: str,
        course_id: str,
        name: str,
        description: str,
        video_url: Optional[str],
        video_duration_seconds: Optional[int],
        video_platform: Optional[str],
        db: Client
    ) -> str:
        """
        Create a new lesson (Level 3) under a module

        Args:
            module_id: Parent module UUID
            course_id: Top-level course UUID
            name: Lesson name
            description: Lesson description
            video_url: URL to video file
            video_duration_seconds: Total video duration
            video_platform: Platform hosting the video (vimeo, youtube, etc.)
            db: Supabase client

        Returns:
            Created lesson ID
        """
        # Get module_id from parent module
        module_result = db.table("knowledge_items").select("module_id").eq("id", module_id).execute()
        if not module_result.data:
            raise ValueError(f"Module {module_id} not found")

        lesson_data = {
            "content_type": "video",
            "hierarchy_level": 3,
            "parent_id": module_id,
            "course_id": course_id,
            "module_id": module_result.data[0]["module_id"],
            "question": name,
            "answer": description,
            "media_url": video_url,
            "video_duration_seconds": video_duration_seconds,
            "video_platform": video_platform,
            "date": date.today().isoformat(),  # Required field from original schema
            # No embeddings for lesson level
        }

        result = db.table("knowledge_items").insert(lesson_data).execute()
        lesson_id = result.data[0]["id"]

        # Set lesson_id to self
        db.table("knowledge_items").update({"lesson_id": lesson_id}).eq("id", lesson_id).execute()

        return lesson_id

    async def get_course_tree(
        self,
        course_id: str,
        db: Client
    ) -> Dict:
        """
        Get complete course tree (Course → Modules → Lessons → Segments)

        Args:
            course_id: Course UUID
            db: Supabase client

        Returns:
            Nested dict representing the full course hierarchy
        """
        # Query all items in this course
        result = db.table("knowledge_items")\
            .select("*")\
            .eq("course_id", course_id)\
            .order("hierarchy_level", desc=False)\
            .order("created_at", desc=False)\
            .execute()

        if not result.data:
            raise ValueError(f"Course {course_id} not found")

        # Build hierarchical structure
        items_by_id = {item["id"]: item for item in result.data}

        # Find root course
        course = next((item for item in result.data if item["hierarchy_level"] == 1), None)
        if not course:
            raise ValueError(f"Course {course_id} has no root node")

        # Build tree recursively
        def build_tree(node: Dict) -> Dict:
            """Recursively build tree from flat structure"""
            children = [
                build_tree(item) for item in result.data
                if item.get("parent_id") == node["id"]
            ]

            return {
                "id": node["id"],
                "name": node["question"],
                "description": node["answer"],
                "type": self._get_type_from_level(node["hierarchy_level"]),
                "hierarchy_level": node["hierarchy_level"],
                "children": children,
                "metadata": {
                    "media_url": node.get("media_url"),
                    "media_thumbnail": node.get("media_thumbnail"),
                    "timecode_start": node.get("timecode_start"),
                    "timecode_end": node.get("timecode_end"),
                    "video_duration_seconds": node.get("video_duration_seconds"),
                    "transcript_language": node.get("transcript_language"),
                    "extraction_confidence": node.get("extraction_confidence"),
                    "created_at": node.get("created_at"),
                    "updated_at": node.get("updated_at"),
                }
            }

        return build_tree(course)

    async def clone_course(
        self,
        course_id: str,
        new_name: str,
        regenerate_embeddings: bool,
        db: Client
    ) -> str:
        """
        Clone an entire course with all children

        Args:
            course_id: Source course UUID
            new_name: Name for cloned course
            regenerate_embeddings: If True, regenerate embeddings for segments (slower, more expensive)
            db: Supabase client

        Returns:
            New course ID
        """
        # Get original course tree
        original_tree = await self.get_course_tree(course_id, db)

        # Get all items to clone
        result = db.table("knowledge_items")\
            .select("*")\
            .eq("course_id", course_id)\
            .order("hierarchy_level", desc=False)\
            .execute()

        # Map old IDs to new IDs
        id_mapping = {}

        # Clone items level by level
        for item in result.data:
            old_id = item["id"]
            new_id = str(uuid4())
            id_mapping[old_id] = new_id

            # Prepare cloned item data
            cloned_item = {
                "id": new_id,
                "content_type": item["content_type"],
                "hierarchy_level": item["hierarchy_level"],
                "question": new_name if item["hierarchy_level"] == 1 else item["question"],
                "answer": item["answer"],
                "media_url": item.get("media_url"),
                "media_thumbnail": item.get("media_thumbnail"),
                "timecode_start": item.get("timecode_start"),
                "timecode_end": item.get("timecode_end"),
                "video_duration_seconds": item.get("video_duration_seconds"),
                "transcript_language": item.get("transcript_language"),
                "transcript_format": item.get("transcript_format"),
                "video_platform": item.get("video_platform"),
                "extracted_by": item.get("extracted_by"),
                "extraction_confidence": item.get("extraction_confidence"),
                "tags": item.get("tags"),
                "source_url": item.get("source_url"),
            }

            # Map parent_id, course_id, module_id, lesson_id to new IDs
            if item.get("parent_id"):
                cloned_item["parent_id"] = id_mapping.get(item["parent_id"])

            if item.get("course_id"):
                cloned_item["course_id"] = id_mapping.get(item["course_id"])

            if item.get("module_id"):
                cloned_item["module_id"] = id_mapping.get(item["module_id"])

            if item.get("lesson_id"):
                cloned_item["lesson_id"] = id_mapping.get(item["lesson_id"])

            # Handle embeddings
            if item["hierarchy_level"] == 4:  # Segments have embeddings
                if regenerate_embeddings:
                    # Regenerate embeddings (more expensive, but fresh)
                    embeddings = await generate_dual_embeddings(item["question"] + " " + item["answer"])
                    cloned_item["embedding_openai"] = embeddings["openai"]
                    cloned_item["embedding_gemini"] = embeddings["gemini"]
                else:
                    # Copy existing embeddings (faster, cheaper)
                    cloned_item["embedding_openai"] = item.get("embedding_openai")
                    cloned_item["embedding_gemini"] = item.get("embedding_gemini")

            # Insert cloned item
            db.table("knowledge_items").insert(cloned_item).execute()

        # Return new course ID
        return id_mapping[course_id]

    async def update_folder(
        self,
        folder_id: str,
        updates: Dict,
        db: Client
    ) -> bool:
        """
        Update course/module/lesson metadata

        Args:
            folder_id: Item UUID to update
            updates: Dict with fields to update (name, description, thumbnail, etc.)
            db: Supabase client

        Returns:
            Success boolean
        """
        update_data = {}

        if "name" in updates:
            update_data["question"] = updates["name"]

        if "description" in updates:
            update_data["answer"] = updates["description"]

        if "thumbnail_url" in updates:
            update_data["media_thumbnail"] = updates["thumbnail_url"]

        if "video_url" in updates:
            update_data["media_url"] = updates["video_url"]

        if "video_duration_seconds" in updates:
            update_data["video_duration_seconds"] = updates["video_duration_seconds"]

        result = db.table("knowledge_items").update(update_data).eq("id", folder_id).execute()

        return len(result.data) > 0

    async def delete_folder(
        self,
        folder_id: str,
        db: Client
    ) -> Dict:
        """
        Delete folder (CASCADE automatically deletes children)

        Args:
            folder_id: Item UUID to delete
            db: Supabase client

        Returns:
            Dict with success status and count of deleted items
        """
        # Count children before deletion (for reporting)
        children_count = db.table("knowledge_items")\
            .select("id", count="exact")\
            .or_(f"parent_id.eq.{folder_id},course_id.eq.{folder_id}")\
            .execute()

        total_to_delete = children_count.count + 1  # +1 for the folder itself

        # Delete (CASCADE handles children automatically)
        db.table("knowledge_items").delete().eq("id", folder_id).execute()

        return {
            "success": True,
            "deleted_count": total_to_delete
        }

    async def get_course_stats(
        self,
        course_id: str,
        db: Client
    ) -> Dict:
        """
        Get statistics for a course

        Args:
            course_id: Course UUID
            db: Supabase client

        Returns:
            Dict with module_count, lesson_count, segment_count, total_duration_seconds
        """
        # Calculate manually (course_stats view approach had issues)
        items = db.table("knowledge_items").select("*").eq("course_id", course_id).execute()

        module_count = sum(1 for item in items.data if item["hierarchy_level"] == 2)
        lesson_count = sum(1 for item in items.data if item["hierarchy_level"] == 3)
        segment_count = sum(1 for item in items.data if item["hierarchy_level"] == 4)
        total_duration = sum(
            item.get("video_duration_seconds", 0)
            for item in items.data
            if item["hierarchy_level"] == 3
        )

        return {
            "module_count": module_count,
            "lesson_count": lesson_count,
            "segment_count": segment_count,
            "total_duration_seconds": total_duration
        }

    def _get_type_from_level(self, level: int) -> str:
        """Convert hierarchy level to type string"""
        type_map = {
            1: "course",
            2: "module",
            3: "lesson",
            4: "segment"
        }
        return type_map.get(level, "unknown")


# Singleton instance
course_manager = CourseManagerService()
