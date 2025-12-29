"""
Answer Generation Service
Generates grounded answers using matched sources
"""

from typing import List, Dict, Any, Tuple
from app.services.llm_adapters import get_adapter


def format_video_citation(source: Dict[str, Any]) -> str:
    """
    Format video segment citation with clickable timestamp and full URL
    Args:
        source: Video segment source
    Returns:
        Formatted citation string
    """
    video_url = source.get('media_url', '')
    start_time = source.get('timecode_start', 0)
    end_time = source.get('timecode_end', 0)

    # Format timestamp as MM:SS
    start_mm = start_time // 60
    start_ss = start_time % 60
    mm_ss = f"{start_mm:02d}:{start_ss:02d}"

    # Create clickable URL with timestamp
    clickable_url = f"{video_url}?t={start_time}" if video_url else ""

    # Get lesson/module/course names if available (from question field)
    segment_title = source.get('question', '')
    transcript_text = source.get('answer', '')

    return (
        f"Watch at [{mm_ss}]({clickable_url})\n"
        f"Full video: {video_url}\n\n"
        f"Transcript: \"{transcript_text}\""
    )


def format_sources_for_prompt(sources: List[Dict[str, Any]]) -> str:
    """
    Format matched sources into context string for LLM
    Args:
        sources: List of matched source documents
    Returns:
        Formatted context string
    """
    if not sources:
        return "No relevant sources found in the knowledge base."

    context_parts = []
    for idx, source in enumerate(sources, 1):
        content_type = source.get("content_type", "")

        # Check if this is a video segment (has timecode)
        if source.get("timecode_start") is not None:
            # Video segment - format differently
            question = source.get("question", "")
            answer = source.get("answer", "")
            video_url = source.get("media_url", "")
            start_time = source.get("timecode_start", 0)

            # Format timestamp
            mm = start_time // 60
            ss = start_time % 60
            mm_ss = f"{mm:02d}:{ss:02d}"

            context_parts.append(
                f"[Video Source {idx}]\n"
                f"From: {question}\n"
                f"Timestamp: {mm_ss}\n"
                f"Video URL: {video_url}?t={start_time}\n"
                f"Full Video URL (for copy-paste): {video_url}\n"
                f"Transcript: {answer}\n"
            )
        else:
            # Regular Q&A source
            question = source.get("question", "")
            answer = source.get("answer", "")
            category = source.get("category", "")
            tags = source.get("tags", [])

            context_parts.append(
                f"[Source {idx}]\n"
                f"Category: {category}\n"
                f"Tags: {', '.join(tags) if tags else 'None'}\n"
                f"Q: {question}\n"
                f"A: {answer}\n"
            )

    return "\n---\n".join(context_parts)


def format_web_sources_for_prompt(web_results: Dict[str, Any]) -> str:
    """
    Format web search results into context string
    Args:
        web_results: Results from Tavily API
    Returns:
        Formatted context string
    """
    if not web_results or not web_results.get("results"):
        return "No relevant web sources found."

    context_parts = []

    # Add Tavily's direct answer if available
    if web_results.get("answer"):
        context_parts.append(
            f"[Web Summary]\n{web_results['answer']}\n"
        )

    # Add individual results
    for idx, result in enumerate(web_results.get("results", []), 1):
        title = result.get("title", "")
        content = result.get("content", "")
        url = result.get("url", "")

        context_parts.append(
            f"[Web Source {idx}]\n"
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Content: {content}\n"
        )

    return "\n---\n".join(context_parts)


async def generate_grounded_answer(
    query: str,
    sources: List[Dict[str, Any]],
    provider: str = "gemini"
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate answer grounded in provided sources
    Args:
        query: User's question
        sources: Matched sources from knowledge base
        provider: Model provider ('gemini' or 'openai')
    Returns:
        Tuple of (answer_text, metadata)
    """
    adapter = get_adapter(provider)

    # Format sources into context
    context = format_sources_for_prompt(sources)

    # System prompt emphasizing grounding and source citation
    system_prompt = """You are a helpful assistant for Online Income Lab (OIL) staff.

Your role is to help staff answer student questions by providing accurate, grounded responses based on the knowledge base.

IMPORTANT CITATION RULES:

1. For VIDEO SOURCES (those with timestamps):
   - MUST cite using: [Course - Module: Lesson](ACTUAL_VIDEO_URL?t=TIMESTAMP)
   - Use the EXACT "Video URL" provided in the source (e.g., the full URL like https://...)
   - Use the course/module/lesson names from the "From:" field
   - Example: [Course 3 - Module 2: Choosing the Right Niche](https://onlineincomelab.stephychen.com/...?t=3600)

2. For REGULAR Q&A SOURCES (those without video timestamps):
   - Cite these as: **[Source N](internal)** (with bold formatting)
   - The bold makes it easy for admins to spot and remove before sharing with students
   - Example: **[Source 1](internal)**, **[Source 2](internal)**

3. NEVER use placeholder text like "video_url" - always use the actual URL from "Video URL:" field

4. If sources don't fully answer the question, say so clearly
5. Be helpful and conversational, but stay factual
6. Synthesize information from multiple sources when appropriate
7. Maintain a friendly, supportive tone for student support

CRITICAL: For video sources, copy the EXACT URL from the "Video URL:" field in the source - never use placeholders!"""

    try:
        answer, metadata = await adapter.generate_answer(
            query=query,
            context=context,
            system_prompt=system_prompt
        )

        return answer, metadata

    except Exception as e:
        raise Exception(f"Answer generation error: {e}")


async def generate_with_web_sources(
    query: str,
    web_results: Dict[str, Any],
    provider: str = "gemini"
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate answer using web search results
    Args:
        query: User's question
        web_results: Results from Tavily web search
        provider: Model provider
    Returns:
        Tuple of (answer_text, metadata)
    """
    adapter = get_adapter(provider)

    # Format web results into context
    context = format_web_sources_for_prompt(web_results)

    # System prompt for external/web-based answers
    system_prompt = """You are a helpful assistant for Online Income Lab (OIL) staff.

The student's question requires external/web information. Use the provided web search results to answer.

IMPORTANT RULES:
1. Base your answer on the web search results provided
2. Cite your sources by mentioning the source titles or URLs
3. Be accurate and helpful
4. If the web results don't fully answer the question, acknowledge this
5. Maintain a helpful, professional tone

Format your answer clearly and provide source attribution."""

    try:
        answer, metadata = await adapter.generate_answer(
            query=query,
            context=context,
            system_prompt=system_prompt
        )

        return answer, metadata

    except Exception as e:
        raise Exception(f"Web answer generation error: {e}")


async def generate_hybrid_answer(
    query: str,
    internal_sources: List[Dict[str, Any]],
    web_results: Dict[str, Any],
    provider: str = "gemini"
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate answer using both internal and web sources
    Args:
        query: User's question
        internal_sources: Sources from knowledge base
        web_results: Web search results
        provider: Model provider
    Returns:
        Tuple of (answer_text, metadata)
    """
    adapter = get_adapter(provider)

    # Combine both contexts
    internal_context = format_sources_for_prompt(internal_sources)
    web_context = format_web_sources_for_prompt(web_results)

    combined_context = (
        "=== INTERNAL KNOWLEDGE BASE ===\n"
        f"{internal_context}\n\n"
        "=== WEB SEARCH RESULTS ===\n"
        f"{web_context}"
    )

    system_prompt = """You are a helpful assistant for Online Income Lab (OIL) staff.

You have access to both internal knowledge base sources AND external web information.

IMPORTANT RULES:
1. Prioritize internal knowledge base for OIL-specific information
2. Use web sources for general/technical information not in the KB
3. Clearly distinguish between internal and external information
4. Cite your sources appropriately
5. Synthesize information from both sources when helpful
6. Be accurate, helpful, and maintain a supportive tone

Format your answer clearly with appropriate source attribution."""

    try:
        answer, metadata = await adapter.generate_answer(
            query=query,
            context=combined_context,
            system_prompt=system_prompt
        )

        return answer, metadata

    except Exception as e:
        raise Exception(f"Hybrid answer generation error: {e}")
