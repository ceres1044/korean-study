#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-fetch new Google Drive recordings, process them, then remove local copy.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Config
SOURCE_DIR = Path(
    "/Users/jingchen/Library/CloudStorage/GoogleDrive-thisisjingchen@gmail.com/My Drive/Meet Recordings/Korean Lessons"
)
DEST_DIR = Path("/Users/jingchen/code/koreanlearning/recordings")
STATE_FILE = Path("/Users/jingchen/code/koreanlearning/output/auto_fetch_state.json")
LOG_FILE = Path("/Users/jingchen/code/koreanlearning/output/auto_fetch.log")

VIDEO_EXTS = {".mp4", ".m4v", ".mov"}


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"processed": {}}
    return {"processed": {}}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def list_videos(source_dir: Path) -> list[Path]:
    if not source_dir.exists():
        return []
    return sorted(
        [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS],
        key=lambda p: p.stat().st_mtime,
    )


def run_processor(local_path: Path) -> bool:
    cmd = [
        sys.executable,
        "/Users/jingchen/code/koreanlearning/main_processor.py",
        str(local_path),
    ]
    result = subprocess.run(cmd, cwd="/Users/jingchen/code/koreanlearning")
    return result.returncode == 0


def main() -> None:
    log("Auto-fetch run started")

    state = load_state()
    processed = state.get("processed", {})

    DEST_DIR.mkdir(parents=True, exist_ok=True)

    videos = list_videos(SOURCE_DIR)
    if not videos:
        log("No videos found in source folder")
        return

    for video_path in videos:
        video_key = f"{video_path.name}:{video_path.stat().st_mtime}"
        if video_key in processed:
            continue

        log(f"New video detected: {video_path.name}")

        local_copy = DEST_DIR / video_path.name
        try:
            shutil.copy2(video_path, local_copy)
            log(f"Copied to local: {local_copy}")

            success = run_processor(local_copy)
            if success:
                log(f"Processed successfully: {video_path.name}")
                processed[video_key] = {
                    "name": video_path.name,
                    "processed_at": datetime.now().isoformat(),
                }
                # Remove local copy to save disk space
                try:
                    local_copy.unlink(missing_ok=True)
                    log(f"Deleted local copy: {local_copy}")
                except Exception as e:
                    log(f"Failed to delete local copy: {e}")
            else:
                log(f"Processing failed: {video_path.name}")
        except Exception as e:
            log(f"Error handling {video_path.name}: {e}")

    state["processed"] = processed
    save_state(state)
    log("Auto-fetch run completed")


if __name__ == "__main__":
    main()
