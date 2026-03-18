# Setup Guide

Complete step-by-step instructions to get Korean Learning Automation running.

## Prerequisites

- **macOS** (launchd scheduler is macOS-specific)
- **Python 3.10+** 
- **FFmpeg** (for audio extraction)
- **API Keys:**
  - OpenAI (Whisper transcription)
  - Anthropic Claude (text analysis)
  - Notion (database integration)
- **Google Drive folder** with Korean class recordings

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/korean-learning-automation.git
cd korean-learning-automation
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**Manual install (if needed):**
```bash
pip install python-dotenv openai anthropic requests notion-client
```

### 4. Install FFmpeg
```bash
# macOS with Homebrew
brew install ffmpeg

# Verify installation
ffmpeg -version
```

## Configuration

### 1. Create .env File
```bash
cp .env.example .env
nano .env  # or open in your editor
```

### 2. Add API Keys

**OpenAI:**
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Add to `.env`:
```
OPENAI_API_KEY=sk-proj-...
```

**Anthropic Claude:**
1. Go to https://console.anthropic.com/
2. Create API key
3. Add to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

**Notion:**
1. Go to https://www.notion.com/profile/integrations
2. Create new integration
3. Share with your database
4. Get database ID from URL: `https://notion.so/{DATABASE_ID}?v=...`
5. Add to `.env`:
```
NOTION_TOKEN=ntn_...
NOTION_DATABASE_ID=2fec304724b580a09dc7dda515f728ea
```

### 3. Configure Settings
```
TEACHER_NAME=Cathy
STUDENT_NAME=Jing
AUTO_SEND_TO_NOTION=false
CONFIDENCE_THRESHOLD=medium
```

### 4. Setup Notion Database

See [NOTION_TEMPLATES.md](NOTION_TEMPLATES.md) for:
- Database schema
- Property definitions
- Recommended views & filters

## Google Drive Setup

### 1. Create Folder Structure
```
Google Drive/
└── Meet Recordings/
    └── Korean Lessons/
        ├── Korean_Class_11_10_2025.mp4
        ├── Korean_Class_11_17_2025.mp4
        └── ... (more recordings)
```

### 2. Sync with Mac
- Use Google Drive for Mac (installed)
- Ensure "Korean Lessons" folder is synced locally
- Path: `~/Library/CloudStorage/GoogleDrive-{email}/My Drive/Meet Recordings/Korean Lessons`

## Testing

### 1. Manual Test Run
```bash
python auto_fetch.py
```

Expected output:
```
🔍 Auto-fetch run started
New video detected: Korean_Class_12_08_2025.mp4
Copied to local: recordings/Korean_Class_12_08_2025.mp4
... [full processing pipeline] ...
✅ Complete! Processed 1 video
```

### 2. Check Logs
```bash
cat output/auto_fetch.log
```

### 3. Verify Notion Upload
- Check your Notion database
- Should see new entries with today's session

## Enable Auto-Scheduling

### 1. Install Scheduler Config
```bash
cp scripts/launchd/com.koreanlearning.autofetch.plist \
   ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist
```

### 2. Load into launchd
```bash
launchctl load ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist
```

### 3. Verify It's Active
```bash
launchctl list | grep koreanlearning
```

Output should show:
```
-       0       com.koreanlearning.autofetch
```

### 4. Check Execution
- Check runs at Monday/Tuesday 11:30 AM EST
- Logs: `output/auto_fetch.stdout.log`

## Run Modes

### Manual Execution
```bash
# Run detection and processing once
python auto_fetch.py

# Process specific video
python main_processor.py recordings/Korean_Class_12_08_2025.mp4

# Reprocess from scratch
python main_processor.py recordings/Korean_Class_12_08_2025.mp4 --reset
```

### Scheduled Execution
- Automatically runs Monday/Tuesday 11:30 AM EST
- No manual intervention needed
- Computer must be on and connected to internet

## Configuration Options

### Change Execution Schedule
Edit `scripts/launchd/com.koreanlearning.autofetch.plist`:

```xml
<key>StartCalendarInterval</key>
<array>
  <dict>
    <key>Weekday</key>
    <integer>2</integer>        <!-- Monday -->
    <key>Hour</key>
    <integer>11</integer>
    <key>Minute</key>
    <integer>30</integer>
  </dict>
</array>
```

Then reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist
launchctl load ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist
```

### Change Google Drive Folder
Edit `auto_fetch.py`:
```python
SOURCE_DIR = Path("/path/to/your/google/drive/folder")
```

### Change Confidence Threshold
Edit `.env`:
```
CONFIDENCE_THRESHOLD=high    # Only high-confidence items
CONFIDENCE_THRESHOLD=medium  # Default (medium + high)
CONFIDENCE_THRESHOLD=low     # All items
```

## Uninstall

### Stop Auto-Scheduling
```bash
launchctl unload ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist
```

### Remove Files
```bash
rm ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist
rm -rf ~/path/to/korean-learning-automation
```

## Next Steps

1. ✅ Complete setup (you are here)
2. 📚 [Review Notion database schema](NOTION_TEMPLATES.md)
3. 🧪 Run first manual test
4. ⏰ Enable auto-scheduling
5. 📖 Read [troubleshooting guide](TROUBLESHOOTING.md) for common issues

---

**Need help?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
