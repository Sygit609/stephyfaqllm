# Claude Project Log - OIL Q&A Search Tool

---
## 2025-12-15 (Session Start)
**Prompt:** Building a Q&A search backend for sister's online course community (Online Income Lab). Need to handle internal KB search + web search for technical questions, with smart recency detection for announcements vs static Q&As.

**Reasoning summary:** User has ~41 Q&A pairs from Facebook, wants to build a system that helps staff answer repetitive questions faster. Key challenges: (1) Distinguish internal vs external questions, (2) Handle recency for announcements, (3) Search web for technical tools (GHL, Systeme.io, etc.), (4) Show all sources to staff for verification, (5) Generate grounded replies without hallucination.

**Actions / changes:** None yet - starting with architecture planning phase.

**Files touched:** None yet

**Next steps:**
- Explain recommended architecture
- Ask clarifying questions about requirements
- Set up database schema
- Implement search pipeline
- Add LLM generation with strict grounding

---
## 2025-12-15 (CSV Analysis)
**Prompt:** User provided CSV structure and answered architecture questions. CSV has 41 Q&A pairs with good metadata (question_raw, question_enriched, answer, answered_by, date, source_url, tags).

**Key insights from CSV:**
- Already has question_raw vs question_enriched (shows user understands semantic variations)
- Tags are well-structured (comma-separated, specific)
- Source URLs point to Facebook group threads
- All current data is from Dec 2024, dates range Nov-Dec
- Data is Q&A format only - no pure announcements yet
- Some answers marked as "pending" (needs follow-up)
- Multiple Q&As can share same thread_id (grouped conversations)

**User requirements clarified:**
- Staff will update KB by pasting Facebook screenshots into chat UI
- Need LLM to extract Q&A from screenshot and store it
- MVP focus, simple auth (staff + sister only)
- Flexible budget for good MVP
- Tech stack: open to recommendations

**Decisions made:**
- Use FastAPI backend (Python - good for LLM workflows, type-safe, async)
- Supabase for DB + auth (handles auth out of box, good free tier)
- Next.js frontend (chat UI pattern, easy to deploy)
- OpenAI for embeddings + generation (user already has API key)
- Tavily for web search (LLM-ready responses)

**Files touched:**
- Read: /Users/chenweisun/Downloads/offerlab_qna.csv

**Next steps:**
1. Design improved database schema based on CSV structure
2. Build CSV import script with embedding generation
3. Create FastAPI backend with search endpoints
4. Add screenshot → Q&A extraction feature
5. Build chat UI frontend

---
## 2025-12-15 (Multi-Model Architecture Decision)
**Prompt:** User wants to test both Gemini and OpenAI, with ability to switch between them during MVP testing. Will remove one after evaluation.

**Reasoning summary:** Built adapter pattern architecture to support both providers with unified interface. Frontend will have model toggle. Backend tracks cost/latency/quality metrics per provider to inform final decision.

**Decisions made:**
- Adapter pattern for LLM abstraction (base class + Gemini/OpenAI implementations)
- Dual embeddings in DB (both OpenAI 1536-dim + Gemini 768-dim vectors)
- Runtime model switching via API parameter
- Metrics tracking table to compare performance
- Optional side-by-side comparison mode

**Plan created:** Complete implementation plan with 5 phases:
- Phase 1: Database + Import (Supabase setup, dual embeddings)
- Phase 2: Backend Core (FastAPI, adapters, search, classification)
- Phase 3: Screenshot Extraction (vision API for Q&A extraction)
- Phase 4: Frontend (Next.js chat UI with model selector)
- Phase 5: Deploy & Polish

**Files touched:**
- Created: /Users/chenweisun/.claude/plans/sprightly-wandering-creek.md (full implementation plan)

**Next steps:**
- Exit plan mode and begin Phase 1 implementation
- Set up Supabase project
- Create migration files
- Build CSV import script with dual embeddings

---
## 2025-12-15 (Phase 1 Implementation - Database & Import Script)
**Prompt:** Build Phase 1 - database setup and CSV import with dual embeddings

**Actions taken:**
1. Created complete project structure (backend/, frontend/, scripts/, supabase/)
2. Built comprehensive Supabase migration (001_initial_schema.sql) with:
   - knowledge_items table (dual embeddings, full-text search, recency tracking)
   - query_logs table (metrics per query)
   - model_metrics table (aggregate stats)
   - Automatic triggers for search_vector and updated_at
   - Helper views for analysis
3. Created CSV import script (import_csv.py) that:
   - Reads CSV and parses to DB format
   - Generates embeddings from both OpenAI and Gemini in parallel
   - Auto-detects categories and time-sensitivity
   - Provides detailed progress output
4. Added supporting files:
   - .env.example with all required API keys
   - requirements.txt for Python dependencies
   - README.md with setup instructions

**Files touched:**
- Created: oil-qa-tool/supabase/migrations/001_initial_schema.sql
- Created: oil-qa-tool/scripts/import_csv.py
- Created: oil-qa-tool/scripts/requirements.txt
- Created: oil-qa-tool/.env.example
- Created: oil-qa-tool/README.md

**Next steps:**
- User needs to: (1) Set up Supabase project, (2) Run migration, (3) Configure .env, (4) Test import
- After successful import: Begin Phase 2 (FastAPI backend)

---
## 2025-12-15 (Phase 1 Complete - CSV Import Success)
**Prompt:** User completed Supabase setup, ran migration, configured .env, and successfully imported CSV data.

**Actions taken:**
1. User created Supabase project and ran 001_initial_schema.sql migration
2. Configured .env file with API credentials (Supabase, OpenAI, Google AI)
3. Installed Python dependencies (openai, google-generativeai, supabase, python-dotenv)
4. Successfully ran CSV import script
5. Imported 40 Q&As with dual embeddings (OpenAI + Gemini)

**Results:**
- ✅ 40 Q&As imported successfully
- ✅ 1 row skipped (pending answer)
- ✅ All embeddings generated (OpenAI 1536-dim + Gemini 768-dim)
- ✅ Database verified with sample records

**Files touched:**
- Created: .gitignore (to protect .env and secrets)
- Created: .env (configured with actual API keys)
- Created: scripts/test_env.py (helper to debug .env loading)

**Next steps:**
- Begin Phase 2: Build FastAPI backend with search + generation endpoints

---
## 2025-12-15 (Phase 2 Start - FastAPI Backend Foundation)
**Prompt:** Begin Phase 2 - Build FastAPI backend with search and answer generation

**Actions taken:**
1. Created implementation plan for Phase 2 (10 steps)
2. Built core configuration system (backend/app/core/config.py)
   - Environment variable loading with Pydantic
   - API key validation
   - Model specifications and cost constants
3. Built database client (backend/app/core/database.py)
   - Supabase connection wrapper
   - Dependency injection pattern for FastAPI
4. Created comprehensive Pydantic models (backend/app/models/schemas.py)
   - Search, Answer, Query request/response models
   - Feedback and Metrics models
5. Implemented LLM adapter pattern (backend/app/services/llm_adapters.py)
   - BaseLLMAdapter abstract class
   - OpenAI adapter (gpt-4o + text-embedding-3-small)
   - Gemini adapter (Gemini 2.0 Flash + text-embedding-004)
   - Factory function for runtime model switching

**Files created:**
- backend/app/__init__.py
- backend/app/core/__init__.py
- backend/app/core/config.py
- backend/app/core/database.py
- backend/app/models/__init__.py
- backend/app/models/schemas.py
- backend/app/services/__init__.py
- backend/app/services/llm_adapters.py

**Progress:** 3/10 implementation steps complete

**Next steps:**
- Build search service with hybrid search (vector + fulltext)
- Implement web search integration (Tavily)
- Create answer generation service
- Build metrics logging service
- Implement API endpoints
- Create FastAPI main application
- Add requirements.txt and test

---
## 2025-12-15 (Phase 2 Complete - Full FastAPI Backend)
**Prompt:** Continue Phase 2 implementation - complete all remaining backend services

**Actions taken:**
1. Built search service (backend/app/services/search.py)
   - Intent classification (internal vs external)
   - Recency detection
   - Vector search with cosine similarity
   - Full-text search using Postgres tsvector
   - Hybrid search combining both with weighted scores (0.7 vector + 0.3 fulltext)

2. Implemented web search integration (backend/app/services/web_search.py)
   - Tavily API integration for external searches
   - Smart fallback logic (triggers when internal score < 0.7)
   - Source attribution from web results

3. Created answer generation service (backend/app/services/generation.py)
   - Grounded answer generation from internal sources
   - Web-based answer generation
   - Hybrid answers combining internal + web sources
   - Strong system prompts preventing hallucination
   - Source citation requirements

4. Built metrics logging service (backend/app/services/metrics.py)
   - Query logging to query_logs table
   - Staff feedback tracking (ratings, edits, notes)
   - Model comparison metrics
   - Recent query history retrieval

5. Implemented all API endpoints (backend/app/api/endpoints.py)
   - GET /health - Health check with API key validation
   - POST /api/search - Search-only endpoint
   - POST /api/answer - Generate answer from provided sources
   - POST /api/query - Main endpoint (search + generation)
   - POST /api/feedback - Staff feedback submission
   - GET /api/metrics - Model comparison stats
   - GET /api/recent-queries - Query history

6. Created FastAPI main application (backend/app/main.py)
   - CORS middleware configuration
   - Startup/shutdown event handlers
   - Router inclusion
   - Root endpoint

7. Added backend dependencies (backend/requirements.txt)
   - FastAPI, Uvicorn, Pydantic
   - OpenAI, Google Generative AI
   - Supabase, httpx, numpy

**Files created:**
- backend/app/services/search.py
- backend/app/services/web_search.py
- backend/app/services/generation.py
- backend/app/services/metrics.py
- backend/app/api/__init__.py
- backend/app/api/endpoints.py
- backend/app/main.py
- backend/requirements.txt

**Progress:** 10/10 implementation steps complete ✅

**Architecture highlights:**
- Hybrid search (vector + fulltext) for best accuracy
- Dual model support (OpenAI gpt-4o vs Gemini 2.0 Flash)
- Adapter pattern for easy model switching
- Comprehensive metrics tracking for model comparison
- Web search integration for external questions
- Grounded generation preventing hallucinations

**Next steps:**
- Install backend dependencies
- Test the API endpoints
- Fix any bugs or issues
- Begin Phase 3 (Screenshot extraction) or Phase 4 (Frontend)

---
## 2025-12-15 (Backend Testing & Bug Fixes)
**Prompt:** Test the backend API step-by-step

**Actions taken:**
1. Installed backend dependencies (all satisfied)
2. Started FastAPI server on port 8001 (port 8000 was in use)
3. Fixed import statements (changed from `backend.app.*` to `app.*`)
4. Tested health endpoint - ✅ All API keys valid, database connected

**Bug discovered and fixed:**
- **Issue:** Embeddings stored as JSON strings in database, not arrays
- **Impact:** Vector search returning 0 results (cosine similarity failed)
- **Fix:** Added JSON parsing in search.py:109-110 to convert strings to arrays
- **Result:** Vector search now works perfectly with 53% match scores

**Testing results:**
- ✅ Health endpoint working
- ✅ Search endpoint working (keyword search)
- ✅ Full query endpoint working (search + answer generation)
- ✅ Hybrid search (vector + fulltext) working correctly
- ✅ Answer generation with OpenAI GPT-4o working
- ✅ Source citation and metadata tracking working
- ✅ Cost tracking ($0.002-0.003 per query)
- ⚠️ Gemini rate-limited (free tier exhausted)

**Test query used:**
"Should I create separate social media accounts for different niches?"
- Found 5 relevant sources from KB
- Top match: 53% similarity (excellent)
- Generated grounded answer citing sources
- Latency: 4-9 seconds

**Backend Status:** ✅ Fully working and tested
**Server:** Running on http://localhost:8001

**Next steps:**
- Build Phase 4 (Frontend UI)

---
## 2025-12-15 (Phase 4 Complete - Frontend UI Built & Tested)
**Prompt:** Build frontend UI and test with backend

**Actions taken:**
1. Updated frontend .env.local to point to backend port 8001
2. Built complete Next.js frontend with TypeScript:
   - Main chat page (app/page.tsx)
   - Root layout (app/layout.tsx)
   - Search interface component (SearchInterface.tsx)
   - Model selector toggle (ModelSelector.tsx)
   - Answer display card (AnswerDisplay.tsx)
   - Sources list component (SourcesList.tsx)
   - API client hook (useQuery.ts)

3. UI Features implemented:
   - Clean, modern design with gradient backgrounds
   - Model selector toggle (OpenAI/Gemini)
   - Large textarea for questions
   - Loading states with spinner
   - Error handling with red alert boxes
   - Answer display with metadata badges (model, cost, latency, tokens)
   - Source cards with numbered badges
   - Match scores and tags as colored pills
   - Clickable Facebook source links
   - Responsive layout

4. Fixed missing dependency (autoprefixer)
5. Started frontend server on port 3000
6. Full stack tested and working

**Frontend Status:** ✅ Fully working and tested
**Server:** Running on http://localhost:3000

**Architecture summary:**
- Frontend: Next.js 15 + TypeScript + TailwindCSS
- Backend: FastAPI + Python
- Database: Supabase (PostgreSQL)
- Models: OpenAI GPT-4o (working) + Gemini 2.0 Flash (rate-limited)
- Search: Hybrid (vector embeddings + fulltext)

**Files created:**
- frontend/app/page.tsx
- frontend/app/layout.tsx
- frontend/components/search/SearchInterface.tsx
- frontend/components/search/ModelSelector.tsx
- frontend/components/search/AnswerDisplay.tsx
- frontend/components/search/SourcesList.tsx
- frontend/lib/hooks/useQuery.ts

**Git Status:**
- All work committed: `70f2d10` (38 files, 9,277 lines)
- Pushed to GitHub: https://github.com/Sygit609/stephyfaqllm
- Remote and local in sync ✅

**Current Status:**
- ✅ Phase 1: Database + Import (40 Q&As imported)
- ✅ Phase 2: Backend API (fully tested, all endpoints working)
- ⏭️ Phase 3: Screenshot Extraction (SKIPPED - to be implemented later)
- ✅ Phase 4: Frontend UI (fully tested, working with backend)

**Both servers running:**
- Backend: http://localhost:8001
- Frontend: http://localhost:3000

**Known issues:**
- Gemini free tier exhausted (use OpenAI instead)
- Screenshot extraction not yet implemented

---
## 2025-12-15 (Planning Phase 3 Enhancement)
**User request:** Build Phase 3 later with enhanced UI for content ingestion:
1. Facebook posts: Paste screenshot + link
2. Course videos: Upload .srt transcript with timecodes + links
3. Better source references for backend

**Phase 3 Future Scope:**
- Admin UI for content management
- Screenshot upload + OCR/Vision API extraction
- SRT transcript parser with timestamp preservation
- Link extraction and validation
- Batch import functionality
- Rich source metadata (timecodes, screenshots, links)

**Next session tasks:**
1. Design Phase 3 architecture
2. Build admin content ingestion UI
3. Implement Facebook screenshot processor
4. Implement SRT transcript parser
5. Update database schema for rich metadata
6. Update search to use enhanced sources

**Session paused - all work saved to GitHub**

---
## 2025-12-22 (Phase 3 Implementation - Screenshot Extraction Backend & Frontend)
**Prompt:** Build Phase 3 - Screenshot extraction feature with admin UI

**Actions taken:**
1. Created database migration (002_content_ingestion.sql) with:
   - New columns in knowledge_items: content_type, media_url, media_thumbnail, timecode_start/end, extracted_by, extraction_confidence, raw_content, parent_id
   - Parent-child relationship for organizing Q&As from single screenshot
   - Indexes and helper views for analytics

2. Extended LLM adapters with vision capabilities:
   - Added extract_from_image() method to BaseLLMAdapter
   - OpenAI implementation using gpt-4o vision ($0.01-0.03 per image)
   - Gemini implementation using gemini-2.0-flash-exp vision (free)

3. Built vision extraction service (vision_extractor.py):
   - Tries Gemini first (free), falls back to GPT-4 if confidence < 0.7
   - Validates extraction quality
   - Returns warnings for low confidence
   - Comparison mode for testing both models

4. Created content manager service (content_manager.py):
   - CRUD operations for knowledge items
   - Parent-child structure for screenshots
   - Dual embedding generation
   - List/delete content with filters

5. Added admin API endpoints:
   - POST /api/admin/extract-screenshot (preview only)
   - POST /api/admin/save-content (with embeddings)
   - GET /api/admin/content-list (with pagination/filters)
   - DELETE /api/admin/content/{item_id}

6. Built frontend admin UI:
   - 3-step workflow: Upload → Preview/Edit → Saved
   - ScreenshotUploader component (drag-drop, file validation)
   - ExtractionPreview component (edit Q&As before save)
   - SaveConfirmation component (success stats)
   - AdminImportPage orchestrating workflow

**Files created/modified:**
Backend:
- supabase/migrations/002_content_ingestion.sql
- backend/app/services/vision_extractor.py
- backend/app/services/content_manager.py
- Modified: backend/app/services/llm_adapters.py
- Modified: backend/app/api/endpoints.py
- Modified: backend/app/models/schemas.py
- Modified: backend/requirements.txt (added Pillow)

Frontend:
- frontend/lib/api/admin.ts
- frontend/app/admin/import/page.tsx
- frontend/components/admin/ScreenshotUploader.tsx
- frontend/components/admin/ExtractionPreview.tsx
- frontend/components/admin/SaveConfirmation.tsx
- Modified: frontend/lib/api/types.ts
- Modified: frontend/app/page.tsx (added "+ Import Content" link)

**Architecture decisions:**
- Gemini Vision primary (free), GPT-4 fallback (paid)
- Parent-child data model (1 screenshot → N Q&As)
- 0.7 confidence threshold for fallback
- Preview-before-save workflow for staff control

**Cost per screenshot:** $0.02-0.05 (mostly embeddings, occasional GPT-4 fallback)

**Documentation:**
- Created: docs/PHASE3_IMPLEMENTATION.md (comprehensive implementation guide)

**Status:**
- ✅ Backend complete and tested
- ✅ Frontend complete and tested
- ✅ Database migration complete
- ⏳ Testing with real screenshots pending

**Git commits:**
- ed3f09c: Add comprehensive session summary
- a80f231: Add detailed Phase 3 implementation plan
- a2b8756: Add comprehensive quick start guide
- 20c4f51: Update project documentation with Phase 2-4 completion
- 70f2d10: Add Phase 2 & 4: Complete backend API and frontend UI

---
## 2025-12-23 (Phase 3b Implementation - Batch Upload with Clipboard Paste)
**Prompt:** Build batch screenshot upload feature with clipboard paste support for bulk Facebook post imports

**Reasoning:** Initial Phase 3 only supported single screenshot uploads. User needs to import 10-50 screenshots at once during initial setup, with flexible workflow (paste all then add URLs, or add URLs as you paste).

**Actions taken:**
1. Created utility functions:
   - clipboard.ts: Extract image files from paste events
   - file-validation.ts: Shared validation logic (type, size limits)

2. Built reusable components:
   - ScreenshotThumbnail: Single screenshot card with status badges
   - BatchProgressTracker: Real-time progress display (success/failed/remaining)

3. Implemented BatchScreenshotUploader component:
   - Global clipboard paste listener (Cmd+V / Ctrl+V)
   - Drag-and-drop multiple files
   - Thumbnail grid with URL inputs per screenshot
   - Sequential extraction with 500ms delay (rate limit protection)
   - Individual status tracking (pending/extracting/success/failed)
   - Async preview generation to avoid hydration errors

4. Created BatchExtractionPreview component:
   - Accordion layout grouping Q&As by screenshot
   - Expand/collapse all functionality
   - Inline Q&A editing per screenshot
   - Individual screenshot deletion
   - Confidence badges per extraction
   - Batch save with sequential API calls

5. Enhanced existing components:
   - AdminImportPage: Added Single/Batch mode toggle, separate state management
   - SaveConfirmation: Added batch statistics support (total screenshots/Q&As/embeddings)
   - types.ts: Added BatchUpload interface

6. Fixed issues:
   - Empty string in image src: Changed to async Promise-based preview generation
   - CORS error: Added localhost:3001 to allowed origins in backend config
   - Nested button HTML error: Restructured accordion header to avoid button-in-button

**Key features:**
- ✅ Paste screenshots from clipboard (Cmd+V / Ctrl+V)
- ✅ Upload 10-50 screenshots at once
- ✅ Sequential extraction with progress tracking
- ✅ Failed extractions don't block others
- ✅ Accordion UI for batch review
- ✅ Error handling and recovery
- ✅ No breaking changes to single-upload workflow

**Files created:**
- frontend/components/admin/BatchScreenshotUploader.tsx (345 lines)
- frontend/components/admin/ScreenshotThumbnail.tsx (130 lines)
- frontend/components/admin/BatchProgressTracker.tsx (68 lines)
- frontend/components/admin/BatchExtractionPreview.tsx (348 lines)
- frontend/lib/utils/clipboard.ts
- frontend/lib/utils/file-validation.ts

**Files modified:**
- backend/app/core/config.py (added localhost:3001 to CORS)
- frontend/app/admin/import/page.tsx (batch mode support)
- frontend/components/admin/SaveConfirmation.tsx (batch statistics)
- frontend/lib/api/types.ts (BatchUpload interface)

**Technical implementation:**
- Async preview generation with Promise.all
- Sequential extraction with 500ms delays
- Flexbox layout to avoid nested buttons
- Conditional rendering for empty previews
- Batch save with error recovery

**Testing status:**
- ✅ Component compilation successful
- ✅ CORS fixed for localhost:3001
- ✅ File upload UI renders correctly
- ⏳ End-to-end batch workflow pending
- ⏳ Clipboard paste on macOS/Windows pending

**Documentation created:**
- docs/SESSION_2025-12-23.md (comprehensive session summary)

**Git commits:**
- 57945d1: Add Phase 3b: Batch screenshot upload with clipboard paste support (10 files, +1205 lines)
- 70e50c5: Add session summary for December 23, 2025

**Status:**
- ✅ Phase 3b implementation complete
- ✅ All code committed and pushed to GitHub
- ✅ Documentation updated
- ⏳ Ready for testing with real screenshots

**Next steps:**
- Test complete batch upload workflow
- Verify clipboard paste on macOS and Windows
- Test with 10-20 screenshots to measure performance
- Update PHASE3_IMPLEMENTATION.md with Phase 3b details

**Session end:** December 23, 2025

---