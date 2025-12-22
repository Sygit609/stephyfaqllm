# Phase 3 Implementation - Screenshot Extraction

**Date:** 2025-12-22
**Status:** ✅ Backend Complete, ✅ Frontend Complete, ⏳ Testing Pending

---

## 🎯 Overview

Phase 3 adds admin UI for importing content from Facebook screenshots using vision AI. The system:
1. Accepts screenshot uploads
2. Extracts Q&A pairs using Gemini (free) with GPT-4 Vision fallback
3. Shows preview with confidence scores and warnings
4. Allows staff to edit before saving
5. Generates dual embeddings and saves to knowledge base

---

## ✅ Completed Components

### Backend Implementation

#### 1. Database Migration ✅
**File:** [supabase/migrations/002_content_ingestion.sql](supabase/migrations/002_content_ingestion.sql)

Added columns to `knowledge_items`:
- `content_type` - Type: manual, csv, screenshot, facebook, video
- `media_url` - Screenshot or video URL
- `media_thumbnail` - Thumbnail for display
- `timecode_start`, `timecode_end` - For future video support
- `extracted_by` - Vision model used (gemini-vision, gpt4-vision, manual)
- `extraction_confidence` - AI confidence score (0.0-1.0)
- `raw_content` - Original vision API response (JSONB)
- `parent_id` - Links child Q&As to parent screenshot

Created indexes and helper views for analytics.

#### 2. LLM Adapter Extensions ✅
**File:** [backend/app/services/llm_adapters.py](backend/app/services/llm_adapters.py:125-231)

Extended `BaseLLMAdapter` with vision capabilities:
```python
async def extract_from_image(
    image_data: bytes,
    source_url: str,
    extraction_prompt: Optional[str] = None
) -> Tuple[List[Dict], float, Dict]
```

**OpenAI Implementation:**
- Uses `gpt-4o` with base64 image encoding
- Structured JSON extraction prompt
- Returns Q&A pairs with confidence scores
- Costs ~$0.01-0.03 per screenshot

**Gemini Implementation:**
- Uses `gemini-2.0-flash-exp` with PIL Image
- Same extraction prompt format
- Free within quota (60 req/min)
- Returns same format as OpenAI

#### 3. Vision Extraction Service ✅
**File:** [backend/app/services/vision_extractor.py](backend/app/services/vision_extractor.py)

Main extraction service with fallback logic:
```python
async def extract_from_screenshot(
    image_data: bytes,
    source_url: str,
    use_fallback: bool = True,
    confidence_threshold: float = 0.7
) -> VisionExtractionResult
```

**Features:**
- Tries Gemini first (free, fast)
- Falls back to GPT-4 Vision if confidence < 0.7 or extraction fails
- Validates extraction quality
- Returns warnings for low confidence or quality issues
- Includes comparison mode for testing both models

**Validation includes:**
- Minimum content length checks
- Placeholder text detection
- Confidence score warnings
- Field completeness validation

#### 4. Content Manager Service ✅
**File:** [backend/app/services/content_manager.py](backend/app/services/content_manager.py)

Content CRUD with parent-child structure:

**Key Functions:**
```python
async def generate_dual_embeddings(text: str) -> Tuple[List[float], List[float]]
async def save_extracted_content(...) -> Dict[str, Any]
async def update_knowledge_item(...) -> bool
def list_content(...) -> Dict[str, Any]
def delete_content(...) -> Dict[str, Any]
```

**Parent-Child Structure:**
1. Creates parent entry (screenshot metadata)
2. Creates child entries (individual Q&As) with embeddings
3. Links children to parent via `parent_id`
4. Cascade delete handled by DB constraint

#### 5. Admin API Endpoints ✅
**File:** [backend/app/api/endpoints.py](backend/app/api/endpoints.py:348-532)

Three new admin endpoints:

**POST `/api/admin/extract-screenshot`**
- Accepts base64 image + source URL
- Returns extracted Q&A preview with confidence
- Does NOT save (preview only)

**POST `/api/admin/save-content`**
- Accepts edited Q&A pairs + metadata
- Generates dual embeddings
- Saves with parent-child structure
- Returns created IDs

**GET `/api/admin/content-list`**
- Lists content with filters
- Supports pagination
- Filters: content_type, extracted_by, min_confidence, has_parent, parent_id

**DELETE `/api/admin/content/{item_id}`**
- Deletes item (cascade to children if parent)

#### 6. Pydantic Models ✅
**File:** [backend/app/models/schemas.py](backend/app/models/schemas.py:202-293)

Added admin models:
- `ExtractScreenshotRequest` / `ExtractScreenshotResponse`
- `QAPair` - Single Q&A with tags
- `SaveContentRequest` / `SaveContentResponse`
- `ContentListFilter` / `ContentListResponse`
- `ContentItem`

---

### Frontend Implementation

#### 1. TypeScript Types ✅
**File:** [frontend/lib/api/types.ts](frontend/lib/api/types.ts:218-286)

Matching TypeScript interfaces for all admin models.

#### 2. Admin API Client ✅
**File:** [frontend/lib/api/admin.ts](frontend/lib/api/admin.ts)

Client functions:
```typescript
async function extractScreenshot(request) -> ExtractScreenshotResponse
async function saveContent(request) -> SaveContentResponse
async function listContent(params) -> ContentListResponse
async function deleteContent(itemId) -> { success, message, deleted_count }
function fileToBase64(file: File) -> Promise<string>
```

#### 3. Admin Import Page ✅
**File:** [frontend/app/admin/import/page.tsx](frontend/app/admin/import/page.tsx)

**3-Step Workflow:**
1. Upload Screenshot
2. Preview & Edit
3. Saved Confirmation

**Features:**
- Progress indicator with 3 steps
- State management for workflow
- Navigation between steps
- Link back to search tool

#### 4. ScreenshotUploader Component ✅
**File:** [frontend/components/admin/ScreenshotUploader.tsx](frontend/components/admin/ScreenshotUploader.tsx)

**Features:**
- Drag-and-drop file upload
- Click to browse fallback
- Image preview with file info
- Source URL input
- File validation (type, size < 10MB)
- Base64 conversion
- Loading states
- Error handling
- Model selection info

#### 5. ExtractionPreview Component ✅
**File:** [frontend/components/admin/ExtractionPreview.tsx](frontend/components/admin/ExtractionPreview.tsx)

**Features:**
- Confidence badge (color-coded by score)
- Warning alerts for quality issues
- Source URL display
- Editable Q&A pairs (question, answer, tags)
- Individual delete buttons
- Validation before save
- Metadata display (latency, cost)
- Cancel and save actions

#### 6. SaveConfirmation Component ✅
**File:** [frontend/components/admin/SaveConfirmation.tsx](frontend/components/admin/SaveConfirmation.tsx)

**Features:**
- Success animation
- Import details (parent ID, child IDs count)
- "What happens next?" explanation
- Statistics display
- Actions: Import another or go to search
- Embeddings count display

#### 7. Main Page Link ✅
**File:** [frontend/app/page.tsx](frontend/app/page.tsx:22-27)

Added "+ Import Content" button in top-right corner linking to `/admin/import`.

---

## 📊 Architecture Decisions

### Vision API Strategy
- **Primary:** Gemini Vision (free, fast)
- **Fallback:** GPT-4 Vision (if confidence < 0.7 or error)
- **Threshold:** 0.7 confidence minimum
- **Cost:** $0.02-0.05 per screenshot (mostly GPT-4 fallback)

### Data Model
```
Parent Entry (Screenshot)
├── ID: UUID
├── content_type: "screenshot"
├── media_url: Screenshot URL
├── extracted_by: Vision model used
├── extraction_confidence: Overall score
├── raw_content: Full API response
└── Children (Q&A Pairs)
    ├── Q&A #1 (with dual embeddings)
    ├── Q&A #2 (with dual embeddings)
    └── Q&A #3 (with dual embeddings)
```

### Workflow
```
1. Upload Screenshot
   ↓
2. Convert to base64
   ↓
3. POST /api/admin/extract-screenshot
   ↓
4. Try Gemini Vision
   ↓ (if fails or confidence < 0.7)
5. Fallback to GPT-4 Vision
   ↓
6. Show preview with warnings
   ↓
7. User edits Q&As
   ↓
8. POST /api/admin/save-content
   ↓
9. Generate dual embeddings (parallel)
   ↓
10. Save parent + children
    ↓
11. Success confirmation
```

---

## 🧪 Testing Plan

### Backend Tests

**Test 1: Database Migration**
```bash
# Run migration
psql -U postgres -d [db] -f supabase/migrations/002_content_ingestion.sql

# Verify columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'knowledge_items'
AND column_name IN ('media_url', 'extracted_by', 'parent_id');
```

**Test 2: Vision Extraction**
```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload --port 8001

# Test with sample image
curl -X POST http://localhost:8001/api/admin/extract-screenshot \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "<base64-encoded-image>",
    "source_url": "https://facebook.com/test",
    "use_fallback": true
  }'
```

**Test 3: Save Content**
```bash
curl -X POST http://localhost:8001/api/admin/save-content \
  -H "Content-Type: application/json" \
  -d '{
    "qa_pairs": [...],
    "media_url": "test.jpg",
    "source_url": "https://facebook.com/test",
    "extracted_by": "gemini-vision",
    "confidence": 0.85
  }'
```

### Frontend Tests

**Test 1: File Upload**
1. Navigate to http://localhost:3000/admin/import
2. Drag-drop an image or click to browse
3. Verify preview appears
4. Check file size validation (try > 10MB)
5. Check file type validation (try PDF)

**Test 2: URL Input**
1. Enter Facebook post URL
2. Verify validation
3. Check button enable/disable logic

**Test 3: Extraction**
1. Click "Extract Q&A Pairs"
2. Verify loading state
3. Check extraction results display
4. Verify warnings appear if low confidence

**Test 4: Edit Q&As**
1. Modify question/answer text
2. Add/remove tags
3. Delete individual Q&A pairs
4. Verify state updates

**Test 5: Save**
1. Click "Save X Q&A Pairs"
2. Verify loading state
3. Check success confirmation
4. Verify statistics display

**Test 6: End-to-End**
1. Upload → Extract → Edit → Save
2. Go to main search
3. Search for newly added content
4. Verify it appears in results

### Integration Test

**Full Workflow:**
```bash
# 1. Start backend
cd backend && python -m uvicorn app.main:app --reload --port 8001

# 2. Start frontend
cd frontend && npm run dev

# 3. Test workflow
- Upload Facebook screenshot
- Extract Q&A (verify Gemini or GPT-4 used)
- Edit if needed
- Save to knowledge base
- Search for the content
- Verify embeddings work (results appear)
```

---

## 📁 Files Created

### Backend (7 files)
1. `supabase/migrations/002_content_ingestion.sql` - Database schema
2. `backend/app/services/vision_extractor.py` - Vision extraction service
3. `backend/app/services/content_manager.py` - Content CRUD service
4. Modified: `backend/app/services/llm_adapters.py` - Added vision methods
5. Modified: `backend/app/api/endpoints.py` - Added 3 admin endpoints
6. Modified: `backend/app/models/schemas.py` - Added admin Pydantic models
7. Modified: `backend/requirements.txt` - Added Pillow==11.0.0

### Frontend (6 files)
1. `frontend/lib/api/admin.ts` - Admin API client
2. `frontend/app/admin/import/page.tsx` - Main import page
3. `frontend/components/admin/ScreenshotUploader.tsx` - Upload component
4. `frontend/components/admin/ExtractionPreview.tsx` - Preview component
5. `frontend/components/admin/SaveConfirmation.tsx` - Success component
6. Modified: `frontend/lib/api/types.ts` - Added admin types
7. Modified: `frontend/app/page.tsx` - Added import link

**Total:** 13 files (7 new, 6 modified)

---

## 🔒 Security Considerations

### Current Implementation
- ✅ File type validation (images only)
- ✅ File size limit (10MB max)
- ✅ Base64 encoding for transfer
- ✅ SQL injection protection (parameterized queries)
- ❌ No authentication (to be added in Phase 5)
- ❌ No rate limiting (to be added in Phase 5)

### Future Improvements (Phase 5)
- Add authentication middleware for `/api/admin/*` routes
- Implement rate limiting (10 uploads/hour per user)
- Add virus scanning for uploaded files
- Use Supabase Storage for file hosting
- Add Row Level Security (RLS) policies
- Implement session management

---

## 💰 Cost Analysis

### Per Screenshot
- **Gemini Vision:** Free (if successful)
- **GPT-4 Vision:** $0.01-0.03 (fallback only)
- **Embeddings:** $0.0004 per Q&A × 2 models × N pairs
- **Example:** 3 Q&As = $0.02-0.05 total

### Monthly Estimates (50 screenshots)
- **Vision API:** $1-1.50 (assuming 50% fallback)
- **Embeddings:** ~$0.12 (150 Q&As)
- **Storage:** Negligible (< 50MB)
- **Total:** ~$1.50-2.00/month

---

## 🚀 Next Steps

### Before Production
1. ✅ Run database migration
2. ⏳ Install Pillow: `pip3 install Pillow==11.0.0`
3. ⏳ Test with real Facebook screenshots
4. ⏳ Verify dual embeddings generated correctly
5. ⏳ Test search with new content
6. ⏳ Measure extraction accuracy
7. ⏳ Test fallback mechanism

### Future Enhancements (Phase 3b)
- Add SRT transcript parser for video content
- Implement batch upload (multiple screenshots at once)
- Add content library view (list/edit/delete existing content)
- Implement video timecode support
- Add screenshot thumbnail generation
- Improve extraction prompts based on real-world usage
- Add extraction quality metrics tracking

---

## 📝 Known Limitations

1. **No Authentication** - Admin endpoints are public (Phase 5)
2. **No Content Library UI** - Can list but no frontend for management yet
3. **No SRT Parser** - Video transcript support not implemented (Phase 3b)
4. **No Batch Upload** - One screenshot at a time
5. **No Image Hosting** - media_url expects external URL (use Supabase Storage in Phase 5)
6. **No Thumbnails** - media_thumbnail field added but not generated

---

**Status:** Backend and frontend implementation complete. Ready for testing and deployment.

**Next Session:** Test Phase 3 with real screenshots, measure accuracy, and fix any issues before Phase 5 (Deployment & Polish).
