#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korean Learning Session Processor - Main Orchestrator
=====================================================
Coordinates the full pipeline with resume capability

Usage:
    python3 main_processor.py path/to/video.mp4
    python3 main_processor.py path/to/video.mp4 --reset  # Start from scratch
    python3 main_processor.py path/to/video.mp4 --skip-notion  # Don't send to Notion
"""

import sys
import os
from pathlib import Path
import argparse
from typing import Optional
from dotenv import load_dotenv

# Import our modules
from state_manager import StateManager, cleanup_audio_files
from claude_analyzer import analyze_transcript, save_analysis
from notion_sender import send_to_notion, verify_database_connection

# Import from existing scripts
import subprocess
import json
from openai import OpenAI
import anthropic

load_dotenv()

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
TEACHER_NAME = os.getenv("TEACHER_NAME", "Cathy")
STUDENT_NAME = os.getenv("STUDENT_NAME", "Jing")


def print_header(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds using FFprobe"""
    try:
        command = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"⚠️ Could not get video duration: {e}")
        return 0


def extract_audio_chunks(video_path: Path, output_dir: Path, session_name: str) -> list:
    """Extract audio from video in chunks to stay under 25MB limit"""
    print("⏳ Extracting audio from video in chunks...")
    
    try:
        # Get video duration
        duration = get_video_duration(video_path)
        if duration == 0:
            print("❌ Could not determine video duration")
            return []
        
        print(f"📹 Video duration: {duration/60:.1f} minutes")
        
        # Split into 20-minute chunks (well under 25MB at 32kbps)
        chunk_duration = 20 * 60  # 20 minutes in seconds
        num_chunks = int(duration / chunk_duration) + 1
        
        if num_chunks == 1:
            print("📦 Video short enough for single chunk")
        else:
            print(f"📦 Splitting into {num_chunks} chunks of ~20 minutes each")
        
        chunk_files = []
        
        for i in range(num_chunks):
            start_time = i * chunk_duration
            chunk_path = output_dir / f"{session_name}_chunk_{i+1}.mp3"
            
            command = [
                'ffmpeg', '-i', str(video_path),
                '-ss', str(start_time),
                '-t', str(chunk_duration),
                '-vn', '-acodec', 'libmp3lame',
                '-ar', '16000', '-ac', '1',
                '-b:a', '32k',
                '-y', str(chunk_path)
            ]
            
            subprocess.run(command, check=True, capture_output=True)
            
            # Check file size
            file_size_mb = chunk_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ Chunk {i+1}/{num_chunks}: {chunk_path.name} ({file_size_mb:.1f}MB)")
            chunk_files.append(chunk_path)
        
        return chunk_files
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Audio extraction failed: {e}")
        return []


def transcribe_audio_chunks(chunk_files: list, output_path: Path) -> bool:
    """Transcribe audio chunks using OpenAI Whisper API and combine results"""
    print(f"⏳ Transcribing {len(chunk_files)} audio chunk(s) with Whisper...")
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        combined_text = []
        
        for i, chunk_path in enumerate(chunk_files, 1):
            print(f"  📝 Transcribing chunk {i}/{len(chunk_files)}...")
            
            with open(chunk_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ko"
                )
            
            combined_text.append(transcript.text)
            print(f"  ✅ Chunk {i} done ({len(transcript.text)} characters)")
        
        # Combine all transcripts
        full_transcript = " ".join(combined_text)
        
        # Save combined transcript
        transcript_data = {
            "text": full_transcript,
            "language": "ko",
            "chunks": len(chunk_files)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Transcript saved: {output_path.name}")
        print(f"📝 Total length: {len(full_transcript)} characters")
        print(f"📝 Preview: {full_transcript[:200]}...")
        
        # Clean up chunk files
        print(f"\n🧹 Cleaning up {len(chunk_files)} audio chunk(s)...")
        for chunk_path in chunk_files:
            try:
                chunk_path.unlink()
            except Exception as e:
                print(f"  ⚠️ Could not delete {chunk_path.name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return False


def parse_session_date(session_name: str) -> Optional[str]:
    """Parse session date from filename.

    Supports:
    - YYYY-MM-DD
    - *_MM_DD_YYYY (e.g., Korean_Class_11_17_2025)
    """
    if len(session_name) == 10 and session_name.count('-') == 2:
        return session_name

    parts = session_name.split('_')
    if len(parts) >= 3:
        mm, dd, yyyy = parts[-3], parts[-2], parts[-1]
        if mm.isdigit() and dd.isdigit() and yyyy.isdigit() and len(yyyy) == 4:
            return f"{yyyy}-{mm.zfill(2)}-{dd.zfill(2)}"

    return None


def main():
    parser = argparse.ArgumentParser(
        description='Process Korean learning session with resume capability'
    )
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--reset', action='store_true', help='Start from scratch')
    parser.add_argument('--skip-notion', action='store_true', help='Skip Notion upload')
    parser.add_argument('--session-date', help='Session date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"❌ Video file not found: {video_path}")
        sys.exit(1)
    
    # Check API keys
    missing = []
    if not ANTHROPIC_API_KEY: missing.append("ANTHROPIC_API_KEY")
    if not OPENAI_API_KEY: missing.append("OPENAI_API_KEY")
    if not NOTION_TOKEN and not args.skip_notion: missing.append("NOTION_TOKEN")
    if not NOTION_DATABASE_ID and not args.skip_notion: missing.append("NOTION_DATABASE_ID")
    
    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        print("\nPlease set them in your .env file")
        sys.exit(1)
    
    # Initialize state manager
    session_name = video_path.stem
    state = StateManager(session_name)
    
    if args.reset:
        print("🔄 Resetting progress...")
        state.reset()
    
    print_header("KOREAN LEARNING SESSION PROCESSOR")
    print(f"👤 Student: {STUDENT_NAME}")
    print(f"👩‍🏫 Teacher: {TEACHER_NAME}")
    print(f"📁 Session: {session_name}")
    print(f"\n{state.get_summary()}")
    
    # Use path relative to this script so it works regardless of cwd
    _script_dir = Path(__file__).resolve().parent
    output_dir = _script_dir / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Determine session date
    if args.session_date:
        session_date = args.session_date
    else:
        parsed_date = parse_session_date(session_name)
        if parsed_date:
            session_date = parsed_date
        else:
            from datetime import datetime
            session_date = datetime.now().strftime('%Y-%m-%d')
    
    # Define file paths
    transcript_path = output_dir / f"{session_name}.json"
    analysis_path = output_dir / f"{session_name}_analysis.json"
    
    # STEP 1: Extract Audio in Chunks
    chunk_files = []
    if not state.is_completed("audio_extracted"):
        print_header("STEP 1: EXTRACT AUDIO")
        chunk_files = extract_audio_chunks(video_path, output_dir, session_name)
        if chunk_files:
            # Store chunk files as absolute paths so resume works from any cwd
            state.state.setdefault("metadata", {})["chunk_files"] = [str(Path(f).resolve()) for f in chunk_files]
            state.mark_completed("audio_extracted", 
                               video_path=str(video_path))
        else:
            print("❌ Cannot continue without audio")
            sys.exit(1)
    else:
        print("\n✅ Audio already extracted, skipping...")
        # Retrieve chunk files from state (resolve to absolute for any cwd)
        saved_chunks = state.state.get("metadata", {}).get("chunk_files", [])
        chunk_files = [Path(f).resolve() for f in saved_chunks if Path(f).resolve().exists()]
        if not chunk_files and not state.is_completed("transcript_created"):
            # Chunk files missing (e.g. deleted or wrong path) — re-extract
            print("⚠️ Chunk files not found, re-extracting audio...")
            state.state["steps_completed"]["audio_extracted"] = False
            chunk_files = extract_audio_chunks(video_path, output_dir, session_name)
            if chunk_files:
                state.state.setdefault("metadata", {})["chunk_files"] = [str(Path(f).resolve()) for f in chunk_files]
                state.mark_completed("audio_extracted", video_path=str(video_path))
    
    # STEP 2: Transcribe
    if not state.is_completed("transcript_created"):
        print_header("STEP 2: TRANSCRIBE AUDIO")
        if transcribe_audio_chunks(chunk_files, transcript_path):
            state.mark_completed("transcript_created", transcript_path=str(transcript_path))
            
            # Clean up audio files after successful transcription
            cleanup_audio_files(state, keep_transcript=True)
        else:
            print("❌ Cannot continue without transcript")
            sys.exit(1)
    else:
        print("\n✅ Transcript already exists, skipping...")
    
    # STEP 3: Analyze with Claude
    if not state.is_completed("analysis_done"):
        print_header("STEP 3: ANALYZE WITH CLAUDE")
        
        # Load transcript
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        transcript_text = transcript_data.get('text', '')
        
        print(f"📝 Transcript length: {len(transcript_text)} characters")
        print("⏳ Analyzing with Claude (this may take 1-2 minutes)...")
        
        analysis = analyze_transcript(
            transcript_text, 
            session_date, 
            ANTHROPIC_API_KEY,
            TEACHER_NAME,
            STUDENT_NAME
        )
        
        if analysis and save_analysis(analysis, str(analysis_path)):
            total = analysis.get('total_items_extracted', 0)
            stats = analysis.get('statistics', {})
            
            print(f"\n✅ Analysis complete!")
            print(f"📊 Extracted {total} items:")
            print(f"   • Vocabulary: {stats.get('vocabulary_count', 0)}")
            print(f"   • Phrases: {stats.get('phrase_count', 0)}")
            print(f"   • Grammar: {stats.get('grammar_count', 0)}")
            print(f"   • Corrections: {stats.get('correction_count', 0)}")
            
            state.mark_completed("analysis_done", 
                               analysis_path=analysis_path,
                               session_date=session_date,
                               total_items_extracted=total)
        else:
            print("❌ Analysis failed")
            sys.exit(1)
    else:
        print("\n✅ Analysis already complete, skipping...")
    
    # STEP 4: Send to Notion
    if not state.is_completed("sent_to_notion") and not args.skip_notion:
        print_header("STEP 4: SEND TO NOTION")
        
        # Verify connection first
        print("🔍 Verifying Notion connection...")
        success, message = verify_database_connection(NOTION_TOKEN, NOTION_DATABASE_ID)
        print(message)
        
        if not success:
            print("\n💡 Troubleshooting:")
            print("  1. Check your NOTION_DATABASE_ID in .env")
            print("  2. Make sure you've connected the integration to your database")
            print("  3. See NOTION_SETUP.md for detailed instructions")
            
            response = input("\nSkip Notion upload? (y/n): ").strip().lower()
            if response != 'y':
                sys.exit(1)
        else:
            stats = send_to_notion(analysis_path, NOTION_TOKEN, NOTION_DATABASE_ID,
                      skip_duplicates=True, min_confidence="medium")
            
            if stats['success'] > 0:
                state.mark_completed("sent_to_notion")
            
            print(f"\n🎉 Sent {stats['success']} items to Notion!")
    elif args.skip_notion:
        print("\n⏭️  Skipping Notion upload (--skip-notion flag)")
    else:
        print("\n✅ Already sent to Notion, skipping...")
    
    # DONE!
    print_header("✅ PROCESSING COMPLETE")
    print(f"📁 Files created:")
    print(f"   • Transcript: {transcript_path.name}")
    print(f"   • Analysis: {analysis_path.name}")
    print(f"   • Progress: {state.state_file.name}")
    
    if not args.skip_notion and state.is_completed("sent_to_notion"):
        print(f"\n🔗 Check your Notion database!")
    
    print(f"\n💡 To reprocess from scratch: python3 {sys.argv[0]} {video_path} --reset")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
