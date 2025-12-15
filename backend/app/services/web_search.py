"""
Web Search Integration
Uses Tavily API for external web search
"""

from typing import Dict, List, Any, Optional
import httpx
from app.core.config import settings


async def search_tavily(
    query: str,
    max_results: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Search the web using Tavily API
    Args:
        query: Search query
        max_results: Maximum number of results to return
    Returns:
        Dict with search results or None if error/not configured
    """
    if not settings.tavily_api_key:
        print("Warning: Tavily API key not configured")
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "search_depth": "basic",
                    "include_answer": True,
                    "include_images": False,
                    "include_raw_content": False,
                    "max_results": max_results
                },
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "query": query,
                    "answer": data.get("answer", ""),
                    "results": [
                        {
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "content": result.get("content", ""),
                            "score": result.get("score", 0.0)
                        }
                        for result in data.get("results", [])
                    ]
                }
            else:
                print(f"Tavily API error: {response.status_code}")
                return None

    except Exception as e:
        print(f"Web search error: {e}")
        return None


def should_use_web_search(
    intent: str,
    best_internal_score: float
) -> bool:
    """
    Determine if web search should be used
    Args:
        intent: Query intent ('internal', 'external', 'both')
        best_internal_score: Best score from internal search
    Returns:
        True if web search should be used
    """
    # Always use web search for external queries
    if intent == "external":
        return True

    # Use web search for 'both' intent
    if intent == "both":
        return True

    # Use web search if internal results are poor
    if best_internal_score < settings.web_search_threshold:
        return True

    return False


async def search_with_fallback(
    query: str,
    internal_results: List[Dict[str, Any]],
    intent: str
) -> Dict[str, Any]:
    """
    Perform web search with fallback logic
    Args:
        query: Search query
        internal_results: Results from internal KB search
        intent: Query intent classification
    Returns:
        Dict with web_search_used flag and results
    """
    # Get best internal score
    best_score = max(
        [r.get("score", 0.0) for r in internal_results],
        default=0.0
    )

    # Check if web search is needed
    use_web = should_use_web_search(intent, best_score)

    if not use_web:
        return {
            "web_search_used": False,
            "web_results": None
        }

    # Perform web search
    web_results = await search_tavily(query)

    return {
        "web_search_used": True,
        "web_results": web_results
    }
