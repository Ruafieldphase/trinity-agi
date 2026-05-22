import os
import subprocess
from pathlib import Path

VIDEO_DIR = Path("C:/workspace/agi/music/ready_videos")
SHORTS_DIR = Path("C:/workspace/agi/music/ready_shorts")

def generate_shorts():
    if not VIDEO_DIR.exists():
        print(f"❌ Video directory not found: {VIDEO_DIR}")
        return

    SHORTS_DIR.mkdir(parents=True, exist_ok=True)
    all_videos = list(VIDEO_DIR.glob("*.mp4"))

    if not all_videos:
        print("❌ No videos found to convert.")
        return

    print(f"🎬 Found {len(all_videos)} videos. Generating Shorts...")

    for video_path in all_videos:
        short_filename = f"{video_path.stem}_short.mp4"
        short_path = SHORTS_DIR / short_filename

        if short_path.exists():
            print(f"⏭️ Skipping {short_filename}, already exists.")
            continue

        print(f"✂️ Processing: {video_path.name} -> {short_filename}")

        # ffmpeg command:
        # -ss 00:01:00 : start at 1 minute mark to skip intros
        # -t 59 : 59 seconds duration
        # -vf "crop=ih*9/16:ih" : crop center to 9:16 vertical ratio
        command = [
            "ffmpeg",
            "-y", # Overwrite if exists
            "-ss", "00:01:00",
            "-i", str(video_path),
            "-t", "59",
            "-vf", "crop=ih*9/16:ih",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            str(short_path)
        ]

        try:
            # We run without capturing output to let it print to console, or we capture to hide clutter
            result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode == 0:
                print(f"   ✅ Success: {short_filename}")
            else:
                print(f"   ❌ Failed to convert {video_path.name}")
        except Exception as e:
            print(f"   ❌ Error processing {video_path.name}: {e}")

if __name__ == "__main__":
    generate_shorts()
