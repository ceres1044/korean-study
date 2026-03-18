# System Architecture

High-level overview of how Korean Learning Automation works.

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    DETECTION LAYER                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  macOS launchd (Scheduler)                                 │
│    └─ Triggers at Monday/Tuesday 11:30 AM EST              │
│       └─ Calls: auto_fetch.py                              │
│                                                              │
│  auto_fetch.py (Detector)                                  │
│    ├─ Load state from: output/auto_fetch_state.json        │
│    ├─ List videos in: Google Drive folder                  │
│    ├─ Create fingerprint: {filename}:{modification_time}   │
│    ├─ Compare with state                                   │
│    │  ├─ If NEW → Copy to recordings/ and process         │
│    │  └─ If EXISTING → Skip                               │
│    └─ Update state.json (mark as processed)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 PROCESSING LAYER                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  main_processor.py (Orchestrator)                          │
│    │                                                        │
│    ├─ STEP 1: extract_audio_chunks()                       │
│    │  ├─ Input: MP4 video                                  │
│    │  ├─ Tool: FFmpeg                                      │
│    │  ├─ Output: 5x MP3 chunks (~4.6MB each)              │
│    │  └─ Reason: Whisper API 25MB limit                    │
│    │                                                        │
│    ├─ STEP 2: transcribe_audio_chunks()                    │
│    │  ├─ Input: 5x MP3 chunks                              │
│    │  ├─ API: OpenAI Whisper v1                            │
│    │  ├─ Output: Combined transcript (20k chars)           │
│    │  └─ Cleanup: Delete chunk files                       │
│    │                                                        │
│    ├─ STEP 3: analyze_transcript()                         │
│    │  ├─ Input: Transcript text                            │
│    │  ├─ Module: claude_analyzer.py                        │
│    │  │  └─ API: Anthropic Claude Sonnet 4                 │
│    │  │     └─ max_tokens: 16000                           │
│    │  ├─ Output: 70 items (vocabulary, phrases, etc)       │
│    │  └─ Save: output/Korean_Class_MM_DD_YYYY_analysis.json│
│    │                                                        │
│    ├─ STEP 4: parse_session_date()                         │
│    │  ├─ Input: Filename "Korean_Class_11_24_2025.mp4"    │
│    │  ├─ Extract: MM_DD_YYYY format                        │
│    │  └─ Output: 2025-11-24 (YYYY-MM-DD)                   │
│    │                                                        │
│    └─ STEP 5: send_to_notion()                             │
│       ├─ Module: notion_sender.py                          │
│       ├─ Query existing entries (direct API)               │
│       ├─ Deduplication by Korean text                      │
│       ├─ Filter by confidence                              │
│       └─ Upload new items to Notion                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  DATABASE LAYER                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Notion API                                                │
│    ├─ POST /databases/{id}/query                           │
│    │  └─ Fetch existing Korean entries for dedup           │
│    └─ POST /pages                                          │
│       └─ Create new learning item pages                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
Google Drive
    │
    ├─ Korean_Class_11_24_2025.mp4
    │   (85 minutes, 163MB)
    │
    ▼
auto_fetch.py (Detection)
    │
    ├─ Create fingerprint
    ├─ Check state.json
    └─ NEW? → Continue
    
    ▼
Copy to recordings/
    │
    ├─ Korean_Class_11_24_2025.mp4
    │   (temp local copy)
    │
    ▼
main_processor.py → STEP 1: Extract Audio
    │
    ├─ FFmpeg → Extract audio to WAV
    ├─ Split into 20-min chunks
    ├─ Encode as MP3 (32kbps, 16kHz mono)
    │
    ├─ Chunk 1: 4.6MB ─┐
    ├─ Chunk 2: 4.6MB ─┤
    ├─ Chunk 3: 4.6MB ─┼─ All < 25MB
    ├─ Chunk 4: 4.6MB ─┤
    └─ Chunk 5: 0.5MB ─┘
    
    ▼
STEP 2: Transcribe Audio
    │
    ├─ Chunk 1 → Whisper API → 4,375 chars
    ├─ Chunk 2 → Whisper API → 3,947 chars
    ├─ Chunk 3 → Whisper API → 5,339 chars
    ├─ Chunk 4 → Whisper API → 4,448 chars
    └─ Chunk 5 → Whisper API → 2,439 chars
    
    └─ Combine → 20,552 chars total
    
    ▼
STEP 3: Analyze (Claude)
    │
    ├─ Input: 20,552 char transcript
    ├─ Claude Sonnet 4
    ├─ max_tokens: 16,000
    │
    └─ Extract:
       ├─ 32 vocabulary items
       ├─ 28 phrases
       ├─ 15 grammar points
       └─ 12 teacher corrections
    
    ▼
STEP 4: Parse Date
    │
    └─ "Korean_Class_11_24_2025.mp4"
       → 2025-11-24
    
    ▼
STEP 5: Deduplication & Upload
    │
    ├─ Query Notion database
    ├─ Extract existing Korean entries
    │  └─ Found: 191 existing items
    │
    ├─ Compare new items
    │  ├─ Skipped: 12 duplicates
    │  └─ New: 58 items
    │
    ├─ Filter by confidence
    │  └─ Keep: high + medium only
    │
    └─ Upload to Notion
       ├─ Create 58 pages
       └─ Set all properties
    
    ▼
Cleanup
    │
    ├─ Delete MP3 chunks
    ├─ Delete local copy
    └─ Update state.json
    
    ▼
✅ Complete
    └─ Notion: +58 new items (249 total)
```

## Module Responsibilities

### auto_fetch.py
- **Purpose:** Detect new videos and trigger pipeline
- **Trigger:** launchd scheduler or manual execution
- **Functions:**
  - `list_videos()` → Find video files in Google Drive
  - `load_state()` / `save_state()` → Track processed files
  - `run_processor()` → Execute main_processor.py

### main_processor.py
- **Purpose:** Orchestrate full pipeline
- **Functions:**
  - `get_video_duration()` → Check video length
  - `extract_audio_chunks()` → Split and encode audio
  - `transcribe_audio_chunks()` → Send chunks to Whisper API
  - `parse_session_date()` → Extract date from filename
  - Main pipeline coordination

### claude_analyzer.py
- **Purpose:** Extract learning materials from transcript
- **Function:** `analyze_transcript(text) → dict`
- **Returns:**
  ```python
  {
    "vocabulary": [{"korean": "...", "english": "..."}],
    "phrases": [...],
    "grammar": [...],
    "corrections": [...]
  }
  ```

### notion_sender.py
- **Purpose:** Upload to Notion with deduplication
- **Functions:**
  - `send_to_notion()` → Main upload function
  - Queries existing entries via direct API
  - Deduplicates by Korean text
  - Filters by confidence level

### state_manager.py
- **Purpose:** Track processing progress
- **Features:**
  - Save/load JSON state files
  - Resume capability
  - Track completed steps

## API Integration Points

### OpenAI Whisper
```
POST https://api.openai.com/v1/audio/transcriptions
├─ Model: whisper-1
├─ Language: Korean
└─ File: MP3 chunk (<25MB)
```

### Anthropic Claude
```
POST https://api.anthropic.com/v1/messages
├─ Model: claude-sonnet-4-20250514
├─ max_tokens: 16000
├─ temperature: 0.3
└─ system: Extract Korean learning materials
```

### Notion
```
GET/POST https://api.notion.com/v1/databases/{id}/query
├─ Method: POST for queries
├─ Headers: Authorization, Notion-Version
└─ Body: filter, sort, pagination

POST https://api.notion.com/v1/pages
├─ Method: POST to create pages
├─ Parent: database_id
└─ Properties: Korean, English, Type, Date, etc
```

## Deduplication Strategy

**Problem:** Multiple uploads of same video create duplicates

**Solution:** Direct Notion API Query
```
1. Format database ID with hyphens
2. POST /databases/{formatted_id}/query
3. Extract Korean text from all existing pages
4. Store in set: {korean_text}
5. For each new item:
   if korean_text in existing_set:
       skip
   else:
       upload
```

**Performance:**
- Scans 627 pages in ~2 seconds
- Identifies 134 unique entries
- Prevents duplicates reliably

## Deployment Architecture

### Local Execution
```
Computer (macOS)
├─ Python virtual environment
├─ API credentials in .env
├─ launchd scheduler
└─ Output files in ~/koreanlearning/output
```

### External Services
```
┌─ Google Drive (recordings source)
├─ OpenAI API (transcription)
├─ Anthropic API (analysis)
└─ Notion API (database)
```

### Data Storage
```
~/koreanlearning/
├─ .env (credentials)
├─ output/
│  ├─ auto_fetch_state.json (tracking)
│  ├─ *.json (transcripts)
│  └─ *_analysis.json (Claude results)
├─ recordings/ (temp local copies)
└─ scripts/launchd/
   └─ com.koreanlearning.autofetch.plist
```

## Error Handling & Resilience

**Retry Logic:**
- Whisper API rate limits → Auto-retry
- Notion API timeouts → Exponential backoff
- FFmpeg failures → Log and continue

**State Management:**
- Progress saved to JSON
- Can resume after interruption
- `--reset` flag restarts from scratch

**Logging:**
- Comprehensive logs in output/
- Separate stdout and stderr
- Timestamps for debugging

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Audio extraction | 30 sec | FFmpeg, 85-min video |
| Transcription | 5 min | 5 chunks × Whisper API |
| Analysis | 2 min | Claude Sonnet 4 |
| Deduplication | 2 sec | Direct Notion API query |
| Upload | 1 min | Batch create pages |
| **Total** | **~10 min** | End-to-end processing |

---

For implementation details, see individual module files and inline code comments.
