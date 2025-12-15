# Phase 3: Enhanced Content Ingestion System

## 🎯 Objective
Build an admin UI that allows staff to easily add content from multiple sources with rich metadata, improving search quality and source attribution.

---

## 📋 Requirements (from user)

### 1. Facebook Post Import
- **Input:** Screenshot image + Facebook post URL
- **Process:** Use vision API (GPT-4 Vision or Gemini Vision) to extract Q&A
- **Output:** Structured Q&A with screenshot thumbnail and source link

### 2. Course Video Transcript Import
- **Input:** .srt transcript file with timecodes + video URL
- **Process:** Parse SRT, chunk by topic, preserve timestamps
- **Output:** Searchable transcript segments with video deep links

### 3. Better Source References
- Store original media (screenshots, video links)
- Preserve timestamps for video content
- Enable "jump to source" functionality in search results

---

## 🗄️ Database Schema Changes

### Update `knowledge_items` table:

```sql
-- Add new columns for rich content
ALTER TABLE knowledge_items
ADD COLUMN content_type VARCHAR(50) DEFAULT 'manual',  -- facebook, video, manual, csv
ADD COLUMN media_url TEXT,                              -- Screenshot or video URL
ADD COLUMN media_thumbnail TEXT,                        -- Thumbnail for display
ADD COLUMN timecode_start INTEGER,                      -- Video start time (seconds)
ADD COLUMN timecode_end INTEGER,                        -- Video end time (seconds)
ADD COLUMN extracted_by VARCHAR(50),                    -- manual, gpt-4-vision, gemini-vision
ADD COLUMN extraction_confidence FLOAT,                 -- AI extraction confidence score
ADD COLUMN raw_content TEXT,                            -- Original text before processing
ADD COLUMN parent_id UUID REFERENCES knowledge_items(id); -- Group related items

-- Create index for content type filtering
CREATE INDEX idx_content_type ON knowledge_items(content_type);

-- Create index for parent-child relationships
CREATE INDEX idx_parent_id ON knowledge_items(parent_id);
```

---

## 🏗️ Architecture Design

### Backend Endpoints (New)

```
POST /api/admin/upload-screenshot
  - Accept: multipart/form-data (image + URL)
  - Process: Vision API extraction
  - Return: Extracted Q&A preview (not saved yet)

POST /api/admin/save-extracted
  - Accept: JSON with extracted Q&A + user edits
  - Process: Generate embeddings, save to DB
  - Return: Success with ID

POST /api/admin/upload-transcript
  - Accept: .srt file + video URL
  - Process: Parse SRT, chunk by timestamps
  - Return: Parsed segments preview

POST /api/admin/batch-import
  - Accept: Array of content items
  - Process: Bulk insert with embeddings
  - Return: Success count + errors

GET /api/admin/content-list
  - Return: Paginated list of all content
  - Filter by: content_type, date, source

DELETE /api/admin/content/:id
  - Soft delete (mark as deleted)
```

### Frontend Routes (New)

```
/admin
  - Dashboard overview
  - Recent imports
  - Content statistics

/admin/import/facebook
  - Screenshot upload area
  - URL input field
  - Preview extracted Q&A
  - Edit before saving

/admin/import/video
  - SRT file upload
  - Video URL input
  - Timeline preview
  - Chunk management

/admin/content
  - Content library
  - Search and filter
  - Edit/delete existing content
```

---

## 🔧 Implementation Steps

### Step 1: Database Migration
- [ ] Create migration file `002_content_ingestion.sql`
- [ ] Add new columns to knowledge_items
- [ ] Create indexes
- [ ] Test migration rollback

### Step 2: Backend Services

#### A. Vision Extraction Service
```python
# backend/app/services/vision_extractor.py
- extract_from_screenshot(image: bytes, url: str) -> dict
- Uses GPT-4 Vision or Gemini Vision
- Returns: { questions: [], answers: [], metadata: {} }
```

#### B. SRT Parser Service
```python
# backend/app/services/srt_parser.py
- parse_srt_file(file: bytes) -> List[Segment]
- chunk_by_topic(segments: List) -> List[Chunk]
- generate_deep_links(chunks: List, video_url: str) -> List
```

#### C. Content Management Service
```python
# backend/app/services/content_manager.py
- save_content(content: dict, type: str) -> UUID
- update_content(id: UUID, updates: dict) -> bool
- delete_content(id: UUID) -> bool
- list_content(filters: dict, page: int) -> List
```

### Step 3: Backend API Endpoints
- [ ] Create admin router `/api/admin`
- [ ] Implement screenshot upload endpoint
- [ ] Implement SRT upload endpoint
- [ ] Add authentication middleware (admin only)
- [ ] Add batch import endpoint

### Step 4: Frontend Components

#### A. Admin Layout
```tsx
// frontend/app/admin/layout.tsx
- Sidebar navigation
- Admin header
- Breadcrumbs
```

#### B. Screenshot Import UI
```tsx
// frontend/components/admin/ScreenshotImport.tsx
- Drag & drop image upload
- URL input
- Loading state during extraction
- Preview editor for Q&A
- Save button
```

#### C. SRT Import UI
```tsx
// frontend/components/admin/TranscriptImport.tsx
- File upload (.srt only)
- Video URL input
- Timeline visualization
- Chunk preview with timecodes
- Bulk save functionality
```

#### D. Content Library
```tsx
// frontend/components/admin/ContentLibrary.tsx
- Filterable table
- Content type badges
- Edit/delete actions
- Pagination
```

### Step 5: Integration & Testing
- [ ] Test screenshot extraction with sample images
- [ ] Test SRT parsing with sample transcript
- [ ] Test full workflow: upload → extract → save → search
- [ ] Verify embeddings generated correctly
- [ ] Test search with new content

---

## 📝 Sample Data Structures

### Screenshot Extraction Result:
```json
{
  "content_type": "facebook",
  "extracted_items": [
    {
      "question": "How do I price my digital product?",
      "answer": "Start with a value-based pricing model...",
      "confidence": 0.92,
      "detected_date": "2024-11-15",
      "detected_tags": ["pricing", "digital_products"]
    }
  ],
  "source_url": "https://facebook.com/groups/...",
  "media_url": "uploaded_screenshot.png",
  "extracted_by": "gpt-4-vision"
}
```

### SRT Parsing Result:
```json
{
  "content_type": "video",
  "video_url": "https://youtube.com/watch?v=...",
  "chunks": [
    {
      "text": "In this section, we'll cover pricing strategies...",
      "timecode_start": 120,
      "timecode_end": 245,
      "deep_link": "https://youtube.com/watch?v=...&t=120s",
      "detected_topic": "pricing_strategies"
    }
  ]
}
```

---

## 🎨 UI Mockup Ideas

### Screenshot Import Flow:
```
┌────────────────────────────────────┐
│  Import from Facebook              │
├────────────────────────────────────┤
│                                    │
│  [Drag & drop screenshot here]    │
│      or click to upload            │
│                                    │
│  Post URL: [___________________]  │
│                                    │
│  [Extract Q&A]                    │
│                                    │
│  ─── Extracted Content ───         │
│                                    │
│  Q: How do I...?                  │
│  A: You should...                 │
│  [Edit] [Delete]                  │
│                                    │
│  Confidence: 92%                  │
│  Tags: [pricing] [strategy]       │
│                                    │
│  [Save to Knowledge Base]         │
└────────────────────────────────────┘
```

### Video Transcript Import:
```
┌────────────────────────────────────┐
│  Import Video Transcript           │
├────────────────────────────────────┤
│                                    │
│  Video URL: [___________________] │
│  SRT File:  [Choose file]         │
│                                    │
│  [Parse Transcript]               │
│                                    │
│  ─── Timeline ───                 │
│  ┌─┬─┬─┬─┬─┬─┬─┬─┐              │
│  │0│2│4│6│8│10│12│14│ (minutes)  │
│  └─┴─┴─┴─┴─┴─┴─┴─┘              │
│   ▓▓░░▓▓▓▓░░▓▓▓▓                 │
│   (colored by topic)              │
│                                    │
│  ─── Chunks (5) ───               │
│                                    │
│  [00:02:00-00:04:15] Pricing     │
│  "In this section..."             │
│  [View] [Edit]                    │
│                                    │
│  [00:04:20-00:06:30] Marketing   │
│  "When it comes to..."            │
│  [View] [Edit]                    │
│                                    │
│  [Import All Chunks]              │
└────────────────────────────────────┘
```

---

## 🔒 Security Considerations

1. **Authentication:**
   - Only admin users can access `/admin/*` routes
   - Use Supabase RLS or JWT middleware
   - Session timeout after 30 minutes

2. **File Upload:**
   - Validate file types (images: jpg/png, transcripts: .srt)
   - Limit file size (images: 10MB, SRT: 5MB)
   - Virus scanning (optional)
   - Store uploads in Supabase Storage or S3

3. **Rate Limiting:**
   - Limit vision API calls (expensive)
   - Max 10 uploads per hour per user
   - Queue system for batch processing

---

## 💰 Cost Estimates

### Vision API Costs:
- GPT-4 Vision: ~$0.01-0.03 per image
- Gemini Vision: ~$0.002-0.01 per image
- Estimated: 50 images/month = $1-1.50/month

### Embedding Generation:
- Already accounted for in Phase 1/2
- Minimal incremental cost

### Storage:
- Supabase Storage: 1GB free
- Screenshots: ~500KB each = 2000 images per GB
- SRT files: ~50KB each = 20,000 files per GB

**Total Phase 3 Monthly Cost:** $5-10 for moderate usage

---

## ✅ Acceptance Criteria

Phase 3 is complete when:

- [ ] Staff can upload Facebook screenshot + URL
- [ ] System extracts Q&A automatically with 80%+ accuracy
- [ ] Staff can edit extracted content before saving
- [ ] Staff can upload .srt file with video URL
- [ ] System chunks transcript by topic with timestamps
- [ ] Search results show source type (facebook/video/manual)
- [ ] Clicking video source jumps to exact timestamp
- [ ] Admin can view/edit/delete all content
- [ ] All new content generates embeddings automatically
- [ ] Search works with new rich content

---

## 📅 Estimated Timeline

- **Step 1 (Database):** 1 hour
- **Step 2 (Backend Services):** 3-4 hours
- **Step 3 (API Endpoints):** 2 hours
- **Step 4 (Frontend UI):** 4-5 hours
- **Step 5 (Testing):** 2 hours

**Total:** 12-14 hours of development time

---

## 🚀 Quick Start for Phase 3

When ready to begin:

1. Review this document
2. Create database migration
3. Start with screenshot extraction (higher priority)
4. Test with real Facebook posts
5. Add SRT parser next
6. Polish UI last

---

**Created:** 2025-12-15
**Status:** Planning phase
**Priority:** Medium (after Phase 1, 2, 4 are solid)
