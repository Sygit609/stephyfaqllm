"""
API Endpoints
All FastAPI route handlers
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    SearchRequest, SearchResponse, SourceMatch,
    AnswerRequest, AnswerResponse,
    QueryRequest, QueryResponse,
    FeedbackRequest, FeedbackResponse,
    MetricsResponse, ModelMetrics,
    RecentQueriesResponse, QueryLogEntry,
    HealthResponse
)
from app.services import search, web_search, generation, metrics
from app.core.config import settings, validate_api_keys
from app.core.database import get_db

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns API status and configuration
    """
    # Validate API keys
    api_keys = validate_api_keys()

    # Check database connection
    try:
        db = get_db()
        db_response = db.table("knowledge_items").select("id").limit(1).execute()
        db_connected = True
    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        database_connected=db_connected,
        api_keys_valid=api_keys,
        environment=settings.environment
    )


@router.post("/api/search", response_model=SearchResponse)
async def search_knowledge_base(request: SearchRequest):
    """
    Search the knowledge base without generating an answer
    Returns matched sources with relevance scores
    """
    try:
        # Perform hybrid search
        sources = await search.hybrid_search(
            query=request.query,
            provider=request.provider or settings.default_model_provider,
            limit=request.limit or settings.default_search_limit
        )

        # Classify intent (optional for search-only)
        intent = await search.classify_intent(
            query=request.query,
            provider=request.provider or settings.default_model_provider
        )

        # Detect recency
        recency_required = search.detect_recency_need(request.query)

        # Convert to SourceMatch models
        source_matches = [
            SourceMatch(
                id=str(s["id"]),
                question=s["question"],
                answer=s["answer"],
                category=s.get("category"),
                tags=s.get("tags", []),
                date=s.get("date"),
                source_url=s.get("source_url"),
                score=s["score"],
                match_type=s["match_type"]
            )
            for s in sources
        ]

        return SearchResponse(
            query=request.query,
            sources=source_matches,
            total_found=len(source_matches),
            provider=request.provider or settings.default_model_provider,
            intent=intent,
            recency_required=recency_required
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/api/answer", response_model=AnswerResponse)
async def generate_answer_from_sources(request: AnswerRequest):
    """
    Generate an answer given specific sources
    Useful for when sources are already known
    """
    try:
        # Generate answer from provided sources
        answer_text, metadata = await generation.generate_grounded_answer(
            query=request.query,
            sources=request.sources,
            provider=request.provider or settings.default_model_provider
        )

        # Convert sources to SourceMatch models
        source_matches = [
            SourceMatch(
                id=str(s.get("id", "")),
                question=s.get("question", ""),
                answer=s.get("answer", ""),
                category=s.get("category"),
                tags=s.get("tags", []),
                date=s.get("date"),
                source_url=s.get("source_url"),
                score=s.get("score", 0.0),
                match_type=s.get("match_type", "unknown")
            )
            for s in request.sources
        ]

        return AnswerResponse(
            query=request.query,
            answer=answer_text,
            sources_used=source_matches,
            provider=request.provider or settings.default_model_provider,
            metadata=metadata
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer generation error: {str(e)}")


@router.post("/api/query", response_model=QueryResponse)
async def query_with_search_and_answer(request: QueryRequest):
    """
    Main endpoint: Search + Answer generation in one call
    This is the primary endpoint for the frontend to use
    """
    try:
        provider = request.provider or settings.default_model_provider

        # Step 1: Classify intent
        intent = await search.classify_intent(request.query, provider)

        # Step 2: Detect recency
        recency_required = search.detect_recency_need(request.query)

        # Step 3: Hybrid search
        internal_sources = await search.hybrid_search(
            query=request.query,
            provider=provider,
            limit=request.search_limit or settings.default_search_limit
        )

        # Step 4: Determine if web search is needed
        web_search_result = None
        web_used = False

        if request.use_web_search:
            best_score = max([s.get("score", 0.0) for s in internal_sources], default=0.0)

            if web_search.should_use_web_search(intent, best_score):
                web_search_result = await web_search.search_tavily(
                    query=request.query,
                    max_results=3
                )
                web_used = web_search_result is not None

        # Step 5: Generate answer based on available sources
        if web_used and internal_sources:
            # Use both internal and web sources
            answer_text, gen_metadata = await generation.generate_hybrid_answer(
                query=request.query,
                internal_sources=internal_sources,
                web_results=web_search_result,
                provider=provider
            )
        elif web_used:
            # Use only web sources
            answer_text, gen_metadata = await generation.generate_with_web_sources(
                query=request.query,
                web_results=web_search_result,
                provider=provider
            )
        else:
            # Use only internal sources
            answer_text, gen_metadata = await generation.generate_grounded_answer(
                query=request.query,
                sources=internal_sources,
                provider=provider
            )

        # Step 6: Log the query
        query_id = await metrics.log_query(
            query_text=request.query,
            model_provider=provider,
            intent_type=intent,
            recency_required=recency_required,
            sources_found=internal_sources,
            web_search_used=web_used,
            web_search_results=web_search_result,
            answer_generated=answer_text,
            metadata=gen_metadata
        )

        # Step 7: Format response
        source_matches = [
            SourceMatch(
                id=str(s["id"]),
                question=s["question"],
                answer=s["answer"],
                category=s.get("category"),
                tags=s.get("tags", []),
                date=s.get("date"),
                source_url=s.get("source_url"),
                score=s["score"],
                match_type=s["match_type"]
            )
            for s in internal_sources
        ]

        return QueryResponse(
            query=request.query,
            answer=answer_text,
            sources=source_matches,
            web_search_used=web_used,
            web_results=web_search_result.get("results") if web_search_result else None,
            intent=intent,
            recency_required=recency_required,
            provider=provider,
            metadata=gen_metadata,
            query_id=query_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")


@router.post("/api/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit staff feedback on a generated answer
    Tracks ratings and edits for model comparison
    """
    try:
        success = await metrics.update_feedback(
            query_id=request.query_id,
            rating=request.rating,
            was_edited=request.was_edited,
            staff_notes=request.staff_notes
        )

        return FeedbackResponse(
            success=success,
            query_id=request.query_id,
            message="Feedback recorded successfully" if success else "Failed to record feedback"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback error: {str(e)}")


@router.get("/api/metrics", response_model=MetricsResponse)
async def get_model_metrics(days: int = 7):
    """
    Get model comparison metrics
    Shows performance stats for OpenAI vs Gemini
    """
    try:
        metrics_data = await metrics.get_metrics_comparison(days=days)

        model_metrics_list = [
            ModelMetrics(
                provider=m.get("model_provider", ""),
                total_queries=m.get("total_queries", 0),
                avg_latency_ms=m.get("avg_latency_ms"),
                total_cost_usd=float(m.get("total_cost_usd", 0.0)),
                avg_cost_per_query=float(m.get("avg_cost_per_query", 0.0)),
                avg_rating=float(m.get("avg_rating", 0.0)) if m.get("avg_rating") else None,
                edit_rate=float(m.get("edit_rate", 0.0)) if m.get("edit_rate") else None,
                web_searches=m.get("web_searches", 0)
            )
            for m in metrics_data.get("models", [])
        ]

        return MetricsResponse(
            period_days=days,
            models=model_metrics_list,
            total_queries=metrics_data.get("total_queries", 0)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics error: {str(e)}")


@router.get("/api/recent-queries", response_model=RecentQueriesResponse)
async def get_recent_query_history(limit: int = 100):
    """
    Get recent query history
    Useful for reviewing past interactions
    """
    try:
        queries_data = await metrics.get_recent_queries(limit=limit)

        query_entries = [
            QueryLogEntry(
                id=str(q.get("id", "")),
                query_text=q.get("query_text", ""),
                model_provider=q.get("model_provider", ""),
                intent_type=q.get("intent_type"),
                latency_ms=q.get("latency_ms"),
                cost_usd=float(q.get("cost_usd", 0.0)) if q.get("cost_usd") else None,
                staff_rating=q.get("staff_rating"),
                was_edited=q.get("was_edited", False),
                created_at=q.get("created_at")
            )
            for q in queries_data
        ]

        return RecentQueriesResponse(
            queries=query_entries,
            total=len(query_entries)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query history error: {str(e)}")
