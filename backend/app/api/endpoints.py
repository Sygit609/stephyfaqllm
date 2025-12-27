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
    HealthResponse,
    ExtractScreenshotRequest, ExtractScreenshotResponse, QAPair,
    SaveContentRequest, SaveContentResponse,
    ContentListFilter, ContentListResponse, ContentItem,
    UpdateContentRequest, UpdateContentResponse
)
from app.services import search, web_search, generation, metrics
from app.services import vision_extractor, content_manager
from app.core.config import settings, validate_api_keys
from app.core.database import get_db
import base64

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


# ============================================================
# Admin Endpoints - Content Ingestion
# ============================================================


@router.post("/api/admin/extract-screenshot", response_model=ExtractScreenshotResponse)
async def extract_screenshot_qa(request: ExtractScreenshotRequest):
    """
    Extract Q&A pairs from screenshot using vision API
    Returns preview for user to review/edit before saving
    """
    try:
        # Decode base64 image
        try:
            image_data = base64.b64decode(request.image_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")

        # Extract Q&A using vision API with fallback
        result = await vision_extractor.extract_from_screenshot(
            image_data=image_data,
            source_url=request.source_url,
            use_fallback=request.use_fallback,
            confidence_threshold=0.7
        )

        # Convert to response format
        qa_pairs = [
            QAPair(
                question=qa.get("question", ""),
                answer=qa.get("answer", ""),
                tags=qa.get("tags", [])
            )
            for qa in result.qa_pairs
        ]

        return ExtractScreenshotResponse(
            qa_pairs=qa_pairs,
            confidence=result.confidence,
            model_used=result.model_used,
            used_fallback=result.used_fallback,
            warnings=result.warnings,
            metadata=result.metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")


@router.post("/api/admin/save-content", response_model=SaveContentResponse)
async def save_extracted_content(request: SaveContentRequest):
    """
    Save extracted (and possibly edited) Q&A content to knowledge base
    Generates dual embeddings for each Q&A pair
    """
    try:
        db = get_db()

        # Convert QAPair models to dicts
        qa_pairs_dict = [
            {
                "question": qa.question,
                "answer": qa.answer,
                "tags": qa.tags
            }
            for qa in request.qa_pairs
        ]

        # Save with parent-child structure
        result = await content_manager.save_extracted_content(
            db=db,
            qa_pairs=qa_pairs_dict,
            media_url=request.media_url,
            source_url=request.source_url,
            extracted_by=request.extracted_by,
            overall_confidence=request.confidence,
            raw_extraction=request.raw_extraction or {},
            content_type=request.content_type or "screenshot"
        )

        return SaveContentResponse(
            success=True,
            parent_id=result["parent_id"],
            child_ids=result["child_ids"],
            total_saved=result["total_saved"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save error: {str(e)}")


@router.get("/api/admin/content-list", response_model=ContentListResponse)
async def list_content_items(
    content_type: str = None,
    extracted_by: str = None,
    min_confidence: float = None,
    has_parent: bool = None,
    parent_id: str = None,
    page: int = 1,
    page_size: int = 50
):
    """
    List content items with filtering and pagination
    Useful for content management and review
    """
    try:
        db = get_db()

        # Build filters
        filters = {}
        if content_type:
            filters["content_type"] = content_type
        if extracted_by:
            filters["extracted_by"] = extracted_by
        if min_confidence is not None:
            filters["min_confidence"] = min_confidence
        if has_parent is not None:
            filters["has_parent"] = has_parent
        if parent_id:
            filters["parent_id"] = parent_id

        # Get content list
        result = content_manager.list_content(
            db=db,
            filters=filters,
            page=page,
            page_size=page_size
        )

        # Convert to ContentItem models
        content_items = [
            ContentItem(
                id=str(item["id"]),
                content_type=item["content_type"],
                question=item["question"],
                answer=item["answer"],
                source_url=item.get("source_url"),
                media_url=item.get("media_url"),
                tags=item.get("tags"),
                extracted_by=item.get("extracted_by"),
                extraction_confidence=item.get("extraction_confidence"),
                parent_id=str(item["parent_id"]) if item.get("parent_id") else None,
                created_at=item["created_at"],
                updated_at=item["updated_at"]
            )
            for item in result["items"]
        ]

        return ContentListResponse(
            items=content_items,
            total_count=result["total_count"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List content error: {str(e)}")


@router.delete("/api/admin/content/{item_id}")
async def delete_content_item(item_id: str):
    """
    Delete a content item
    If item is a parent, cascade delete children
    """
    try:
        db = get_db()

        result = content_manager.delete_content(
            db=db,
            item_id=item_id,
            delete_children=True
        )

        if not result["success"]:
            raise HTTPException(status_code=404, detail="Content item not found")

        return {
            "success": True,
            "message": f"Deleted {result['deleted_count']} item(s)",
            "deleted_count": result["deleted_count"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")


@router.put("/api/admin/content/{item_id}", response_model=UpdateContentResponse)
async def update_content_item(item_id: str, request: UpdateContentRequest):
    """
    Update a knowledge item
    Optionally regenerate embeddings if question/answer changed
    """
    try:
        db = get_db()

        # Build updates dictionary from non-None fields
        updates = {}
        if request.question is not None:
            updates["question"] = request.question
        if request.answer is not None:
            updates["answer"] = request.answer
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.source_url is not None:
            updates["source_url"] = request.source_url
        if request.content_type is not None:
            updates["content_type"] = request.content_type

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Update the item
        success = await content_manager.update_knowledge_item(
            db=db,
            item_id=item_id,
            updates=updates,
            regenerate_embeddings=request.regenerate_embeddings or False
        )

        if not success:
            raise HTTPException(status_code=404, detail="Content item not found")

        # Fetch updated item
        updated_item_data = content_manager.get_content_by_id(db, item_id)

        if not updated_item_data:
            raise HTTPException(status_code=404, detail="Content item not found after update")

        return UpdateContentResponse(
            success=True,
            message="Content updated successfully",
            updated_item=ContentItem(
                id=str(updated_item_data["id"]),
                content_type=updated_item_data["content_type"],
                question=updated_item_data["question"],
                answer=updated_item_data["answer"],
                source_url=updated_item_data.get("source_url"),
                media_url=updated_item_data.get("media_url"),
                tags=updated_item_data.get("tags"),
                extracted_by=updated_item_data.get("extracted_by"),
                extraction_confidence=updated_item_data.get("extraction_confidence"),
                parent_id=str(updated_item_data["parent_id"]) if updated_item_data.get("parent_id") else None,
                created_at=updated_item_data["created_at"],
                updated_at=updated_item_data["updated_at"]
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")
