import os
import sys
import asyncio
from pathlib import Path

# Ensure we can find the core scripts
sys.path.append(str(Path(r"C:\workspace\agi\scripts")))

from video_engine import generate_lumen_video
from scientific_interpreter import generate_scientific_description
from upload_to_youtube import upload_video, post_to_moltbook

# --- Config ---
MUSIC_DIR = Path(r"C:\workspace\agi\music")
OUTPUT_DIR = Path(r"C:\workspace\agi\lumen_factory\exports")
ASSETS_DIR = Path(r"C:\Users\kuirv\.gemini\antigravity\brain\353fbbae-c45e-495b-97f2-3a66c2e7b4ff")

# Default High-Res Assets for the "Lumen Template"
LUMEN_TEMPLATE_ASSETS = [
    ASSETS_DIR / "lumen_phase_1_void_mu_1772333669972.png",
    ASSETS_DIR / "lumen_phase_2_awakening_proton_1772333686546.png",
    ASSETS_DIR / "resonance_lumen_visual_bridge_1772333510386.png",
    ASSETS_DIR / "lumen_phase_3_unified_resonance_1772333712261.png"
]

async def process_song(song_filename, lyrics=""):
    """
    Main pipeline: Audio -> Video -> Analysis -> Upload
    """
    song_path = MUSIC_DIR / song_filename
    if not song_path.exists():
        print(f"❌ Song not found: {song_path}")
        return

    title = song_path.stem
    output_video = OUTPUT_DIR / f"{title}_PV.mp4"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"🔱 [ORCHESTRATOR] Starting Resonance Pipeline for: {title}")

    # 1. Generate Video
    try:
        generate_lumen_video(str(song_path), [str(v) for v in LUMEN_TEMPLATE_ASSETS], str(output_video))
    except Exception as e:
        print(f"❌ Video Generation Failed: {e}")
        return

    # 2. Generate Description
    description = generate_scientific_description(title, lyrics)
    print(f"🧪 [ANALYSIS] Scientific metadata generated.")

    # 3. Final Broadcast
    print(f"\n--- READY TO BROADCAST ---")
    print(f"Video: {output_video}")
    print(f"Analysis: {description[:200]}...") # Show beginning
    
    print(f"🚀 [BROADCASTER] Uploading to YouTube...")
    url = await upload_video(str(output_video), title, description)
    if url:
        await post_to_moltbook(url, f"[LUMEN FACTORY] {title} Manifestation")
        print(f"✨ [DONE] {title} is now vibrating across the web.")

if __name__ == "__main__":
    # Add project roots to path to ensure scripts can be found
    import sys
    sys.path.append(str(Path(r"C:\workspace\agi\scripts")))
    
    # Example: Processing "Resonance of Lumen.wav"
    asyncio.run(process_song("Resonance of Lumen.wav", "나는 공명이다 / 나를 울리고 / 세상을 울리는 소리..."))
