#About the user

Non-technical, korean learner, can read korean, listenining is better than speaking and writting in daily conversation setting, have difficulties express self despite learning most grammar points, lack of vocabulary but lack of practice. The user use VS code to build this tool.  

# Product Goals

A complete, automated workflow to:
- ✅ Fetch new weekly Korean session recording with Cathy from Google Drive App 
- ✅ Transcribe recording using Whisper cloud service
- ✅ Extract vocabulary, phrases, and corrections automatically
- ✅ Translate everything to English
- ✅ Organize learning materials in Notion to build a interactive learning database
- ✅ Flag items for review based on confidence
- ✅ Track your progress over time


## The Workflow

```
You have a Korean class with Cathy (recorded in Google Meet)
                    ↓
Fetch recording from Google Drive
                    ↓
Run: python3 main_processor.py recordings/Korean_Class_MM_DD_YYYY.mp4
                    ↓
        [AUTOMATIC PROCESSING]
                    ↓
1. Extract audio from video (30 seconds)
   - Splits into 20-minute chunks (~4.6MB each)
   - Ensures compliance with Whisper's 25MB limit
                    ↓
2. Transcribe with Whisper AI (10-20 mins per 85-min video)
   - Processes each chunk separately
   - Combines transcripts automatically
   - Cleans up temporary audio files
                    ↓
3. Analyze with Claude AI (2-3 mins)
   - Identify Cathy (teacher) and Jing (student)
   - Extract vocabulary, phrases, grammar points, corrections
   - Translate to English
   - Assign confidence levels
   - max_tokens=16000 for comprehensive analysis
                    ↓
4. Auto-extract session date from filename
   - Korean_Class_11_17_2025.mp4 → 2025-11-17
   - No manual date entry needed
                    ↓
5. Send to Notion with smart deduplication (1 min)
   - Queries existing database entries via direct API
   - Checks Korean text for exact matches
   - Skips duplicates automatically
   - Only uploads new materials
                    ↓
Study from your organized Notion database! 

## Recent Improvements (February 2026)

### 🎯 Session Date Auto-Extraction
- **Problem:** Sessions were dated with processing date (2026-02-05) instead of actual class date
- **Solution:** Added `parse_session_date()` function in `main_processor.py`
- **How it works:** Extracts date from filename format `Korean_Class_MM_DD_YYYY.mp4`
- **Example:** `Korean_Class_11_17_2025.mp4` → Session date: `2025-11-17`
- **Location:** Lines 170-187 in `main_processor.py`

### 🚫 Smart Deduplication System
- **Problem:** Re-uploading sessions created duplicate entries in Notion database
- **Root cause:** `notion-client` library's `databases.query()` method missing/broken
- **Solution:** Direct Notion REST API calls using `requests` library
- **How it works:**
  1. Formats database ID with hyphens: `2fec304724b580a09dc7dda515f728ea` → `2fec3047-24b5-80a0-9dc7-dda515f728ea`
  2. Calls `POST https://api.notion.com/v1/databases/{id}/query`
  3. Paginates through all pages (100 per batch)
  4. Extracts Korean text from each entry
  5. Skips items where Korean text matches existing entries
- **Performance:** Scans 627 pages, identifies 134 unique entries in ~2 seconds
- **Location:** Lines 43-89 in `notion_sender.py`

### 📦 Audio Chunking for Large Files
- **Problem:** 85-minute videos produce 163MB WAV files, exceeding Whisper's 25MB limit
- **Solution:** Split audio into 20-minute MP3 chunks at 32kbps
- **Result:** Each chunk ~4.6MB (well under 25MB limit)
- **Location:** `extract_audio_chunks()` and `transcribe_audio_chunks()` in `main_processor.py`

### Needs
- Delete the audio outputs once full transcripts are ready
- Need a output data format to easily accumulate data gained every session
- Need 2 example sentences in daily conversation setting for every new words, expressions and grammar points
- Notion interface should be easy to view and interact as users are familiar with Notion
- Need seperate py script for video fetching, video->audio->transcript processing, transcript extraction with Claude, publish to Notion. Each script should have code to avoid repetitive work - whenever the code running is interuppted, it can pick up at where it is stopped, unless users explicitily ask to rerun the whole process

