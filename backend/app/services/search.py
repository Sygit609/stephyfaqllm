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
    limit: int = 5,
    course_id: str = None
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search using native pgvector

    Args:
        embedding: The query embedding vector
        provider: 'openai' or 'gemini' (determines which RPC function to use)
        limit: Maximum number of results to return
        course_id: Optional course ID to filter results by specific course

    Returns:
        List of matched items with similarity scores
    """
    db = get_db()

    # Choose the correct RPC function based on provider
    rpc_function = f"vector_search_{provider}"

    # Determine batch limit (search more than we need for better quality)
    # For hybrid search, we fetch 2x to account for overlap with fulltext
    batch_limit = min(limit * 2, settings.vector_search_batch_limit)

    try:
        # Call native pgvector RPC function
        # This leverages IVFFlat indexes and returns pre-sorted results
        response = db.rpc(
            rpc_function,
            {
                "query_embedding": embedding,
                "match_limit": batch_limit,
                "filter_course_id": course_id
            }
        ).execute()

        items = response.data

        # Transform to consistent format
        results = []
        for item in items:
            result = {
                "id": item["id"],
                "question": item["question_enriched"] or item["question_raw"] or item.get("question", ""),
                "answer": item["answer"],
                "category": item.get("category"),
                "tags": item.get("tags") or [],
                "date": item.get("date"),
                "source_url": item.get("source_url"),
                "score": float(item["similarity"]),  # Already calculated by database
                "match_type": "vector",
                "content_type": item.get("content_type"),
                "media_url": item.get("media_url"),
                "timecode_start": item.get("timecode_start"),
                "timecode_end": item.get("timecode_end"),
                "course_id": item.get("course_id"),
                "module_id": item.get("module_id"),
                "lesson_id": item.get("lesson_id"),
            }
            results.append(result)

        # Results are already sorted by similarity (database does this)
        return results[:limit]

    except Exception as e:
        print(f"Vector search error: {e}")
        # Return empty results on error
        return []


async def fulltext_search(query: str, limit: int = 5, course_id: str = None) -> List[Dict[str, Any]]:
    """
    Perform full-text search using Postgres tsvector
    Args:
        query: The search query
        limit: Maximum number of results
        course_id: Optional course ID to filter results
    Returns:
        List of matched items with scores
    """
    db = get_db()

    try:
        # Extract important keywords from query (remove common words)
        stop_words = {
            'how', 'to', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'on', 'in', 'at', 'for', 'of', 'with',
            'do', 'does', 'did', 'can', 'could', 'would', 'should', 'will', 'what', 'when', 'where', 'why',
            'who', 'which', 'this', 'that', 'these', 'those', 'am', 'been', 'being', 'have', 'has', 'had',
            'from', 'by', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'use', 'get', 'make', 'go', 'see', 'know', 'take', 'find', 'give', 'tell', 'work', 'call',
            'try', 'ask', 'need', 'feel', 'become', 'leave', 'put', 'my', 'your', 'their', 'our', 'its'
        }
        keywords = [word.lower() for word in query.split() if word.lower() not in stop_words and len(word) > 2]

        # If we have keywords, search for each one
        if keywords:
            # Build OR condition for each keyword
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append(f"question.ilike.%{keyword}%")
                keyword_conditions.append(f"question_raw.ilike.%{keyword}%")
                keyword_conditions.append(f"question_enriched.ilike.%{keyword}%")
                keyword_conditions.append(f"answer.ilike.%{keyword}%")

            query_builder = db.table("knowledge_items").select(
                "id, question, question_raw, question_enriched, answer, category, tags, "
                "date, source_url, content_type, media_url, timecode_start, "
                "timecode_end, course_id, module_id, lesson_id"
            ).or_(",".join(keyword_conditions))
        else:
            # Fallback to original query if no keywords extracted
            query_builder = db.table("knowledge_items").select(
                "id, question, question_raw, question_enriched, answer, category, tags, "
                "date, source_url, content_type, media_url, timecode_start, "
                "timecode_end, course_id, module_id, lesson_id"
            ).or_(
                f"question.ilike.%{query}%,question_raw.ilike.%{query}%,question_enriched.ilike.%{query}%,answer.ilike.%{query}%"
            )

        # Apply course filter if specified
        if course_id:
            query_builder = query_builder.or_(f"course_id.eq.{course_id},course_id.is.null")

        response = query_builder.limit(limit).execute()

        results = []
        for idx, item in enumerate(response.data):
            # Assign scores based on rank (first result = highest score)
            score = 1.0 - (idx * 0.1)  # Simple scoring
            results.append({
                "id": item["id"],
                "question": item["question_enriched"] or item["question_raw"] or item.get("question", ""),
                "answer": item["answer"],
                "category": item.get("category"),
                "tags": item.get("tags") or [],
                "date": item.get("date"),
                "source_url": item.get("source_url"),
                "score": max(0.1, score),  # Min score 0.1
                "match_type": "fulltext",
                "content_type": item.get("content_type"),
                "media_url": item.get("media_url"),
                "timecode_start": item.get("timecode_start"),
                "timecode_end": item.get("timecode_end"),
                "course_id": item.get("course_id"),
                "module_id": item.get("module_id"),
                "lesson_id": item.get("lesson_id"),
            })

        return results

    except Exception as e:
        print(f"Full-text search error: {e}")
        return []


def parse_admin_search_directive(admin_input: str) -> Dict[str, Any]:
    """
    Parse admin input for search directives
    Returns dict with:
        - prioritize_courses: bool - whether to prioritize course content
        - course_only: bool - whether to search ONLY course content
        - instructor_filter: str | None - specific instructor name to filter by
    """
    if not admin_input:
        return {"prioritize_courses": False, "course_only": False, "instructor_filter": None}

    admin_lower = admin_input.lower()

    # Keywords that indicate course prioritization
    course_keywords = [
        "search the course", "check the course", "look in the course",
        "course first", "prioritize course", "from the course",
        "search course", "check course", "look in course",
        # More natural patterns for transcripts
        "share lessons", "use lessons", "from lessons",
        "share transcript", "use transcript", "from transcript",
        "check transcript", "look in transcript"
    ]

    # Keywords that indicate ONLY course content
    course_only_keywords = [
        "only the course", "just the course", "course only",
        "only course", "just course",
        # Transcript-specific
        "only transcript", "just transcript", "only lessons", "just lessons"
    ]

    prioritize_courses = any(keyword in admin_lower for keyword in course_keywords)
    course_only = any(keyword in admin_lower for keyword in course_only_keywords)

    # Extract instructor/course name from admin input
    instructor_filter = None

    # Pattern: "from [Name]" or "share [Name]" or "use [Name]"
    import re

    # Try to extract name after keywords
    # Matches patterns like:
    # - "share lessons from Nick Buhelos transcript"
    # - "use Sahil Segal course"
    # - "from [Mark Harbert]"
    name_patterns = [
        # Pattern 1: "from [Name]" where Name is 2+ capitalized words
        r'(?:from|share|use)\s+(?:lessons?\s+from\s+)?(?:transcript\s+from\s+)?(?:\[?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\]?)\s+(?:transcript|lessons?|course)',
        # Pattern 2: "[Name] transcript/lessons/course"
        r'(?:\[?([A-Z][a-z]+\s+[A-Z][a-z]+)\]?)\s+(?:transcript|lessons?|course)',
        # Pattern 3: Simple "from [Name]" without trailing keyword
        r'from\s+(?:\[?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\]?)\s*$',
    ]

    for pattern in name_patterns:
        match = re.search(pattern, admin_input, re.IGNORECASE)
        if match:
            instructor_filter = match.group(1).strip()
            # Also set prioritize if we found a specific instructor
            prioritize_courses = True
            break

    return {
        "prioritize_courses": prioritize_courses,
        "course_only": course_only,
        "instructor_filter": instructor_filter
    }


async def llm_rerank_results(
    query: str,
    results: List[Dict[str, Any]],
    provider: str = "gemini",
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Use LLM to rerank search results by relevance to query

    This provides true semantic understanding beyond keyword matching and embeddings.
    The LLM scores each result 0-10 based on how relevant it is to the user's intent.

    Args:
        query: User's search query
        results: Candidate results from hybrid search
        provider: LLM provider (gemini or openai)
        limit: Number of top results to return

    Returns:
        Reranked results with LLM relevance scores
    """
    import json
    import time

    if not results or len(results) == 0:
        return []

    # Limit the number of results we rerank to avoid token limits
    # We'll batch in groups of 20 for efficiency
    batch_size = 20
    results_to_rerank = results[:batch_size]

    # Build the prompt with result summaries
    results_text = ""
    for idx, result in enumerate(results_to_rerank, 1):
        question_preview = result.get("question", "")[:150]
        answer_preview = result.get("answer", "")[:250]

        results_text += f"{idx}. Title: {question_preview}\n"
        results_text += f"   Content: {answer_preview}\n\n"

    system_prompt = """You are a search relevance expert. Given a user query and a list of search results, score each result from 0-10 based on how relevant it is to the query.

Scoring guidelines:
- 9-10: Directly answers the query, highly relevant
- 7-8: Related to the topic, somewhat helpful
- 4-6: Tangentially related, low relevance
- 0-3: Completely irrelevant or off-topic

Return ONLY a valid JSON array of scores in order, like: [8.5, 2.0, 9.0, ...]
Do not include any explanation, just the JSON array."""

    user_prompt = f"""User Query: "{query}"

Results to score:
{results_text}

Return a JSON array of {len(results_to_rerank)} scores (one for each result)."""

    try:
        adapter = get_adapter(provider)
        start_time = time.time()

        # Use the adapter's generate_answer method
        # We pass user_prompt as both query and context for simplicity
        response_text, metadata = await adapter.generate_answer(
            query=user_prompt,
            context="",
            system_prompt=system_prompt,
            max_tokens=200  # Short response, just need scores
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Parse the JSON array of scores
        # Clean up the response to extract just the JSON array
        response_text = response_text.strip()

        # Try to find JSON array in response
        if '[' in response_text and ']' in response_text:
            start_idx = response_text.index('[')
            end_idx = response_text.rindex(']') + 1
            json_str = response_text[start_idx:end_idx]
            scores = json.loads(json_str)
        else:
            raise ValueError("No JSON array found in LLM response")

        # Validate we got the right number of scores
        if len(scores) != len(results_to_rerank):
            print(f"Warning: Expected {len(results_to_rerank)} scores, got {len(scores)}. Using original ranking.")
            return results[:limit]

        # Apply LLM scores to results
        for idx, result in enumerate(results_to_rerank):
            result["llm_relevance_score"] = float(scores[idx])
            result["original_score"] = result["score"]
            # Replace the score with LLM relevance score
            result["score"] = float(scores[idx])

        # Sort by LLM relevance score (descending)
        results_to_rerank.sort(key=lambda x: x["llm_relevance_score"], reverse=True)

        # Add any remaining results that weren't reranked (if there were more than batch_size)
        remaining_results = results[batch_size:]

        # Return top N reranked + remaining
        return results_to_rerank[:limit] + remaining_results[:max(0, limit - len(results_to_rerank))]

    except Exception as e:
        print(f"LLM reranking error: {e}")
        # Fall back to original ranking on error
        return results[:limit]


async def hybrid_search(
    query: str,
    provider: str = "gemini",
    limit: int = 5,
    course_id: str = None,
    admin_input: str = None
) -> List[Dict[str, Any]]:
    """
    Hybrid search combining vector and full-text search
    Args:
        query: The search query
        provider: Model provider for embeddings
        limit: Maximum number of results
        course_id: Optional course ID to filter results by specific course
        admin_input: Optional admin guidance for search behavior
    Returns:
        List of unique matched items with combined scores
    """
    # Parse admin search directive
    search_directive = parse_admin_search_directive(admin_input)

    # Generate query embedding
    adapter = get_adapter(provider)

    try:
        embedding = await adapter.generate_embedding(query)
    except Exception as e:
        print(f"Embedding generation error: {e}")
        # Fallback to fulltext only
        return await fulltext_search(query, limit, course_id)

    # Perform both searches in parallel
    # If instructor filter is specified, fetch MORE results to increase chance of finding matches
    # Otherwise use 3x to get enough results for both categories without pulling in low-quality matches
    batch_multiplier = 10 if search_directive.get("instructor_filter") else 3
    vector_results = await vector_search(embedding, provider, limit * batch_multiplier, course_id)

    # If instructor filter is specified, also do a keyword search for the instructor name
    if search_directive.get("instructor_filter"):
        instructor_name = search_directive["instructor_filter"]
        instructor_results = await fulltext_search(instructor_name, limit * batch_multiplier, course_id)
        # Combine with regular fulltext results
        fulltext_results = await fulltext_search(query, limit * batch_multiplier, course_id)
        # Merge instructor results with fulltext (instructor results will be scored higher)
        fulltext_results = instructor_results + fulltext_results
    else:
        fulltext_results = await fulltext_search(query, limit * batch_multiplier, course_id)

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

    # Default course content prioritization (applies to all users)
    # This ensures course transcripts appear before Facebook posts for students
    for item_id in combined:
        hierarchy_level = combined[item_id].get("hierarchy_level")

        # Strongly boost transcript segments (actual course content with video timestamps)
        if hierarchy_level == 4:
            combined[item_id]["score"] *= 3.0
        # Moderately boost other course-related content (course/module/lesson metadata)
        elif combined[item_id].get("course_id") is not None:
            combined[item_id]["score"] *= 1.5

    # Apply admin-guided course prioritization
    if search_directive["course_only"]:
        # Filter to ONLY course content (has course_id)
        final_results = [
            item for item in combined.values()
            if item.get("course_id") is not None
        ]
    elif search_directive["prioritize_courses"]:
        # Boost course content scores by 50%
        for item_id in combined:
            if combined[item_id].get("course_id") is not None:
                combined[item_id]["score"] *= 1.5
        final_results = list(combined.values())
    else:
        final_results = list(combined.values())

    # Apply instructor filter if specified
    instructor_filter = search_directive.get("instructor_filter")
    if instructor_filter:
        # First, try to find matching results
        matching_results = [
            item for item in final_results
            if instructor_filter.lower() in item.get("question", "").lower()
        ]

        if matching_results:
            # If we found matching results, boost their scores massively and use them
            for item in matching_results:
                item["score"] *= 10.0  # Massive boost for instructor-specific content
            final_results = matching_results
        else:
            # If no results match the instructor filter, we need to search more broadly
            # This happens when the query doesn't semantically match the transcript content
            # So we'll keep all course results but boost them anyway
            # (The prioritize_courses flag already boosted by 1.5x)
            pass

    # Sort by combined score (initial ranking)
    final_results.sort(key=lambda x: x["score"], reverse=True)

    # LLM reranking for better semantic relevance (NEW - USP: Search with AI)
    # This uses LLM to understand query intent and score results for true relevance
    # Helps prevent issues like "capcut" queries returning finance content
    if settings.enable_llm_reranking and len(final_results) > 0:
        # Rerank with LLM - fetch 3x limit to ensure we have enough for categorization
        final_results = await llm_rerank_results(
            query=query,
            results=final_results,
            provider=provider,
            limit=limit * 3
        )

    # Separate results into course content and non-course content for tab optimization
    # This ensures each tab (Course Transcripts, Facebook Posts) gets its own top N results
    course_results = [
        item for item in final_results
        if item.get("course_id") is not None or item.get("content_type") in ["video", "manual"]
    ]

    facebook_results = [
        item for item in final_results
        if item.get("content_type") == "facebook" or
           (item.get("course_id") is None and item.get("content_type") not in ["video", "manual"])
    ]

    # Return top N from each category (course results first, then Facebook)
    # Frontend tabs will filter by content_type, so each tab gets optimized results
    return course_results[:limit] + facebook_results[:limit]
