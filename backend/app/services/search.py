"""
Search Service
Implements hybrid search combining vector and full-text search
"""

from typing import List, Dict, Any
from app.core.database import get_db
from app.core.config import settings
from app.services.llm_adapters import get_adapter


async def classify_intent(query: str, provider: str = "gemini") -> str:
    """
    Classify if query is about internal knowledge or external information
    Returns: 'internal', 'external', or 'both'
    """
    adapter = get_adapter(provider)

    system_prompt = """You are a query classifier. Determine if the user's question is about:
- INTERNAL: Questions about courses, community, support, specific tools/platforms mentioned in the knowledge base
- EXTERNAL: General knowledge questions, latest information, technical how-to questions
- BOTH: Questions that might need both internal and external information

Respond with ONLY one word: internal, external, or both"""

    try:
        # Use a simple prompt for classification
        answer, _ = await adapter.generate_answer(
            query=query,
            context="",
            system_prompt=system_prompt
        )

        intent = answer.strip().lower()
        if intent in ["internal", "external", "both"]:
            return intent
        return "internal"  # Default to internal if unclear

    except Exception as e:
        print(f"Intent classification error: {e}")
        return "internal"  # Default to internal on error


def detect_recency_need(query: str) -> bool:
    """
    Detect if query requires recent/time-sensitive information
    Returns: True if time-sensitive keywords found
    """
    time_keywords = [
        "today", "this week", "this month", "latest", "recent", "current",
        "zoom link", "meeting link", "upcoming", "next", "schedule",
        "when is", "what time", "now"
    ]

    query_lower = query.lower()
    return any(keyword in query_lower for keyword in time_keywords)


async def vector_search(
    embedding: List[float],
    provider: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search using embeddings
    Args:
        embedding: The query embedding vector
        provider: 'openai' or 'gemini' (determines which embedding field to use)
        limit: Maximum number of results
    Returns:
        List of matched items with scores
    """
    db = get_db()

    # Choose the correct embedding column based on provider
    embedding_column = f"embedding_{provider}"

    try:
        # Supabase vector search using RPC function
        # Note: We need to create a custom function for this, but for MVP
        # we'll use a simpler approach with manual distance calculation

        # Get all items (in production, you'd use pgvector's similarity search)
        response = db.table("knowledge_items").select(
            "id, question_raw, question_enriched, answer, category, tags, "
            f"date, source_url, {embedding_column}"
        ).limit(100).execute()

        items = response.data

        # Calculate cosine similarity manually (MVP approach)
        # In production, use pgvector's built-in operators
        import numpy as np
        import json

        def cosine_similarity(a, b):
            if not a or not b:
                return 0.0
            # Convert to numpy arrays to ensure proper types
            a_arr = np.array(a, dtype=np.float64)
            b_arr = np.array(b, dtype=np.float64)
            return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr)))

        results = []
        for item in items:
            item_embedding = item.get(embedding_column)
            if item_embedding:
                # Parse JSON string to array if needed
                if isinstance(item_embedding, str):
                    item_embedding = json.loads(item_embedding)
                score = cosine_similarity(embedding, item_embedding)
                results.append({
                    "id": item["id"],
                    "question": item["question_enriched"] or item["question_raw"],
                    "answer": item["answer"],
                    "category": item.get("category"),
                    "tags": item.get("tags", []),
                    "date": item.get("date"),
                    "source_url": item.get("source_url"),
                    "score": float(score),
                    "match_type": "vector"
                })

        # Sort by score and return top results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    except Exception as e:
        print(f"Vector search error: {e}")
        return []


async def fulltext_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Perform full-text search using Postgres tsvector
    Args:
        query: The search query
        limit: Maximum number of results
    Returns:
        List of matched items with scores
    """
    db = get_db()

    try:
        # Use keyword search with ilike (case-insensitive pattern matching)
        # For MVP, this is simpler than full postgres ts_search
        response = db.table("knowledge_items").select(
            "id, question_raw, question_enriched, answer, category, tags, "
            "date, source_url"
        ).or_(
            f"question_raw.ilike.%{query}%,question_enriched.ilike.%{query}%,answer.ilike.%{query}%"
        ).limit(limit).execute()

        results = []
        for idx, item in enumerate(response.data):
            # Assign scores based on rank (first result = highest score)
            score = 1.0 - (idx * 0.1)  # Simple scoring
            results.append({
                "id": item["id"],
                "question": item["question_enriched"] or item["question_raw"],
                "answer": item["answer"],
                "category": item.get("category"),
                "tags": item.get("tags", []),
                "date": item.get("date"),
                "source_url": item.get("source_url"),
                "score": max(0.1, score),  # Min score 0.1
                "match_type": "fulltext"
            })

        return results

    except Exception as e:
        print(f"Full-text search error: {e}")
        return []


async def hybrid_search(
    query: str,
    provider: str = "gemini",
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Hybrid search combining vector and full-text search
    Args:
        query: The search query
        provider: Model provider for embeddings
        limit: Maximum number of results
    Returns:
        List of unique matched items with combined scores
    """
    # Generate query embedding
    adapter = get_adapter(provider)

    try:
        embedding = await adapter.generate_embedding(query)
    except Exception as e:
        print(f"Embedding generation error: {e}")
        # Fallback to fulltext only
        return await fulltext_search(query, limit)

    # Perform both searches in parallel
    vector_results = await vector_search(embedding, provider, limit * 2)
    fulltext_results = await fulltext_search(query, limit * 2)

    # Combine results with weighted scoring
    combined = {}

    # Add vector results
    for result in vector_results:
        item_id = result["id"]
        combined[item_id] = result.copy()
        combined[item_id]["vector_score"] = result["score"]
        combined[item_id]["fulltext_score"] = 0.0
        combined[item_id]["match_type"] = "vector"

    # Add/merge fulltext results
    for result in fulltext_results:
        item_id = result["id"]
        if item_id in combined:
            # Item found in both searches
            combined[item_id]["fulltext_score"] = result["score"]
            combined[item_id]["match_type"] = "hybrid"
        else:
            # Item only in fulltext
            combined[item_id] = result.copy()
            combined[item_id]["vector_score"] = 0.0
            combined[item_id]["fulltext_score"] = result["score"]
            combined[item_id]["match_type"] = "fulltext"

    # Calculate weighted combined score
    for item_id in combined:
        vector_score = combined[item_id]["vector_score"]
        fulltext_score = combined[item_id]["fulltext_score"]

        combined[item_id]["score"] = (
            settings.hybrid_search_vector_weight * vector_score +
            settings.hybrid_search_fulltext_weight * fulltext_score
        )

    # Sort by combined score and return top results
    final_results = list(combined.values())
    final_results.sort(key=lambda x: x["score"], reverse=True)

    return final_results[:limit]
