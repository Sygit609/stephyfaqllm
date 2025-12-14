# OIL Q&A Search Tool

AI-powered search tool for Online Income Lab staff to quickly find and draft answers to student questions.

## Features

- 🔍 **Hybrid Search**: Combines semantic (vector) search with keyword matching
- 🤖 **Dual Model Support**: Compare Gemini 2.0 Flash vs OpenAI GPT-4o
- 🌐 **Web Search Integration**: Automatically searches external sources for technical questions
- 📸 **Screenshot Extraction**: Upload Facebook screenshots to automatically add Q&As
- 📊 **Metrics Tracking**: Compare model performance, cost, and quality

## Project Structure

```
oil-qa-tool/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Config, auth
│   │   ├── models/      # Pydantic models
│   │   └── services/    # Business logic
│   └── requirements.txt
├── frontend/            # Next.js frontend
│   ├── app/
│   ├── components/
│   └── package.json
├── scripts/             # Utilities
│   ├── import_csv.py   # CSV import with embeddings
│   └── requirements.txt
├── supabase/
│   └── migrations/     # Database schema
└── docs/
    └── claude-history.md  # Development log
```

## Quick Start - Phase 1 (Database Setup)

### Prerequisites

1. **Supabase Account**
   - Go to [supabase.com](https://supabase.com)
   - Create a new project
   - Get your project URL and anon key

2. **API Keys**
   - OpenAI API key from [platform.openai.com](https://platform.openai.com)
   - Google AI API key from [makersuite.google.com](https://makersuite.google.com/app/apikey)

### Step 1: Set up Supabase

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy the entire contents of `supabase/migrations/001_initial_schema.sql`
4. Paste and run the SQL script
5. Verify tables are created: `knowledge_items`, `query_logs`, `model_metrics`

### Step 2: Configure Environment

```bash
cd oil-qa-tool
cp .env.example .env
# Edit .env with your actual API keys
```

### Step 3: Import CSV Data

```bash
cd scripts
pip install -r requirements.txt
python import_csv.py /path/to/your/offerlab_qna.csv
```

This will:
- Read your CSV
- Generate embeddings using both OpenAI and Gemini
- Insert all Q&As into Supabase
- Show progress and final stats

**Expected output:**
```
🚀 Starting CSV import from: offerlab_qna.csv
📝 Found 41 rows in CSV
🔄 Processing row 1/41: Instagram won't let me follow accounts...
✅ Row 1: Imported successfully
...
✅ Import complete!
📊 Successfully imported: 39
❌ Errors: 2 (pending answers skipped)
```

### Step 4: Verify Import

In Supabase dashboard:
1. Go to **Table Editor**
2. Select `knowledge_items` table
3. You should see 39+ rows with:
   - question_raw, question_enriched, answer
   - embedding_openai (1536 dimensions)
   - embedding_gemini (768 dimensions)
   - tags, category, date

## Cost Estimate for Import

For 41 Q&As with average 200 words each:

| Provider | Operation | Cost |
|----------|-----------|------|
| OpenAI   | 41 embeddings × ~300 tokens | ~$0.01 |
| Gemini   | 41 embeddings | Free (within quota) |
| **Total** | **One-time import** | **~$0.01** |

## Next Steps

- [ ] **Phase 2**: Build FastAPI backend with search + generation
- [ ] **Phase 3**: Add screenshot extraction
- [ ] **Phase 4**: Build Next.js frontend
- [ ] **Phase 5**: Deploy to production

## Development Log

See [docs/claude-history.md](docs/claude-history.md) for detailed development history.

## Support

Issues? Check the logs in the import script output or contact the development team.

---

Built with ❤️ for Online Income Lab
