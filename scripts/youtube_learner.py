#!/usr/bin/env python3
"""
YouTube Learner
===============
Fetches latest videos from configured channels, extracts transcripts,
and integrates them into the Resonance Ledger as 'external_wisdom'.
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
except ImportError:
    print("❌ Missing dependencies. Run: pip install youtube-transcript-api yt-dlp")
    sys.exit(1)

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
CHANNELS_FILE = WORKSPACE_ROOT / "scripts" / "youtube_channels.json"
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

def load_channels() -> Dict[str, str]:
    with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_latest_videos(channel_name: str, limit: int = 3) -> List[Dict]:
    """Get latest videos using yt-dlp search"""
    # Use ytsearch{limit}:{query} to find videos
    query = f"ytsearch{limit}:{channel_name}"
    
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        query
    ]
    
    videos = []
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    videos.append({
                        'id': data['id'],
                        'title': data['title'],
                        'url': f"https://www.youtube.com/watch?v={data['id']}",
                        'date': data.get('upload_date', 'unknown')
                    })
                except:
                    pass
    except Exception as e:
        print(f"⚠️ Failed to fetch videos for {channel_name}: {e}")
        
    return videos

def get_transcript(video_id: str) -> str:
    """Download transcript using yt-dlp --write-auto-sub"""
    try:
        # Download vtt
        cmd = [
            "yt-dlp",
            "--write-auto-sub",
            "--sub-lang", "ko,en",
            "--skip-download",
            "--output", f"/tmp/{video_id}",
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Read vtt file (try ko first, then en)
        vtt_path = Path(f"/tmp/{video_id}.ko.vtt")
        if not vtt_path.exists():
            vtt_path = Path(f"/tmp/{video_id}.en.vtt")
            
        if vtt_path.exists():
            # Simple VTT parser (remove timestamps)
            lines = []
            with open(vtt_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if '-->' not in line and line.strip() and not line.startswith('WEBVTT'):
                        lines.append(line.strip())
            # Cleanup
            vtt_path.unlink()
            return " ".join(list(dict.fromkeys(lines))) # Remove duplicates
            
        return ""
    except Exception as e:
        print(f"   (Transcript error: {e})")
        return ""

def save_to_ledger(video: Dict, transcript: str, channel_name: str):
    """Save learned content to resonance ledger"""
    if not transcript:
        return

    # Create summary (first 200 chars + title)
    summary = f"[{channel_name}] {video['title']}"
    
    # Create entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "external_wisdom",
        "summary": summary,
        "narrative": transcript[:2000] + "...", # Truncate for now, RAG handles chunking ideally
        "vector": None, # RAG will handle embedding later or we can add it here if we import RAG
        "metadata": {
            "source": "youtube",
            "channel": channel_name,
            "video_id": video['id'],
            "url": video['url'],
            "upload_date": video['date']
        }
    }
    
    # Append to ledger
    with open(LEDGER_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"✅ Learned: {summary}")

def main():
    print("📺 YouTube Learner Started")
    print("=" * 40)
    
    channels = load_channels()
    total_learned = 0
    
    for name, _ in channels.items():
        if "CHANNEL_ID_HERE" in name: # Skip placeholders if any
            continue
            
        print(f"\n📡 Scanning channel: {name}...")
        videos = get_latest_videos(name, limit=2) # Search by name
        
        for video in videos:
            # Check if already learned (simple check)
            # In production, check ledger for video_id
            
            print(f"   Processing: {video['title']}")
            transcript = get_transcript(video['id'])
            
            if transcript:
                save_to_ledger(video, transcript, name)
                total_learned += 1
            else:
                print("   (Skipped: No transcript)")
                
            time.sleep(1) # Be polite to YouTube
            
    print("\n" + "=" * 40)
    print(f"🎉 Learning Complete. Total new wisdom: {total_learned}")

if __name__ == "__main__":
    main()
