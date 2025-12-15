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