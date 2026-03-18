# 🇰🇷 Korean Learning Automation System

**Automatically process Korean class recordings → Extract learning materials → Organize in Notion**

Convert hours of Korean lessons into a structured, searchable learning database with zero manual work.

---

## 📌 Problem

You have weekly Korean class recordings but:
- ❌ Transcribing takes hours
- ❌ Manually extracting vocabulary/phrases is tedious  
- ❌ Organizing in Notion requires constant copy-paste
- ❌ Duplicates keep appearing in your database
- ❌ Session dates get confused with processing dates

## ✅ Solution

Fully automated workflow that runs **every Tuesday & Wednesday at 11:30 AM EST**:

1. **Auto-detects** new videos in Google Drive
2. **Transcribes** entire 85-minute videos using OpenAI Whisper (splits into chunks to bypass 25MB limit)
3. **Extracts** vocabulary, phrases, grammar points, corrections with Claude Sonnet AI
4. **Parses dates** from filenames (no manual date entry)
5. **Deduplicates** by Korean text (prevents duplicate entries)
6. **Uploads** organized materials to Notion database
7. **Cleans up** local files to save disk space

**Result:** 249+ unique Korean learning items organized in Notion, zero duplicates, automatic updates

---

## 🚀 Quick Start

### Prerequisites
- macOS (launchd scheduler)
- Python 3.10+
- FFmpeg (for audio extraction)
- API Keys: OpenAI, Anthropic Claude, Notion

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/korean-learning-automation.git
cd korean-learning-automation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

### 3. Setup Notion Database
See [docs/NOTION_TEMPLATES.md](docs/NOTION_TEMPLATES.md) for database schema

### 4. Enable Auto-fetch Schedule
```bash
# Load the LaunchAgent (first time only)
launchctl load ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist

# If already loaded, start it manually with:
launchctl start com.koreanlearning.autofetch

# Check if it's loaded:
launchctl list | grep koreanlearning
```

### 5. Done!
New videos in Google Drive folder are automatically processed every Tuesday & Wednesday

---

## 📊 Features

| Feature | Status | Details |
|---------|--------|---------|
| **Auto-Detection** | ✅ | Detects new videos by filename + modification timestamp |
| **Audio Chunking** | ✅ | Splits large videos into 20-min MP3 chunks (~4.6MB each) |
| **Transcription** | ✅ | OpenAI Whisper with Korean language support |
| **Analysis** | ✅ | Claude Sonnet extracts vocab, phrases, grammar, corrections |
| **Date Parsing** | ✅ | Extracts dates from filenames (MM_DD_YYYY format) |
| **Deduplication** | ✅ | Prevents duplicate Notion entries via direct API query |
| **Confidence Filtering** | ✅ | Skips low-confidence items (except corrections) |
| **Resume Capability** | ✅ | Tracks progress, can resume interrupted processing |
| **Automatic Cleanup** | ✅ | Deletes local copies after successful processing |
| **Scheduled Execution** | ✅ | Runs via macOS launchd (Tuesday/Wednesday 11:30 AM EST) |

---

## 📁 Project Structure

```
korean-learning-automation/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── LICENSE                            # MIT License
│
├── auto_fetch.py                      # Auto-detection & orchestration
├── main_processor.py                  # Main pipeline orchestrator
├── claude_analyzer.py                 # Claude AI analysis
├── notion_sender.py                   # Notion API integration
├── state_manager.py                   # Progress tracking
│
├── docs/
│   ├── SETUP.md                       # Detailed setup instructions
│   ├── NOTION_TEMPLATES.md            # Notion database schema
│   ├── TROUBLESHOOTING.md             # Common issues & fixes
│   └── ARCHITECTURE.md                # System design details
│
├── scripts/
│   ├── cleanup_duplicates.py          # One-time duplicate cleanup
│   ├── launchd/
│   │   └── com.koreanlearning.autofetch.plist  # Schedule config
│   └── update_session_dates.py        # Manual date correction
│
├── output/                            # Generated files
│   ├── *.json                         # Transcripts & analyses
│   ├── auto_fetch.log                 # Execution logs
│   └── auto_fetch_state.json          # Processing state
│
└── recordings/                        # Temporary local copies (auto-deleted)
```

---

## 🔧 How It Works

### Detection & Scheduling
- **Trigger:** macOS launchd runs at Tuesday/Wednesday 11:30 AM EST
- **Detection:** `auto_fetch.py` scans Google Drive folder
- **Key:** Uses `{filename}:{modification_timestamp}` fingerprint to identify new files
- **State:** Tracks processed videos in `output/auto_fetch_state.json`

### Processing Pipeline
```
1. auto_fetch.py (detects new video)
   ↓
2. main_processor.py (orchestrates)
   ├─ extract_audio_chunks() → FFmpeg splits into 20-min MP3s
   ├─ transcribe_audio_chunks() → OpenAI Whisper API
   ├─ parse_session_date() → Extracts YYYY-MM-DD from filename
   ├─ analyze_transcript() → Claude Sonnet (16k tokens)
   └─ send_to_notion() → Direct API query + dedup + upload
3. Auto-cleanup (delete local copy)
```

### Deduplication Strategy
- **Query existing entries** via `POST /databases/{id}/query` (direct REST API)
- **Extract Korean text** from all existing pages
- **Skip items** where Korean text matches existing entries
- **Result:** Zero duplicate entries in Notion

---

## 📈 Results

**Sample Run (Korean_Class_11_24_2025):**
```
Audio:        91.1 minutes → 5 chunks (~4.6MB each)
Transcription: 20,552 characters
Analysis:     70 items extracted (32 vocab, 28 phrases, 15 grammar, 12 corrections)
Dedup:        12 duplicates skipped
Upload:       58 new items to Notion
Total DB:     249 unique Korean learning items
```

---

## 🛠️ Tech Stack

- **Audio:** FFmpeg (extraction), FFprobe (duration detection)
- **Transcription:** OpenAI Whisper API (whisper-1 model)
- **Analysis:** Anthropic Claude Sonnet 4 (max_tokens=16000)
- **Database:** Notion API (direct REST calls via `requests`)
- **Scheduling:** macOS launchd (StartCalendarInterval)
- **State Management:** JSON file tracking

---

## 📚 Documentation

- **[SETUP.md](docs/SETUP.md)** - Step-by-step installation & configuration
- **[NOTION_TEMPLATES.md](docs/NOTION_TEMPLATES.md)** - Database schema & property mapping
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues & solutions
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design & module overview

---

## 🚨 Troubleshooting

**Auto-fetch not running?**
- Check if launchd is loaded: `launchctl list | grep korean`
- View logs: `tail -f output/auto_fetch.log`
- Manually trigger: `launchctl start com.koreanlearning.autofetch`
- If already loaded and you get errors, use `launchctl start` instead of `load`
- See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

**Duplicates still appearing?**
- Run cleanup script: `python scripts/cleanup_duplicates.py`
- Check Notion database permissions

**Notion upload fails?**
- Verify API token in `.env`
- Ensure integration is shared with database
- Check for API rate limits

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙋 Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Review logs in `output/auto_fetch.log`
3. Test manually: `python auto_fetch.py`

---

## 🎓 Use Cases

- 📚 **Language Learners:** Build personalized vocabulary databases from class recordings
- 👨‍🏫 **Teachers:** Track what was taught and extract key learning points
- 🔄 **Study Groups:** Share analyzed materials automatically
- 📊 **Progress Tracking:** See learning progression over weeks/months

---

**Built with ❤️ for Korean language learners who don't want to spend hours organizing materials manually.**
