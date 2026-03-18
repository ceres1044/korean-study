# Troubleshooting Guide

Common issues and solutions for Korean Learning Automation.

## Auto-Fetch Not Running

### Issue: Scheduled task doesn't execute at 11:30 AM

**Check if launchd is loaded:**
```bash
launchctl list | grep koreanlearning
```

Expected output:
```
-       0       com.koreanlearning.autofetch
```

If not listed:
```bash
launchctl load ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist
```

**Check logs:**
```bash
tail -f ~/code/koreanlearning/output/auto_fetch.stdout.log
tail -f ~/code/koreanlearning/output/auto_fetch.stderr.log
```

### Issue: Computer was asleep during scheduled time

**Solution:** launchd won't wake sleeping computers. Keep Mac awake during scheduled times or adjust schedule to when you're working.

### Issue: Timezone incorrect

**Check timezone in plist:**
```bash
cat ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist | grep -A1 "TZ"
```

Should show:
```
<key>TZ</key>
<string>America/New_York</string>
```

If incorrect, reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist
launchctl load ~/Library/LaunchAgents/com.koreanlearning.autofetch.plist
```

---

## Notion Upload Failing

### Issue: "Could not connect to Notion database"

**Check API token:**
```bash
grep NOTION_TOKEN .env
```

**Verify token is valid:**
```bash
curl -H "Authorization: Bearer {YOUR_TOKEN}" \
     https://api.notion.com/v1/users/me
```

Should return user info, not error.

### Issue: "Database not found"

**Verify database ID:**
1. Open Notion database
2. URL: `https://notion.so/{DATABASE_ID}?v=...`
3. Check ID in `.env`

**Ensure integration is connected:**
1. Go to Notion settings
2. Click "Connections" → "Manage connections"
3. Search for your integration
4. Click "Connect" if not already connected

### Issue: Permission denied

**Re-share database with integration:**
1. Open database
2. Click "Share" button
3. Search for your integration name
4. Add with read/write access

---

## Audio Processing Issues

### Issue: "FFmpeg not found"

```bash
ffmpeg -version
```

If not installed:
```bash
brew install ffmpeg
```

Verify:
```bash
which ffmpeg
which ffprobe
```

### Issue: "Video file too large"

System automatically handles this by chunking into 20-minute MP3s.

Check chunk size in logs:
```bash
grep "MB" output/auto_fetch.stdout.log
```

Should show chunks ~4.6MB each.

### Issue: Audio extraction taking too long

Normal timing:
- 85-min video: ~30 seconds extraction
- 5 chunks → ~5 minutes transcription

If slower:
- Check disk space: `df -h`
- Check CPU: `top -n 1 | head -20`
- Check internet: `ping 8.8.8.8`

---

## Transcription Problems

### Issue: "Whisper API rate limit exceeded"

**Wait and retry:**
- API resets every minute
- System will auto-retry
- Check logs for backoff timing

### Issue: "Audio quality too poor to transcribe"

**Check:**
- Video has audio track
- Audio is in Korean
- Volume isn't too low

**Solution:**
- Improve source video quality
- Manually provide transcript

### Issue: Transcription incomplete or garbled

**Check logs:**
```bash
grep "Chunk.*done" output/auto_fetch.stdout.log
```

Should show 5 chunks successfully transcribed.

If one chunk fails:
- Check file size (should be ~4.6MB)
- Retry manually:
```bash
python main_processor.py recordings/Korean_Class_MM_DD_YYYY.mp4 --reset
```

---

## Claude Analysis Issues

### Issue: "Claude API error" or timeout

**Check token:**
```bash
grep ANTHROPIC_API_KEY .env
```

**Check status:**
```bash
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: {YOUR_KEY}" \
  -H "anthropic-version: 2023-06-01"
```

### Issue: Extracted items incomplete or wrong

**Common causes:**
- Transcript too short (system needs min 100 characters)
- Language not Korean
- Low transcript quality

**Check transcript:**
```bash
cat output/Korean_Class_MM_DD_YYYY.json | head -50
```

**Manual analysis:**
```bash
python claude_analyzer.py --input output/Korean_Class_MM_DD_YYYY.json
```

### Issue: Confidence scores unrealistic

System assigns:
- High: Clear, confident extractions
- Medium: Reasonable but context-dependent
- Low: Uncertain or unclear

This is normal. Filter by confidence in Notion if needed.

---

## Deduplication Issues

### Issue: Duplicates appearing in Notion

**Likely cause:** Dedup check failed but upload succeeded

**Check dedup logs:**
```bash
grep "Found.*existing" output/auto_fetch.stdout.log
```

**Manual cleanup:**
```bash
python scripts/cleanup_duplicates.py
```

**Re-run with fresh dedup:**
```bash
python auto_fetch.py
```

### Issue: Valid items being skipped as duplicates

**Check state file:**
```bash
cat output/auto_fetch_state.json
```

**Clear state to reprocess:**
```bash
rm output/auto_fetch_state.json
python auto_fetch.py
```

---

## File Organization Issues

### Issue: Google Drive folder not syncing

**Verify path:**
```bash
ls -la ~/Library/CloudStorage/GoogleDrive-*/
```

Find your Google Drive:
```bash
ls -la "~/Library/CloudStorage/GoogleDrive-{youremail}/My Drive/Meet Recordings/Korean Lessons/"
```

**Update auto_fetch.py** if path differs:
```python
SOURCE_DIR = Path("/path/to/your/google/drive")
```

### Issue: Local files not being deleted

**Check logs:**
```bash
grep "Deleted local copy" output/auto_fetch.stdout.log
```

**Manual cleanup:**
```bash
rm -f recordings/Korean_Class_*.mp4
```

**Free up space:**
```bash
du -sh recordings/
du -sh output/
```

---

## Date Parsing Issues

### Issue: Wrong session date extracted

**Check filename format:**
```
Korean_Class_MM_DD_YYYY.mp4  ← Required format
```

Wrong formats:
```
Korean Class 2025-11-24.mp4  ← Won't parse
Korean_11-24-2025.mp4        ← Won't parse
```

**Fix:** Rename video to correct format, then reprocess

**Check parsed date:**
```bash
grep "Session Date" output/auto_fetch.stdout.log
```

### Issue: Date off by one day

**Check timezone:**
```bash
date
```

System parses dates in UTC. Adjust if needed in code.

---

## Performance Issues

### Issue: High CPU usage

**Check what's running:**
```bash
top -n 1 | grep -E "python|ffmpeg"
```

**Normal loads:**
- FFmpeg extraction: 20-30% CPU
- Whisper transcription: 5-10% CPU (cloud-based)
- Claude analysis: 1-2% CPU (cloud-based)

### Issue: Slow uploads to Notion

**Check:**
- Database size: `SELECT COUNT(*) FROM database` in Notion
- API rate limits: Notion allows 3 requests/sec
- Network: `ping -c 5 api.notion.com`

---

## Environment & Setup Issues

### Issue: "ModuleNotFoundError: No module named 'openai'"

**Install dependencies:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: ".env file not found"

**Create from template:**
```bash
cp .env.example .env
nano .env
```

### Issue: Wrong Python version

**Check version:**
```bash
python --version
python3 --version
```

**Ensure Python 3.10+:**
```bash
python3.10 -m venv .venv
```

---

## Testing & Debugging

### Manual test run
```bash
python auto_fetch.py
```

### Test Whisper only
```bash
python -c "from openai import OpenAI; print(OpenAI())"
```

### Test Claude only
```bash
python claude_analyzer.py
```

### Test Notion connection
```bash
python notion_sender.py
```

### Full pipeline with specific video
```bash
python main_processor.py recordings/Korean_Class_11_24_2025.mp4 --reset
```

### Check all logs
```bash
tail -f output/*.log
```

---

## Getting Help

1. **Check logs first:**
   ```bash
   cat output/auto_fetch.log
   cat output/auto_fetch.stdout.log
   cat output/auto_fetch.stderr.log
   ```

2. **Test manually:**
   ```bash
   python auto_fetch.py
   ```

3. **Review recent changes:**
   ```bash
   git log --oneline -5
   ```

4. **Check system resources:**
   ```bash
   df -h
   top -n 1
   ```

5. **Verify credentials:**
   ```bash
   grep -E "^[A-Z_]+=" .env | grep -v "#"
   ```

---

## Quick Fixes Checklist

- [ ] launchd is loaded: `launchctl list | grep korean`
- [ ] .env file exists and has valid API keys
- [ ] FFmpeg installed: `which ffmpeg`
- [ ] Notion integration connected in database
- [ ] Google Drive folder syncing locally
- [ ] Sufficient disk space: `df -h`
- [ ] Recent video in Google Drive
- [ ] Computer not in sleep mode

---

Still stuck? Check the full [README.md](../README.md) or [SETUP.md](SETUP.md)
