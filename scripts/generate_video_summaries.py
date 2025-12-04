#!/usr/bin/env python3
"""
Generate Video Summaries
========================
Creates contact sheet images for video files using ffmpeg.
"""
import subprocess
import json
import sys
from pathlib import Path

INPUT_DIR = Path("/home/bino/agi/input/obs_recode")
OUTPUT_DIR = Path("/home/bino/agi/outputs/video_summaries")

def get_duration(file_path):
    """Get video duration in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration for {file_path.name}: {e}")
        return None

def generate_summary(file_path):
    """Generate a 5x5 contact sheet."""
    try:
        duration = get_duration(file_path)
        if not duration:
            return
            
        # Calculate interval to get ~25 frames
        # We want 25 frames total. Interval = duration / 25
        interval = duration / 25
        fps = 1 / interval
        
        output_file = OUTPUT_DIR / f"summary_{file_path.stem}.jpg"
        
        print(f"Processing {file_path.name} (Duration: {duration/60:.1f}m)...")
        
        # ffmpeg command
        # fps filter: extract frames at calculated rate
        # scale: resize to reasonable width
        # tile: arrange in 5x5 grid
        cmd = [
            "ffmpeg",
            "-y", # Overwrite
            "-i", str(file_path),
            "-vf", f"fps={fps:.4f},scale=480:-1,tile=5x5",
            "-frames:v", "1",
            "-q:v", "2", # High quality jpeg
            str(output_file)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Generated: {output_file}")
        return output_file
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to process {file_path.name}: {e.stderr}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    if not INPUT_DIR.exists():
        print(f"Input directory not found: {INPUT_DIR}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    videos = sorted(list(INPUT_DIR.glob("2025-12-01*.mp4")))
    print(f"Found {len(videos)} videos (Targeting 2025-12-01).")
    
    for video in videos:
        generate_summary(video)

if __name__ == "__main__":
    main()
