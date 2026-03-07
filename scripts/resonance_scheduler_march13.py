print("🐍 [DEBUG] Script loaded. Starting imports...")
import asyncio
import os
import sys
from pathlib import Path

# Add the scripts directory to path to import the scheduler
sys.path.append(str(Path("C:/workspace/agi/scripts")))
from youtube_bulk_scheduler import YoutubeBulkScheduler
print("🔮 [DEBUG] Imports complete.")

async def main():
    print("🎬 [DEBUG] Starting main function...")
    try:
        print("🔍 [DEBUG] Initializing YoutubeBulkScheduler...")
        scheduler = YoutubeBulkScheduler()
        print("✅ [DEBUG] Scheduler initialized.")
    except Exception as e:
        print(f"❌ [ERROR] Failed to init scheduler: {e}")
        return
    
    # Target date: March 13th
    # Today is March 7th. now < 6 PM.
    # day_offset 1 = March 7
    # day_offset 2 = March 8
    # day_offset 3 = March 9
    # day_offset 4 = March 10
    # day_offset 5 = March 11
    # day_offset 6 = March 12
    # day_offset 7 = March 13
    
    start_offset = 7
    
    # VIDEO_DIR is a constant in the module, let's get it
    import youtube_bulk_scheduler
    video_dir = youtube_bulk_scheduler.VIDEO_DIR
    
    all_videos = list(video_dir.glob("*.mp4"))
    uploaded_paths = [entry['original_path'] for entry in scheduler.history]
    available_videos = [v for v in all_videos if str(v) not in uploaded_paths]
    available_videos.sort()
    
    if not available_videos:
        print("✅ No new videos to schedule.")
        return

    print(f"📝 [TEMP SCHEDULER] Found {len(available_videos)} new videos.")
    
    day_offset = start_offset
    for i, video in enumerate(available_videos):
        publish_at = scheduler.get_next_publish_time(day_offset)
        title, _, _ = scheduler.generate_unique_metadata(video.name)
        print(f"🔍 [SCHEDULE PLAN] Will schedule: {title}")
        print(f"   📅 Date: {publish_at}")
        
        day_offset += 1
        if i >= 4: # Just print first 5 for confirmation in logs
            break
    
    print("\n🚀 Starting actual scheduling...")
    day_offset = start_offset
    for video in available_videos:
        publish_at = scheduler.get_next_publish_time(day_offset)
        success = await scheduler.schedule_video(video, publish_at, dry_run=False)
        if success:
            day_offset += 1
            await asyncio.sleep(2)
        else:
            print(f"⚠️ Stopped at {video.name} due to failure.")
            break

if __name__ == "__main__":
    asyncio.run(main())
