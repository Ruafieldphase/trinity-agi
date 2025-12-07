import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add workspace root to path to import vision_cortex
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.append(str(WORKSPACE_ROOT))

try:
    from scripts.vision_cortex import VisionCortex
except ImportError:
    print("Error: Could not import VisionCortex. Make sure you are running from the workspace root.")
    sys.exit(1)

def get_channel_videos(channel_url: str) -> List[Dict[str, str]]:
    """Get all video URLs from the channel using yt-dlp."""
    print(f"🔍 Fetching video list from {channel_url}...")
    try:
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            '--flat-playlist',
            '--print', '%(url)s\t%(title)s\t%(duration)s',
            channel_url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        
        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            parts = line.split('\t')
            if len(parts) >= 2:
                videos.append({
                    'url': parts[0],
                    'title': parts[1],
                    'duration': float(parts[2]) if len(parts) > 2 and parts[2] != 'NA' else 0.0
                })
        return videos
    except Exception as e:
        print(f"Error fetching channel videos: {e}")
        return []

def extract_frame_from_stream(video_url: str, output_path: Path, timestamp: float) -> bool:
    """Extract a frame from a YouTube video stream at a specific timestamp."""
    try:
        # Get direct stream URL
        stream_url_cmd = [sys.executable, '-m', 'yt_dlp', '-f', 'best', '-g', video_url]
        stream_url_proc = subprocess.run(stream_url_cmd, capture_output=True, text=True, check=True)
        stream_url = stream_url_proc.stdout.strip()
        
        cmd = [
            'ffmpeg',
            '-ss', str(timestamp),
            '-i', stream_url,
            '-frames:v', '1',
            '-q:v', '2',
            '-y',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        # print(f"Error extracting frame: {e}") # Suppress for cleaner output
        return False

def generate_markdown_report(results: List[Dict[str, Any]], output_dir: Path):
    """Generate a comprehensive markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_path = output_dir / "youtube_channel_synesthetic_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# 📺 YouTube Channel Synesthetic Resonance Report\n\n")
        f.write(f"**Generated**: {timestamp}\n")
        f.write(f"**Total Videos Analyzed**: {len(results)}\n\n")
        
        f.write("---\n\n")
        
        for video_data in results:
            video_title = video_data['title']
            f.write(f"## 🎬 {video_title}\n\n")
            f.write(f"- **URL**: `{video_data['url']}`\n")
            f.write(f"- **Duration**: {video_data['duration']:.1f}s\n")
            f.write(f"- **Frames Analyzed**: {len(video_data['frames'])}\n\n")
            
            f.write("### 🌊 Sensory Timeline\n\n")
            
            for frame in video_data['frames']:
                analysis = frame['analysis']
                if 'error' in analysis:
                    f.write(f"> ⚠️ **{frame['timestamp']}s**: Analysis Failed - {analysis['error']}\n\n")
                    continue
                    
                synesthesia = analysis.get('synesthesia', {})
                mood = analysis.get('mood', 'Unknown')
                score = analysis.get('resonance_score', 0.0)
                poetic = analysis.get('poetic_interpretation', '')
                
                f.write(f"#### ⏱️ {frame['timestamp']}s (Resonance: {score})\n")
                f.write(f"> *\"{poetic}\"*\n\n")
                f.write(f"- **Mood**: {mood}\n")
                f.write(f"- **👃 Smell**: {synesthesia.get('smell', 'N/A')}\n")
                f.write(f"- **✋ Touch**: {synesthesia.get('touch', 'N/A')}\n")
                f.write(f"- **👅 Taste**: {synesthesia.get('taste', 'N/A')}\n")
                f.write("\n")
            
            f.write("---\n\n")
            
    print(f"\n✨ Report generated: {report_path}")

def main():
    parser = argparse.ArgumentParser(description="Analyze YouTube channel for Synesthetic Resonance.")
    parser.add_argument("--channel", required=True, help="YouTube Channel URL")
    parser.add_argument("--interval", type=int, default=60, help="Analysis interval in seconds")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of videos to process (0 = all)")
    
    args = parser.parse_args()
    
    channel_url = args.channel
    interval = args.interval
    
    # Setup directories
    output_base = WORKSPACE_ROOT / "outputs" / "youtube_channel_analysis"
    temp_frames_dir = output_base / "temp_frames"
    output_base.mkdir(parents=True, exist_ok=True)
    temp_frames_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Vision Cortex
    print("👁️ Initializing Vision Cortex...")
    cortex = VisionCortex()
    
    # Get videos
    videos = get_channel_videos(channel_url)
    print(f"Found {len(videos)} videos in channel.")
    
    if args.limit > 0:
        videos = videos[:args.limit]
        print(f"Limiting to first {args.limit} videos.")
    
    results = []
    partial_json_path = output_base / "youtube_analysis_partial.json"
    
    # Load partial results
    processed_urls = set()
    if partial_json_path.exists():
        try:
            with open(partial_json_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
                processed_urls = {r['url'] for r in results}
            print(f"Loaded {len(results)} previously processed videos.")
        except Exception as e:
            print(f"Error loading partial results: {e}")
            
    # Load Contextual Perspectives
    try:
        perspectives_path = WORKSPACE_ROOT / "data" / "contextual_perspectives.json"
        with open(perspectives_path, "r", encoding="utf-8") as f:
            perspectives_data = json.load(f)
            patterns = perspectives_data.get("patterns", [])
            
            lenses_text = ""
            for i, p in enumerate(patterns, 1):
                if "perspective" in p:
                    lenses_text += f"{i}. **{p['perspective']} ({p.get('source', 'Unknown')}):** {p['thought']}\n"
                elif "patterns" in p: # Handle nested structure if any
                     for j, sub_p in enumerate(p["patterns"], 1):
                        lenses_text += f"{i}-{j}. **{sub_p['perspective']} ({sub_p.get('source', 'Unknown')}):** {sub_p['thought']}\n"

    except Exception as e:
        print(f"Warning: Could not load contextual perspectives: {e}")
        lenses_text = "Analyze this frame for hidden patterns and structural meaning."

    for i, video in enumerate(videos):
        if video['url'] in processed_urls:
            print(f"[{i+1}/{len(videos)}] Skipping {video['title']} (Already Processed)")
            continue
            
        print(f"\n[{i+1}/{len(videos)}] Processing: {video['title']}")
        print(f"  Duration: {video['duration']:.1f}s")
        
        video_result = {
            "title": video['title'],
            "url": video['url'],
            "duration": video['duration'],
            "frames": []
        }
        
        current_time = 0.0
        timestamps = []
        while current_time < video['duration']:
            timestamps.append(current_time)
            current_time += interval
            
        # Limit frames per video
        if len(timestamps) > 10:
             step = len(timestamps) // 10
             timestamps = timestamps[::step][:10]
             print(f"  (Sampling 10 frames out of {len(timestamps) * step})")
        
        for ts in timestamps:
            print(f"  - Analyzing frame at {ts}s...", end="", flush=True)
            
            frame_path = temp_frames_dir / f"frame_{i}_{int(ts)}.jpg"
            
            if extract_frame_from_stream(video['url'], frame_path, ts):
                context = (
                    f"This video is being analyzed by an AI seeking to understand the world through specific 'Cognitive Lenses'. "
                    f"Title: {video['title']}. "
                    f"ANALYZE THIS FRAME THROUGH THE FOLLOWING LENSES:\n"
                    f"{lenses_text}"
                    f"SYNTHESIZE these perspectives into a poetic and analytical description."
                )
                analysis = cortex.analyze_image(str(frame_path), context=context)
                
                video_result['frames'].append({
                    "timestamp": ts,
                    "analysis": analysis
                })
                
                try:
                    frame_path.unlink()
                except:
                    pass
                
                if analysis.get('status') == 'success':
                    print(" Done.")
                    time.sleep(5) # Normal breathing
                else:
                    error_msg = analysis.get('error', 'Unknown error')
                    print(f" Failed: {error_msg}")
                    if "429" in error_msg or "quota" in error_msg.lower():
                        print(" 🛑 Quota Exceeded. Taking a deep breath (Resting for 60s)...")
                        time.sleep(60) # Deep rest
                    else:
                        time.sleep(5)
            else:
                print(" Extraction Failed.")
                
        results.append(video_result)
        
        with open(partial_json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  Saved partial results.")
        
    generate_markdown_report(results, output_base)

if __name__ == "__main__":
    main()
