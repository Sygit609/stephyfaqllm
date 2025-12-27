"""
Content Management Service
Handles CRUD operations for knowledge items with dual embeddings
"""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from app.services.llm_adapters import get_adapter
from supabase import Client


async def generate_dual_embeddings(text: str) -> tuple[List[float], List[float]]:
    """
    Generate both OpenAI and Gemini embeddings for a text

    Args:
        text: Text to embed

    Returns:
        Tuple of (openai_embedding, gemini_embedding)
    """
    openai_adapter = get_adapter("openai")
    gemini_adapter = get_adapter("gemini")

    # Generate embeddings in parallel
    import asyncio

    openai_emb, gemini_emb = await asyncio.gather(
        openai_adapter.generate_embedding(text), gemini_adapter.generate_embedding(text)
    )

    return openai_emb, gemini_emb


async def save_extracted_content(
    db: Client,
    qa_pairs: List[Dict[str, Any]],
    media_url: str,
    source_url: str,
    extracted_by: str,
    overall_confidence: float,
    raw_extraction: Dict[str, Any],
    content_type: str = "screenshot",
) -> Dict[str, Any]:
    """
    Save extracted content with parent-child structure

    Process:
    1. Create parent entry (screenshot metadata)
    2. Create child entries (individual Q&As) with dual embeddings
    3. Link children to parent via parent_id

    Args:
        db: Supabase client
        qa_pairs: List of Q&A dictionaries
        media_url: URL to the screenshot image
        source_url: Original Facebook post URL
        extracted_by: 'gemini-vision' or 'gpt4-vision'
        overall_confidence: Extraction confidence score
        raw_extraction: Raw API response for debugging
        content_type: Type of content (screenshot, facebook, etc.)

    Returns:
        Dict with parent_id and list of child_ids
    """
    # Create parent entry (the screenshot itself)
    parent_id = str(uuid4())
    parent_data = {
        "id": parent_id,
        "content_type": content_type,
        "question": f"Screenshot from {source_url}",
        "answer": f"Contains {len(qa_pairs)} Q&A pair(s)",
        "source_url": source_url,
        "media_url": media_url,
        "extracted_by": extracted_by,
        "extraction_confidence": float(overall_confidence),
        "raw_content": raw_extraction,
        "parent_id": None,  # This is the parent
        "date": datetime.utcnow().date().isoformat(),  # Required field
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        # No embeddings for parent (it's just metadata)
        "embedding_openai": None,
        "embedding_gemini": None,
    }

    # Insert parent
    parent_result = db.table("knowledge_items").insert(parent_data).execute()

    if not parent_result.data:
        raise Exception("Failed to create parent entry")

    # Create child entries for each Q&A pair
    child_ids = []

    for i, qa in enumerate(qa_pairs):
        question = qa.get("question", "")
        answer = qa.get("answer", "")
        tags = qa.get("tags", [])

        # Combine question and answer for embedding
        combined_text = f"{question}\n{answer}"

        # Generate dual embeddings
        openai_emb, gemini_emb = await generate_dual_embeddings(combined_text)

        # Create child entry
        child_id = str(uuid4())
        child_data = {
            "id": child_id,
            "content_type": content_type,
            "question": question,
            "answer": answer,
            "source_url": source_url,
            "media_url": media_url,
            "tags": tags if isinstance(tags, list) else [],  # Keep as array for PostgreSQL
            "extracted_by": extracted_by,
            "extraction_confidence": float(overall_confidence),
            "parent_id": parent_id,  # Link to parent
            "date": datetime.utcnow().date().isoformat(),  # Required field
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "embedding_openai": openai_emb,
            "embedding_gemini": gemini_emb,
        }

        # Insert child
        child_result = db.table("knowledge_items").insert(child_data).execute()

        if child_result.data:
            child_ids.append(child_id)
        else:
            # Log error but continue with other items
            print(f"Warning: Failed to insert Q&A pair {i+1}")

    return {"parent_id": parent_id, "child_ids": child_ids, "total_saved": len(child_ids)}


async def update_knowledge_item(
    db: Client,
    item_id: str,
    updates: Dict[str, Any],
    regenerate_embeddings: bool = False,
) -> bool:
    """
    Update an existing knowledge item

    Args:
        db: Supabase client
        item_id: UUID of the item to update
        updates: Dictionary of fields to update
        regenerate_embeddings: Whether to regenerate embeddings if question/answer changed

    Returns:
        True if successful
    """
    # Check if question or answer changed and embeddings should be regenerated
    if regenerate_embeddings and ("question" in updates or "answer" in updates):
        # Fetch current data to get question/answer
        result = db.table("knowledge_items").select("question,answer").eq("id", item_id).execute()

        if result.data:
            current = result.data[0]
            question = updates.get("question", current["question"])
            answer = updates.get("answer", current["answer"])

            # Generate new embeddings
            combined_text = f"{question}\n{answer}"
            openai_emb, gemini_emb = await generate_dual_embeddings(combined_text)

            updates["embedding_openai"] = openai_emb
            updates["embedding_gemini"] = gemini_emb

    # Add updated_at timestamp
    updates["updated_at"] = datetime.utcnow().isoformat()

    # Update in database
    result = db.table("knowledge_items").update(updates).eq("id", item_id).execute()

    return len(result.data) > 0


def list_content(
    db: Client,
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    page_size: int = 50,
    order_by: str = "created_at",
    order_desc: bool = True,
) -> Dict[str, Any]:
    """
    List knowledge items with filters and pagination

    Args:
        db: Supabase client
        filters: Dict of filters (content_type, extracted_by, min_confidence, has_parent)
        page: Page number (1-indexed)
        page_size: Items per page
        order_by: Field to sort by
        order_desc: Sort descending if True

    Returns:
        Dict with items, total_count, page, page_size
    """
    # Build query
    query = db.table("knowledge_items").select("*", count="exact")

    # Apply filters
    if filters:
        if "content_type" in filters:
            query = query.eq("content_type", filters["content_type"])

        if "extracted_by" in filters:
            query = query.eq("extracted_by", filters["extracted_by"])

        if "min_confidence" in filters:
            query = query.gte("extraction_confidence", filters["min_confidence"])

        if "has_parent" in filters:
            if filters["has_parent"]:
                query = query.not_.is_("parent_id", "null")
            else:
                query = query.is_("parent_id", "null")

        if "parent_id" in filters:
            query = query.eq("parent_id", filters["parent_id"])

    # Apply ordering
    if order_desc:
        query = query.order(order_by, desc=True)
    else:
        query = query.order(order_by, desc=False)

    # Apply pagination
    start = (page - 1) * page_size
    end = start + page_size - 1
    query = query.range(start, end)

    # Execute query
    result = query.execute()

    return {
        "items": result.data,
        "total_count": result.count,
        "page": page,
        "page_size": page_size,
        "total_pages": (result.count + page_size - 1) // page_size if result.count else 0,
    }


def delete_content(db: Client, item_id: str, delete_children: bool = True) -> Dict[str, Any]:
    """
    Delete a knowledge item

    If item is a parent and delete_children=True, cascade delete is handled by DB constraint

    Args:
        db: Supabase client
        item_id: UUID of the item to delete
        delete_children: If True and item is parent, delete children too (handled by CASCADE)

    Returns:
        Dict with success status and count of deleted items
    """
    # Check if item has children
    children_result = (
        db.table("knowledge_items").select("id").eq("parent_id", item_id).execute()
    )

    child_count = len(children_result.data) if children_result.data else 0

    # Delete the item (CASCADE will handle children if delete_children=True)
    result = db.table("knowledge_items").delete().eq("id", item_id).execute()

    deleted_count = 1 + (child_count if delete_children else 0)

    return {
        "success": len(result.data) > 0,
        "deleted_count": deleted_count,
        "had_children": child_count > 0,
    }


def get_content_by_id(db: Client, item_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single content item by ID

    Args:
        db: Supabase client
        item_id: UUID of the item

    Returns:
        Item dict or None if not found
    """
    result = db.table("knowledge_items").select("*").eq("id", item_id).execute()

    return result.data[0] if result.data else None


def get_children(db: Client, parent_id: str) -> List[Dict[str, Any]]:
    """
    Get all children of a parent item

    Args:
        db: Supabase client
        parent_id: UUID of the parent

    Returns:
        List of child items
    """
    result = (
        db.table("knowledge_items")
        .select("*")
        .eq("parent_id", parent_id)
        .order("created_at", desc=False)
        .execute()
    )

    return result.data if result.data else []
