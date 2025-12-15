"""
Metrics Service
Logs queries and tracks model performance
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from app.core.database import get_db


async def log_query(
    query_text: str,
    model_provider: str,
    intent_type: Optional[str],
    recency_required: bool,
    sources_found: List[Dict[str, Any]],
    web_search_used: bool,
    web_search_results: Optional[Dict[str, Any]],
    answer_generated: str,
    metadata: Dict[str, Any]
) -> str:
    """
    Log a query to the database for metrics tracking
    Args:
        query_text: The user's question
        model_provider: 'gemini' or 'openai'
        intent_type: 'internal', 'external', or 'both'
        recency_required: Whether query needed time-sensitive info
        sources_found: Matched sources from KB
        web_search_used: Whether web search was used
        web_search_results: Results from web search
        answer_generated: The generated answer
        metadata: Token counts, cost, latency from generation
    Returns:
        Query ID (UUID as string)
    """
    db = get_db()

    try:
        # Prepare data for insertion
        log_data = {
            "query_text": query_text,
            "model_provider": model_provider,
            "intent_type": intent_type,
            "recency_required": recency_required,
            "sources_found": sources_found,  # JSONB
            "web_search_used": web_search_used,
            "web_search_results": web_search_results,  # JSONB
            "answer_generated": answer_generated,
            "latency_ms": metadata.get("latency_ms"),
            "tokens_input": metadata.get("tokens_input"),
            "tokens_output": metadata.get("tokens_output"),
            "cost_usd": metadata.get("cost_usd"),
        }

        # Insert into query_logs table
        response = db.table("query_logs").insert(log_data).execute()

        if response.data and len(response.data) > 0:
            query_id = response.data[0]["id"]
            return str(query_id)
        else:
            raise Exception("Failed to get query ID from insert")

    except Exception as e:
        print(f"Error logging query: {e}")
        # Return a placeholder ID if logging fails (don't break the main flow)
        return "00000000-0000-0000-0000-000000000000"


async def update_feedback(
    query_id: str,
    rating: Optional[int] = None,
    was_edited: bool = False,
    staff_notes: Optional[str] = None
) -> bool:
    """
    Update query log with staff feedback
    Args:
        query_id: UUID of the query
        rating: Staff rating (1-5)
        was_edited: Whether staff edited the answer
        staff_notes: Optional feedback notes
    Returns:
        True if successful
    """
    db = get_db()

    try:
        # Prepare update data
        update_data = {
            "was_edited": was_edited
        }

        if rating is not None:
            update_data["staff_rating"] = rating

        if staff_notes is not None:
            update_data["staff_notes"] = staff_notes

        # Update the query log
        response = db.table("query_logs").update(
            update_data
        ).eq("id", query_id).execute()

        return len(response.data) > 0

    except Exception as e:
        print(f"Error updating feedback: {e}")
        return False


async def get_metrics_comparison(days: int = 7) -> Dict[str, Any]:
    """
    Get model comparison metrics from the view
    Args:
        days: Number of days to look back (used in view filter)
    Returns:
        Dict with metrics for each model provider
    """
    db = get_db()

    try:
        # Query the model_comparison view
        response = db.table("model_comparison").select("*").execute()

        metrics = {
            "period_days": days,
            "models": response.data,
            "total_queries": sum(m.get("total_queries", 0) for m in response.data)
        }

        return metrics

    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return {
            "period_days": days,
            "models": [],
            "total_queries": 0
        }


async def get_recent_queries(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent query history
    Args:
        limit: Maximum number of queries to return
    Returns:
        List of recent queries
    """
    db = get_db()

    try:
        # Query the recent_queries view
        response = db.table("recent_queries").select("*").limit(limit).execute()

        return response.data

    except Exception as e:
        print(f"Error fetching recent queries: {e}")
        return []
