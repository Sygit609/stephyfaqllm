"""
Answer Generation Service
Generates grounded answers using matched sources
"""

from typing import List, Dict, Any, Tuple, Optional
from app.services.llm_adapters import get_adapter


def build_admin_guidance_section(admin_input: Optional[str]) -> str:
    """
    Build admin guidance section for system prompt
    Args:
        admin_input: Optional admin guidance text
    Returns:
        Formatted admin guidance section (empty string if no input)
    """
    if not admin_input or not admin_input.strip():
        return ""

    return f"""
ADMIN GUIDANCE:
The coach/admin has provided the following guidance for answering this question:
"{admin_input.strip()}"

Please incorporate this guidance while maintaining accuracy and proper citation.
"""


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

    # Get lesson/module/course names if available (from question field)
    segment_title = source.get('question', '')
    transcript_text = source.get('answer', '')

    return (
        f"Video: {video_url}\n"
        f"Timestamp: {mm_ss}\n\n"
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
                f"Video URL: {video_url}\n"
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
    provider: str = "gemini",
    admin_input: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate answer grounded in provided sources
    Args:
        query: User's question
        sources: Matched sources from knowledge base
        provider: Model provider ('gemini' or 'openai')
        admin_input: Optional admin guidance to influence answer generation
    Returns:
        Tuple of (answer_text, metadata)
    """
    adapter = get_adapter(provider)

    # Format sources into context
    context = format_sources_for_prompt(sources)

    # Build admin guidance section
    admin_guidance = build_admin_guidance_section(admin_input)

    # System prompt emphasizing grounding and source citation
    system_prompt = f"""You are a helpful assistant for Online Income Lab (OIL) staff.

Your role is to help staff answer student questions by providing accurate, grounded responses based on the knowledge base.
{admin_guidance}

IMPORTANT CITATION RULES:

1. For VIDEO SOURCES (those with timestamps):
   - MUST cite using: [Course/Module/Lesson Name](COMPLETE_VIDEO_URL)
   - Copy the COMPLETE "Video URL" field from the source WITHOUT any abbreviation or truncation
   - DO NOT shorten URLs with "..." - use the FULL URL exactly as provided
   - DO NOT add timestamp parameters (?t= or &t=) to the URL - the timestamp is separate information
   - Include the timestamp as separate text: "at 12:34" or "Timestamp: 12:34"
   - Use the course/module/lesson names from the "From:" field
   - Example: [OIL 2 - Module 1: Choosing Your Niche](https://onlineincomelab.stephychen.com/courses/products/eb44e66c-cf32-4860-a47d-19878d09396a/categories/3437cbbc-514c-4c39-831d-ff4eb54a0bed/posts/e404002e-d3b4-41a0-8526-c5ef43304b8a?source=courses) at 01:00

2. For REGULAR Q&A SOURCES (those without video timestamps):
   - Cite these as: [Source N](internal) (NO bold formatting, NO asterisks)
   - Example: [Source 1](internal), [Source 2](internal)

3. DO NOT use placeholder text, abbreviations, or "..." in URLs
4. DO NOT append timestamp parameters to video URLs
4. If sources don't fully answer the question, say so clearly
5. Be helpful and conversational, but stay factual
6. Synthesize information from multiple sources when appropriate
7. Maintain a friendly, supportive tone for student support
8. DO NOT use em dashes (—) or fancy punctuation - use simple hyphens (-) or commas instead
9. Write in a natural, human-friendly way - avoid AI-sounding phrases

CRITICAL: Copy the COMPLETE "Video URL:" from the source - NO abbreviations, NO truncation, NO "..." - the FULL URL!"""

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
    provider: str = "gemini",
    admin_input: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate answer using web search results
    Args:
        query: User's question
        web_results: Results from Tavily web search
        provider: Model provider
        admin_input: Optional admin guidance to influence answer generation
    Returns:
        Tuple of (answer_text, metadata)
    """
    adapter = get_adapter(provider)

    # Format web results into context
    context = format_web_sources_for_prompt(web_results)

    # Build admin guidance section
    admin_guidance = build_admin_guidance_section(admin_input)

    # System prompt for external/web-based answers
    system_prompt = f"""You are a helpful assistant for Online Income Lab (OIL) staff.

The student's question requires external/web information. Use the provided web search results to answer.
{admin_guidance}

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
    provider: str = "gemini",
    admin_input: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate answer using both internal and web sources
    Args:
        query: User's question
        internal_sources: Sources from knowledge base
        web_results: Web search results
        provider: Model provider
        admin_input: Optional admin guidance to influence answer generation
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

    # Build admin guidance section
    admin_guidance = build_admin_guidance_section(admin_input)

    system_prompt = f"""You are a helpful assistant for Online Income Lab (OIL) staff.

You have access to both internal knowledge base sources AND external web information.
{admin_guidance}

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
