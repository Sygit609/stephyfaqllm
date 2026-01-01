"""
API Endpoints
All FastAPI route handlers
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
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
    UpdateContentRequest, UpdateContentResponse,
    GenerateTagsRequest, GenerateTagsResponse,
    ParseThreadRequest, ParseThreadResponse, ParsedQAPair,
    CreateFolderRequest, CreateCourseRequest, CreateModuleRequest, CreateLessonRequest,
    TranscribeRequest, TranscriptionResponse,
    UploadVideoResponse, UploadTranscriptResponse,
    Segment, UpdateSegmentRequest,
    CloneCourseRequest, CloneCourseResponse,
    CourseTreeNode, CourseTreeResponse,
    Course, CourseListResponse,
    Folder, UpdateFolderRequest, DeleteFolderResponse,
    CourseStatsResponse
)
from app.services import search, web_search, generation, metrics
from app.services import vision_extractor, content_manager
from app.services.transcription import transcription_service
from app.services.course_manager import course_manager
from app.core.config import settings, validate_api_keys
from app.core.database import get_db
import base64
import io

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
        admin_input = request.admin_input  # Extract admin input

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
                provider=provider,
                admin_input=admin_input  # Pass admin input
            )
        elif web_used:
            # Use only web sources
            answer_text, gen_metadata = await generation.generate_with_web_sources(
                query=request.query,
                web_results=web_search_result,
                provider=provider,
                admin_input=admin_input  # Pass admin input
            )
        else:
            # Use only internal sources
            answer_text, gen_metadata = await generation.generate_grounded_answer(
                query=request.query,
                sources=internal_sources,
                provider=provider,
                admin_input=admin_input  # Pass admin input
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


@router.post("/api/admin/generate-tags", response_model=GenerateTagsResponse)
async def generate_tags_for_qa(request: GenerateTagsRequest):
    """
    Generate AI tags for a Q&A pair
    Uses LLM to extract relevant topic tags from question and answer
    """
    try:
        # Use OpenAI adapter for tag generation (Gemini quota exceeded)
        from app.services.llm_adapters import get_adapter

        adapter = get_adapter("openai")

        # Create prompt for tag generation
        system_prompt = """You are a tag generation assistant for an online business education platform (Online Income Lab).

Your task is to extract 3-5 concise, relevant tags from Q&A pairs.

RULES:
1. Return ONLY tags, one per line
2. Tags should be business/niche topics (e.g., "pricing", "digital products", "niche selection")
3. Be specific but concise (2-3 words max per tag)
4. Focus on the main topics, not minor details
5. Use lowercase
6. No special characters or punctuation
7. Avoid generic tags like "business" or "online"

Example:
Q: How do I price my digital product?
A: Focus on value-based pricing...

Good tags:
digital product pricing
value-based pricing
pricing strategy

Bad tags:
business
online
how to price things"""

        user_prompt = f"""Generate tags for this Q&A:

Question: {request.question}

Answer: {request.answer}

Return only the tags, one per line."""

        # Generate tags
        response, _ = await adapter.generate_answer(
            query=user_prompt,
            context="",
            system_prompt=system_prompt
        )

        # Parse tags from response
        tags = [
            tag.strip().lower()
            for tag in response.strip().split('\n')
            if tag.strip() and len(tag.strip()) > 2
        ]

        # Limit to 5 tags
        tags = tags[:5]

        return GenerateTagsResponse(tags=tags)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tag generation error: {str(e)}")


@router.post("/api/admin/parse-thread", response_model=ParseThreadResponse)
async def parse_thread(request: ParseThreadRequest):
    """
    Parse Facebook thread with AI classification

    Extracts Q&A pairs from full thread text, classifies as meaningful vs filler,
    generates tags for meaningful content, and preserves thread hierarchy.
    """
    try:
        from app.services.thread_parser import parse_facebook_thread, validate_parsed_qa

        # Parse thread with LLM
        qa_pairs, metadata = await parse_facebook_thread(
            thread_text=request.thread_text,
            source_url=request.source_url,
            provider=request.provider or "openai"
        )

        # Validate and clean parsed Q&As
        validated_pairs = []
        for qa in qa_pairs:
            if await validate_parsed_qa(qa):
                validated_pairs.append(qa)
            else:
                print(f"Warning: Skipping invalid Q&A: {qa}")

        # Count classifications
        meaningful_count = sum(1 for qa in validated_pairs if qa.get("classification") == "meaningful")
        filler_count = sum(1 for qa in validated_pairs if qa.get("classification") == "filler")

        return ParseThreadResponse(
            qa_pairs=validated_pairs,
            total_parsed=len(validated_pairs),
            meaningful_count=meaningful_count,
            filler_count=filler_count,
            metadata=metadata
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Thread parsing error: {str(e)}")


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


# ============================================================
# Course Transcript Management Endpoints
# ============================================================


@router.post("/api/admin/courses", response_model=Course)
async def create_course(request: CreateCourseRequest):
    """Create a new course (Level 1)"""
    try:
        db = get_db()
        course_id = await course_manager.create_course(
            name=request.name,
            description=request.description,
            thumbnail_url=request.thumbnail_url,
            db=db
        )

        # Fetch created course with stats
        course_data = db.table("knowledge_items").select("*").eq("id", course_id).single().execute()
        stats = await course_manager.get_course_stats(course_id, db)

        return Course(
            id=course_id,
            name=course_data.data["question"],
            description=course_data.data["answer"],
            thumbnail_url=course_data.data.get("media_thumbnail"),
            module_count=stats.get("module_count", 0),
            lesson_count=stats.get("lesson_count", 0),
            segment_count=stats.get("segment_count", 0),
            total_duration_seconds=stats.get("total_duration_seconds", 0),
            created_at=course_data.data["created_at"],
            updated_at=course_data.data["updated_at"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Course creation error: {str(e)}")


@router.get("/api/admin/courses", response_model=CourseListResponse)
async def list_courses():
    """List all courses with statistics"""
    try:
        db = get_db()

        # Get all root folders (hierarchy_level = 1)
        # Support both old "video" and new "folder" content types for backwards compatibility
        courses_data = db.table("knowledge_items")\
            .select("*")\
            .eq("hierarchy_level", 1)\
            .in_("content_type", ["video", "folder"])\
            .order("created_at", desc=True)\
            .execute()

        courses = []
        for course_data in courses_data.data:
            stats = await course_manager.get_course_stats(course_data["id"], db)

            courses.append(Course(
                id=course_data["id"],
                name=course_data["question"],
                description=course_data["answer"],
                thumbnail_url=course_data.get("media_thumbnail"),
                module_count=stats.get("module_count", 0),
                lesson_count=stats.get("lesson_count", 0),
                segment_count=stats.get("segment_count", 0),
                total_duration_seconds=stats.get("total_duration_seconds", 0),
                created_at=course_data["created_at"],
                updated_at=course_data["updated_at"]
            ))

        return CourseListResponse(
            courses=courses,
            total_count=len(courses)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List courses error: {str(e)}")


@router.get("/api/admin/courses/{course_id}/tree", response_model=CourseTreeResponse)
async def get_course_tree(course_id: str):
    """Get complete course tree with all modules, lessons, and segments"""
    try:
        db = get_db()
        tree = await course_manager.get_course_tree(course_id, db)

        return CourseTreeResponse(course=tree)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get course tree error: {str(e)}")


@router.post("/api/admin/folders/{parent_id}/subfolder", response_model=Folder)
async def create_subfolder(parent_id: str, request: CreateFolderRequest):
    """Create a new subfolder under any folder (generic)"""
    try:
        db = get_db()
        folder_id = await course_manager.create_folder(
            name=request.name,
            description=request.description,
            parent_id=parent_id,
            thumbnail_url=request.thumbnail_url,
            db=db
        )

        # Fetch created folder
        folder_data = db.table("knowledge_items").select("*").eq("id", folder_id).single().execute()

        return Folder(
            id=folder_id,
            name=folder_data.data["question"],
            description=folder_data.data["answer"],
            type="folder",
            parent_id=folder_data.data.get("parent_id"),
            metadata={
                "hierarchy_level": folder_data.data.get("hierarchy_level"),
                "content_type": folder_data.data.get("content_type"),
                "media_thumbnail": folder_data.data.get("media_thumbnail"),
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Folder creation error: {str(e)}")


@router.post("/api/admin/courses/{course_id}/modules", response_model=Folder)
async def create_module(course_id: str, request: CreateModuleRequest):
    """Create a new module (Level 2) under a course - LEGACY, use /folders/{id}/subfolder instead"""
    try:
        db = get_db()
        module_id = await course_manager.create_module(
            course_id=course_id,
            name=request.name,
            description=request.description,
            db=db
        )

        # Fetch created module
        module_data = db.table("knowledge_items").select("*").eq("id", module_id).single().execute()

        return Folder(
            id=module_id,
            name=module_data.data["question"],
            description=module_data.data["answer"],
            type="folder",
            parent_id=module_data.data.get("parent_id"),
            metadata={}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Module creation error: {str(e)}")


@router.post("/api/admin/modules/{module_id}/lessons", response_model=Folder)
async def create_lesson(module_id: str, request: CreateLessonRequest):
    """Create a new lesson (Level 3) under a module"""
    try:
        db = get_db()

        # Get module to find course_id
        module_data = db.table("knowledge_items").select("course_id").eq("id", module_id).single().execute()
        course_id = module_data.data["course_id"]

        lesson_id = await course_manager.create_lesson(
            module_id=module_id,
            course_id=course_id,
            name=request.name,
            description=request.description,
            video_url=request.video_url,
            video_duration_seconds=None,
            video_platform=request.video_platform,
            db=db
        )

        # Fetch created lesson
        lesson_data = db.table("knowledge_items").select("*").eq("id", lesson_id).single().execute()

        return Folder(
            id=lesson_id,
            name=lesson_data.data["question"],
            description=lesson_data.data["answer"],
            type="lesson",
            parent_id=lesson_data.data.get("parent_id"),
            metadata={
                "video_url": lesson_data.data.get("media_url"),
                "video_platform": lesson_data.data.get("video_platform"),
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lesson creation error: {str(e)}")


@router.post("/api/admin/lessons/{lesson_id}/upload-video", response_model=UploadVideoResponse)
async def upload_video(lesson_id: str, file: UploadFile = File(...)):
    """Upload video file (to be stored in Supabase Storage or similar)"""
    try:
        # TODO: Implement video upload to Supabase Storage
        # For MVP, return a placeholder response
        raise HTTPException(
            status_code=501,
            detail="Video upload not yet implemented. Please provide external video URL when creating lesson."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video upload error: {str(e)}")


@router.post("/api/admin/lessons/{lesson_id}/transcribe", response_model=TranscriptionResponse)
async def transcribe_lesson(lesson_id: str, request: TranscribeRequest):
    """Transcribe lesson video using Whisper API"""
    try:
        db = get_db()

        # Get lesson data
        lesson_data = db.table("knowledge_items").select("*").eq("id", lesson_id).single().execute()
        if not lesson_data.data:
            raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")

        video_url = lesson_data.data.get("media_url")
        if not video_url:
            raise HTTPException(status_code=400, detail="Lesson has no video URL")

        # TODO: Download video from URL to pass to Whisper
        # For now, this will fail - need to implement video download
        raise HTTPException(
            status_code=501,
            detail="Automatic transcription not yet implemented. Please upload .srt/.vtt file manually."
        )

        # Code for when video download is implemented:
        # video_file = download_video(video_url)
        # transcription = await transcription_service.transcribe_video(video_file, request.language)
        # segments = transcription_service.parse_srt_to_segments(transcription["srt_text"], request.segment_duration)
        # segment_ids = await transcription_service.create_transcript_segments(...)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")


@router.post("/api/admin/lessons/{lesson_id}/upload-transcript", response_model=UploadTranscriptResponse)
async def upload_transcript(lesson_id: str, file: UploadFile = File(...)):
    """Upload manual transcript file (.srt or .vtt)"""
    try:
        db = get_db()

        # Get folder data (new structure)
        folder_result = db.table("knowledge_items").select("*").eq("id", lesson_id).single().execute()
        if not folder_result.data:
            raise HTTPException(status_code=404, detail=f"Folder {lesson_id} not found")

        folder_data = folder_result.data
        folder_name = folder_data.get("question", "")
        video_url = folder_data.get("media_url", "")

        # Get course_id and video_url by traversing up the tree
        # Video URL might be on parent folder if not set on current folder
        course_id = None
        parent_id = folder_data.get("parent_id")
        current_level = folder_data.get("hierarchy_level", 1)

        # If already at course level, use current ID
        if current_level == 1:
            course_id = lesson_id
        else:
            # Traverse up to find course (level 1) and video_url if not set
            while parent_id and current_level > 1:
                parent_result = db.table("knowledge_items").select("*").eq("id", parent_id).single().execute()
                if parent_result.data:
                    parent_data = parent_result.data
                    current_level = parent_data.get("hierarchy_level", 1)

                    # If video_url not set yet and parent has it, use parent's URL
                    if not video_url and parent_data.get("media_url"):
                        video_url = parent_data.get("media_url")

                    if current_level == 1:
                        course_id = parent_id
                        break
                    parent_id = parent_data.get("parent_id")
                else:
                    break

        # Read file content
        file_content = await file.read()
        file_text = file_content.decode("utf-8")

        # Determine format
        file_format = "srt" if file.filename.endswith(".srt") else "vtt"

        # Parse transcript
        segments = transcription_service.parse_uploaded_transcript(file_text, file_format)

        # Build hierarchical context names
        folder_path = await course_manager.get_folder_path(lesson_id, db)
        course_name = folder_path[0] if len(folder_path) > 0 else ""
        module_name = folder_path[1] if len(folder_path) > 1 else ""

        # Create segments
        segment_ids = await transcription_service.create_transcript_segments(
            lesson_id=lesson_id,
            course_id=course_id or lesson_id,  # Use folder ID as fallback
            module_id=None,  # No longer used in new structure
            segments=segments,
            video_url=video_url,
            db=db,
            lesson_name=folder_name,
            module_name=module_name,
            course_name=course_name
        )

        return UploadTranscriptResponse(
            success=True,
            lesson_id=lesson_id,
            segments_created=len(segment_ids),
            segment_ids=segment_ids,
            format=file_format
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Upload transcript error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Upload transcript error: {str(e)}")


@router.get("/api/admin/lessons/{lesson_id}/segments", response_model=list[Segment])
async def get_lesson_segments(lesson_id: str):
    """Get all transcript segments for a lesson"""
    try:
        db = get_db()

        segments_data = db.table("knowledge_items")\
            .select("*")\
            .eq("lesson_id", lesson_id)\
            .eq("hierarchy_level", 4)\
            .order("timecode_start", desc=False)\
            .execute()

        segments = [
            Segment(
                id=seg["id"],
                lesson_id=seg["lesson_id"],
                text=seg["answer"],
                timecode_start=seg["timecode_start"],
                timecode_end=seg["timecode_end"],
                created_at=seg["created_at"],
                updated_at=seg["updated_at"]
            )
            for seg in segments_data.data
        ]

        return segments

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get segments error: {str(e)}")


@router.put("/api/admin/segments/{segment_id}", response_model=Segment)
async def update_segment(segment_id: str, request: UpdateSegmentRequest):
    """Update a transcript segment"""
    try:
        db = get_db()

        # Build update data
        update_data = {"answer": request.text}
        if request.timecode_start is not None:
            update_data["timecode_start"] = request.timecode_start
        if request.timecode_end is not None:
            update_data["timecode_end"] = request.timecode_end

        # Update segment
        result = db.table("knowledge_items").update(update_data).eq("id", segment_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail=f"Segment {segment_id} not found")

        updated_seg = result.data[0]

        return Segment(
            id=updated_seg["id"],
            lesson_id=updated_seg["lesson_id"],
            text=updated_seg["answer"],
            timecode_start=updated_seg["timecode_start"],
            timecode_end=updated_seg["timecode_end"],
            created_at=updated_seg["created_at"],
            updated_at=updated_seg["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update segment error: {str(e)}")


@router.put("/api/admin/folders/{folder_id}", response_model=Folder)
async def update_folder(folder_id: str, request: UpdateFolderRequest):
    """Update course/module/lesson metadata"""
    try:
        db = get_db()

        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.thumbnail_url is not None:
            updates["thumbnail_url"] = request.thumbnail_url
        if request.video_url is not None:
            updates["video_url"] = request.video_url
        if request.video_duration_seconds is not None:
            updates["video_duration_seconds"] = request.video_duration_seconds

        success = await course_manager.update_folder(folder_id, updates, db)

        if not success:
            raise HTTPException(status_code=404, detail=f"Folder {folder_id} not found")

        # Fetch updated folder
        folder_data = db.table("knowledge_items").select("*").eq("id", folder_id).single().execute()
        hierarchy_level = folder_data.data["hierarchy_level"]

        type_map = {1: "course", 2: "module", 3: "lesson"}

        return Folder(
            id=folder_id,
            name=folder_data.data["question"],
            description=folder_data.data["answer"],
            type=type_map.get(hierarchy_level, "unknown"),
            parent_id=folder_data.data.get("parent_id"),
            metadata={}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update folder error: {str(e)}")


@router.delete("/api/admin/folders/{folder_id}", response_model=DeleteFolderResponse)
async def delete_folder(folder_id: str):
    """Delete folder (CASCADE deletes all children automatically)"""
    try:
        db = get_db()

        result = await course_manager.delete_folder(folder_id, db)

        return DeleteFolderResponse(
            success=result["success"],
            deleted_count=result["deleted_count"],
            message=f"Successfully deleted {result['deleted_count']} items"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete folder error: {str(e)}")


@router.post("/api/admin/courses/{course_id}/clone", response_model=CloneCourseResponse)
async def clone_course_endpoint(course_id: str, request: CloneCourseRequest):
    """Clone entire course with all children"""
    try:
        db = get_db()

        # Get segment count for reporting
        segments_data = db.table("knowledge_items")\
            .select("id", count="exact")\
            .eq("course_id", course_id)\
            .eq("hierarchy_level", 4)\
            .execute()

        segment_count = segments_data.count or 0

        new_course_id = await course_manager.clone_course(
            course_id=course_id,
            new_name=request.new_name,
            regenerate_embeddings=request.regenerate_embeddings,
            db=db
        )

        return CloneCourseResponse(
            success=True,
            new_course_id=new_course_id,
            message=f"Course cloned successfully as '{request.new_name}'",
            segments_cloned=segment_count,
            embeddings_regenerated=request.regenerate_embeddings
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clone course error: {str(e)}")


@router.get("/api/admin/courses/{course_id}/stats", response_model=CourseStatsResponse)
async def get_course_stats(course_id: str):
    """Get statistics for a course"""
    try:
        db = get_db()
        stats = await course_manager.get_course_stats(course_id, db)

        if not stats:
            raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

        # Get course name
        course_data = db.table("knowledge_items").select("question", "updated_at").eq("id", course_id).single().execute()

        return CourseStatsResponse(
            course_id=course_id,
            course_name=course_data.data["question"],
            module_count=stats.get("module_count", 0),
            lesson_count=stats.get("lesson_count", 0),
            segment_count=stats.get("segment_count", 0),
            total_duration_seconds=stats.get("total_duration_seconds", 0),
            last_updated=course_data.data["updated_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get stats error: {str(e)}")
