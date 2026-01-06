import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from workspace_root import get_workspace_root

# Add workspace root to path to import vision_cortex
WORKSPACE_ROOT = get_workspace_root()
sys.path.append(str(WORKSPACE_ROOT))

try:
    from scripts.vision_cortex import VisionCortex
except ImportError:
    print("Error: Could not import VisionCortex. Make sure you are running from the workspace root.")
    sys.exit(1)

def get_video_files(directory: str) -> List[Path]:
    """Recursively find video files in the directory."""
    video_extensions = {'.mp4', '.insv', '.mov', '.mkv', '.avi'}
    video_files = []
    
    # Use os.walk to find files
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if Path(file).suffix.lower() in video_extensions:
                    video_files.append(Path(root) / file)
    except Exception as e:
        print(f"Error scanning directory {directory}: {e}")
        
    return video_files

def extract_frame(video_path: Path, output_path: Path, timestamp: float) -> bool:
    """Extract a single frame from the video at the given timestamp using ffmpeg."""
    try:
        cmd = [
            'ffmpeg',
            '-ss', str(timestamp),
            '-i', str(video_path),
            '-frames:v', '1',
            '-q:v', '2',  # High quality jpeg
            '-y',         # Overwrite output
            str(output_path)
        ]
        
        # Run ffmpeg silently
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception as e:
        print(f"Error extracting frame: {e}")
        return False

def get_video_duration(video_path: Path) -> float:
    """Get video duration using ffprobe."""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def generate_markdown_report(results: List[Dict[str, Any]], output_dir: Path):
    """Generate a comprehensive markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_path = output_dir / "insta360_synesthetic_report.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# 🌌 Insta360 Synesthetic Resonance Report\n\n")
        f.write(f"**Generated**: {timestamp}\n")
        f.write(f"**Total Videos Analyzed**: {len(results)}\n\n")
        
        f.write("---\n\n")
        
        for video_data in results:
            video_name = video_data['filename']
            f.write(f"## 🎬 {video_name}\n\n")
            f.write(f"- **Path**: `{video_data['path']}`\n")
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
    parser = argparse.ArgumentParser(description="Analyze local videos for Synesthetic Resonance.")
    parser.add_argument("--input", required=True, help="Input directory containing videos")
    parser.add_argument("--interval", type=int, default=60, help="Analysis interval in seconds")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of videos to process (0 = all)")
    
    args = parser.parse_args()
    
    input_dir = args.input
    interval = args.interval
    
    # Setup directories
    output_base = WORKSPACE_ROOT / "outputs" / "insta360_analysis"
    temp_frames_dir = output_base / "temp_frames"
    output_base.mkdir(parents=True, exist_ok=True)
    temp_frames_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Vision Cortex
    print("👁️ Initializing Vision Cortex...")
    cortex = VisionCortex()
    
    # Find videos
    print(f"🔍 Scanning {input_dir}...")
    videos = get_video_files(input_dir)
    print(f"Found {len(videos)} video files.")
    
    if args.limit > 0:
        videos = videos[:args.limit]
        print(f"Limiting to first {args.limit} videos.")
    
    results = []
    partial_json_path = output_base / "insta360_analysis_partial.json"
    
    # Load partial results if exist
    processed_filenames = set()
    if partial_json_path.exists():
        try:
            with open(partial_json_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
                processed_filenames = {r['filename'] for r in results}
            print(f"Loaded {len(results)} previously processed videos.")
        except Exception as e:
            print(f"Error loading partial results: {e}")
    
    for i, video_path in enumerate(videos):
        if video_path.name in processed_filenames:
            print(f"[{i+1}/{len(videos)}] Skipping {video_path.name} (Already Processed)")
            continue
            
        print(f"\n[{i+1}/{len(videos)}] Processing: {video_path.name}")
        
        duration = get_video_duration(video_path)
        if duration == 0:
            print("  ⚠️ Could not determine duration, skipping.")
            continue
            
        print(f"  Duration: {duration:.1f}s")
        
        video_result = {
            "filename": video_path.name,
            "path": str(video_path),
            "duration": duration,
            "frames": []
        }
        
        # Process frames
        current_time = 0.0
        # Always capture at least one frame (start)
        timestamps = []
        while current_time < duration:
            timestamps.append(current_time)
            current_time += interval
            
        for ts in timestamps:
            print(f"  - Analyzing frame at {ts}s...", end="", flush=True)
            
            frame_path = temp_frames_dir / f"frame_{i}_{int(ts)}.jpg"
            
            if extract_frame(video_path, frame_path, ts):
                # Analyze with Vision Cortex
                context = "The person filming this video is Binoche_Observer (The User). Observe the scene from their perspective."
                analysis = cortex.analyze_image(str(frame_path), context=context)
                
                video_result['frames'].append({
                    "timestamp": ts,
                    "analysis": analysis
                })
                
                # Cleanup frame
                try:
                    frame_path.unlink()
                except:
                    pass
                
                if analysis.get('status') == 'success':
                    print(" Done.")
                else:
                    print(f" Failed: {analysis.get('error', 'Unknown error')}")
                
                # Rate limit delay (10 RPM = 6s, using 10s to be safe)
                time.sleep(10)
            else:
                print(" Extraction Failed.")
                
        results.append(video_result)
        
        # Save partial results
        with open(partial_json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  Saved partial results to {partial_json_path.name}")
        
    # Generate Report
    generate_markdown_report(results, output_base)
    
    # Save raw JSON
    json_path = output_base / "insta360_analysis_raw.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Raw data saved: {json_path}")

if __name__ == "__main__":
    main()
