# OIL Q&A Tool - Quick Start Guide

## 🎯 Project Overview
AI-powered Q&A search tool for Online Income Lab community. Helps staff answer repetitive questions by searching internal knowledge base and generating grounded responses.

**GitHub Repository:** https://github.com/Sygit609/stephyfaqllm

---

## 📊 Current Status (2025-12-22)

### ✅ Completed Phases:
- **Phase 1:** Database + CSV Import (40 Q&As loaded)
- **Phase 2:** Backend API (FastAPI, fully tested)
- **Phase 3:** Screenshot extraction with vision AI (ready for testing)
- **Phase 4:** Frontend UI (Next.js, fully tested)

### ⏳ Future Phases:
- **Phase 3b:** SRT transcript parser (video content)
- **Phase 5:** Deployment + Polish

---

## 🚀 How to Start the Application

### Prerequisites:
- Python 3.9+
- Node.js 18+
- Supabase account
- API keys: OpenAI, Google AI (Gemini), Tavily

### 1. Environment Setup

Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Required variables:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_gemini_key
TAVILY_API_KEY=your_tavily_key  # Optional for web search
```

### 2. Start Backend (Port 8001)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001
```

Verify: http://localhost:8001/health

### 3. Start Frontend (Port 3000)

```bash
cd frontend
npm install
npm run dev
```

Access: http://localhost:3000

---

## 🧪 Testing the Application

### Sample Queries to Try:

**Internal Knowledge (should find matches):**
```
Should I create separate social media accounts for different niches?
How do I get clients for my digital products?
```

**External Knowledge (general advice):**
```
What is the best time to post on Instagram in 2024?
```

### Expected Results:
- Answer generated in 3-5 seconds
- Source citations with match scores
- Cost: ~$0.002-0.003 per query (OpenAI)
- Metadata: model, latency, tokens

---

## 📁 Project Structure

```
oil-qa-tool/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Config, database
│   │   ├── models/       # Pydantic schemas
│   │   └── services/     # Search, LLM, metrics
│   └── requirements.txt
├── frontend/             # Next.js frontend
│   ├── app/             # Pages and layouts
│   ├── components/      # React components
│   └── lib/             # Hooks and API client
├── scripts/             # Utilities
│   └── import_csv.py   # Initial data import
├── supabase/
│   └── migrations/     # Database schema
└── docs/
    └── claude-history.md  # Full session log
```

---

## 🔧 Architecture

### Backend (FastAPI):
- **Search:** Hybrid (vector embeddings + fulltext)
- **Models:** OpenAI GPT-4o + Gemini 2.0 Flash (dual support)
- **Embeddings:** OpenAI 1536-dim + Gemini 768-dim
- **Database:** Supabase (PostgreSQL with pgvector)

### Frontend (Next.js):
- **UI:** TailwindCSS + TypeScript
- **State:** React hooks
- **API:** Axios client

### Key Features:
- Intent classification (internal vs external)
- Recency detection for time-sensitive queries
- Source citation and verification
- Cost and latency tracking
- Model comparison metrics

---

## 🐛 Known Issues

1. **Gemini Rate Limits:**
   - Free tier exhausted during testing
   - Use OpenAI instead (fully working)
   - Error: "429 quota exceeded"

2. **Embedding Storage:**
   - Fixed: JSON parsing added in search.py:109-110
   - Embeddings were stored as strings, now properly parsed

---

## 📋 Phase 3: Screenshot Extraction (2025-12-22)

### ✅ Implemented Features:

1. **Facebook Screenshot Import:**
   - Drag-and-drop or click to upload
   - Image preview and validation
   - Enter Facebook post URL
   - Extract Q&A with Gemini Vision (free) + GPT-4 Vision fallback
   - Confidence scores and warnings
   - Preview & edit workflow
   - Auto-tag and categorize

2. **Admin UI Workflow:**
   - Step 1: Upload screenshot + URL
   - Step 2: Review & edit extracted Q&As
   - Step 3: Success confirmation with statistics

3. **Backend Features:**
   - Dual embeddings (OpenAI + Gemini)
   - Parent-child data model (screenshot → Q&As)
   - Vision API fallback logic
   - Quality validation and warnings

### Database Schema Updates ✅
- ✅ Added `content_type` field (screenshot, facebook, video, manual, csv)
- ✅ Added `media_url` for screenshots/videos
- ✅ Added `timecode_start` and `timecode_end` (for future video support)
- ✅ Added `extracted_by` (gemini-vision, gpt4-vision, manual)
- ✅ Added `extraction_confidence` (0.0-1.0)
- ✅ Added `raw_content` (JSONB) for original API responses
- ✅ Added `parent_id` for linking Q&As to parent screenshot

### ⏳ Phase 3b: Future Enhancements
- Course video transcript parser (.srt files)
- Video timecode deep links
- Batch screenshot upload
- Content library management UI

---

## 📝 Important URLs

- **Local Frontend:** http://localhost:3000
- **Admin Import:** http://localhost:3000/admin/import
- **Local Backend:** http://localhost:8001
- **API Docs:** http://localhost:8001/docs
- **Health Check:** http://localhost:8001/health
- **GitHub Repo:** https://github.com/Sygit609/stephyfaqllm

---

## 🔐 Security Notes

- `.env` is gitignored (contains secrets)
- Never commit API keys
- Use `.env.example` as template
- Supabase RLS not yet configured (Phase 5)

---

## 💡 Quick Commands

```bash
# Import CSV data
python scripts/import_csv.py

# Run backend tests
python -m pytest backend/tests  # (not yet created)

# Build frontend for production
cd frontend && npm run build

# Check git status
git status

# View logs
cd backend && tail -f /tmp/claude/tasks/*.output
```

---

## 📚 Documentation

- **Full Session Log:** `docs/claude-history.md`
- **This Guide:** `QUICKSTART.md`
- **API Reference:** Visit http://localhost:8001/docs when server is running

---

## 🆘 Troubleshooting

### Backend won't start:
```bash
# Check if port 8001 is in use
lsof -ti:8001 | xargs kill -9

# Reinstall dependencies
cd backend && pip install -r requirements.txt --force-reinstall
```

### Frontend won't compile:
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules .next
npm install
npm run dev
```

### Search returns no results:
- Check if embeddings exist: Run `python scripts/test_env.py`
- Verify backend logs for errors
- Ensure database has data: Check Supabase dashboard

---

## ✅ Next Session Checklist

To resume where you left off:

1. Read `docs/claude-history.md` for full context
2. Start both servers (backend + frontend)
3. Test that everything still works
4. Begin Phase 3 implementation if ready

**Phase 3 Starting Point:**
- Design admin UI mockups
- Plan database schema changes
- Implement screenshot upload endpoint
- Build SRT parser utility

---

**Last Updated:** 2025-12-22
**Status:** Phase 1, 2, 3, 4 Complete ✅
**Next:** Phase 3 Testing & Phase 5 Deployment
