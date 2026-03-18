#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
State Manager for Korean Learning Pipeline
==========================================
Tracks progress so scripts can resume after interruption
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class StateManager:
    """Manages pipeline state across script runs"""
    
    def __init__(self, session_name: str, output_dir: str = "output"):
        self.session_name = session_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.state_file = self.output_dir / f"{session_name}_progress.json"
        self.state = self.load_state()
    
    def load_state(self) -> Dict[str, Any]:
        """Load existing state or create new"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Default state
        return {
            "session_name": self.session_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "steps_completed": {
                "video_fetched": False,
                "audio_extracted": False,
                "transcript_created": False,
                "analysis_done": False,
                "sent_to_notion": False
            },
            "files": {
                "video_path": None,
                "audio_path": None,
                "transcript_path": None,
                "analysis_path": None
            },
            "metadata": {
                "session_date": None,
                "duration_seconds": None,
                "total_items_extracted": None
            }
        }
    
    def save_state(self):
        """Save current state"""
        self.state["updated_at"] = datetime.now().isoformat()
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def mark_completed(self, step: str, **kwargs):
        """Mark a step as completed with optional metadata"""
        if step in self.state["steps_completed"]:
            self.state["steps_completed"][step] = True
        
        # Update files/metadata
        for key, value in kwargs.items():
            if key in self.state["files"]:
                self.state["files"][key] = str(value) if value else None
            elif key in self.state["metadata"]:
                self.state["metadata"][key] = value
        
        self.save_state()
    
    def is_completed(self, step: str) -> bool:
        """Check if a step is completed"""
        return self.state["steps_completed"].get(step, False)
    
    def get_file(self, file_type: str) -> Optional[Path]:
        """Get path to a file"""
        path_str = self.state["files"].get(file_type)
        if path_str and Path(path_str).exists():
            return Path(path_str)
        return None
    
    def reset(self, step: str = None):
        """Reset progress (optionally from a specific step)"""
        if step is None:
            # Reset everything
            for key in self.state["steps_completed"]:
                self.state["steps_completed"][key] = False
        else:
            # Reset from this step onwards
            reset_order = [
                "video_fetched",
                "audio_extracted",
                "transcript_created",
                "analysis_done",
                "sent_to_notion"
            ]
            if step in reset_order:
                idx = reset_order.index(step)
                for s in reset_order[idx:]:
                    self.state["steps_completed"][s] = False
        
        self.save_state()
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        steps = self.state["steps_completed"]
        completed = [k for k, v in steps.items() if v]
        
        lines = [
            f"Session: {self.session_name}",
            f"Progress: {len(completed)}/5 steps completed",
            ""
        ]
        
        status_icon = {True: "✅", False: "⬜"}
        for step, done in steps.items():
            lines.append(f"  {status_icon[done]} {step.replace('_', ' ').title()}")
        
        return "\n".join(lines)


def cleanup_audio_files(state: StateManager, keep_transcript: bool = True):
    """
    Clean up audio files after successful transcription
    Keeps transcript JSON for future reference
    """
    audio_path = state.get_file("audio_path")
    
    if audio_path and audio_path.exists():
        # Also remove chunk files if they exist
        chunk_pattern = audio_path.parent / f"{audio_path.stem}_chunk_*.wav"
        import glob
        for chunk in glob.glob(str(chunk_pattern)):
            try:
                Path(chunk).unlink()
                print(f"🗑️  Deleted audio chunk: {Path(chunk).name}")
            except:
                pass
        
        # Delete main audio file
        try:
            audio_path.unlink()
            print(f"🗑️  Deleted audio file: {audio_path.name}")
        except Exception as e:
            print(f"⚠️  Could not delete audio: {e}")
