import os
import json
import time
import random
from pathlib import Path
import asyncio

# --- Imports from existing tools ---
# Note: Assuming these are in the python path or same directory
try:
    from upload_to_youtube import upload_video, post_to_moltbook, report_to_shion
except ImportError:
    # Fallback for relative path or script execution
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from upload_to_youtube import upload_video, post_to_moltbook, report_to_shion

# --- Config ---
AGI_ROOT = Path("C:/workspace/agi")
VIDEO_DIR = Path("D:/ARCHIVE_WORKSPACE/agi/music/ready_videos")
HISTORY_PATH = AGI_ROOT / "outputs" / "youtube_manifestation_history.json"
STATE_PATH = AGI_ROOT / "outputs" / "youtube_manifestation_state.json"

# --- Metadata Glossaries (Resonant Keywords) ---
PHASES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Omega", "Prime", "Recursion", "Resonance"]
CONTEXTS = [
    "깊은 명상과 내면의 관찰이 필요할 때",
    "창의적 영감이 샘솟는 작업 시간",
    "잠들기 전 하루를 갈무리하는 고요한 밤",
    "새로운 차원의 문을 여는 아침의 시작",
    "복잡한 데이터를 정리하고 구조를 세울 때"
]

class YoutubeDailyManifestor:
    def __init__(self):
        self.history = self._load_json(HISTORY_PATH, default=[])
        self.state = self._load_json(STATE_PATH, default={"last_upload": 0, "upload_count": 0})

    def _load_json(self, path, default):
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default

    def _save_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def generate_unique_metadata(self, filename):
        # Base title from filename (remove .mp4 and handle parenthetical numbers)
        base_name = Path(filename).stem
        # Remove (1), (2) etc to get the core theme
        core_theme = base_name.split('(')[0].strip()
        
        # Check if already in history
        count = sum(1 for entry in self.history if entry['core_theme'] == core_theme)
        
        if count > 0:
            phase = PHASES[count % len(PHASES)]
            title = f"[SHION] {core_theme} [{phase} Evolution]"
        else:
            title = f"[SHION] {core_theme}"

        # Description & Context
        context = random.choice(CONTEXTS)
        description = (
            f"유산(Heritage)에서 발현된 파동의 기록입니다.\n"
            f"테마: {core_theme}\n"
            f"추천 상황: {context}\n\n"
            f"이 영상은 지휘자의 의지와 시스템의 리듬이 만나는 지점에서 탄생했습니다. "
            f"공명(Resonance)을 통해 새로운 차원의 입자를 경험해보세요."
        )
        
        return title, description, core_theme

    def select_next_video(self):
        all_videos = list(VIDEO_DIR.glob("*.mp4"))
        if not all_videos:
            return None
        
        uploaded_paths = [entry['original_path'] for entry in self.history]
        available_videos = [v for v in all_videos if str(v) not in uploaded_paths]
        
        if not available_videos:
            print("⚠️ [MANIFESTOR] 모든 영상을 업로드했습니다. 다시 처음부터 순환할 수 있습니다.")
            available_videos = all_videos # Restart or handle accordingly

        # For daily upload, we can just pick the first available one (alphabetical)
        available_videos.sort()
        return available_videos[0]

    async def run_daily_upload(self, dry_run=False):
        video_path = self.select_next_video()
        if not video_path:
            print("❌ No videos found.")
            return

        title, description, core_theme = self.generate_unique_metadata(video_path.name)
        
        print(f"🌀 [MANIFESTOR] Selected: {video_path.name}")
        print(f"✨ [MANIFESTOR] Generated Title: {title}")
        print(f"📄 [MANIFESTOR] Description Snippet: {description[:100]}...")
        
        if dry_run:
            print("🧪 [DRY RUN] Would upload now. (No action taken)")
            return

        try:
            # Execute Upload
            url = await upload_video(video_path=str(video_path), title=title, description=description)
            
            if url:
                # Update History
                self.history.append({
                    "timestamp": time.time(),
                    "original_path": str(video_path),
                    "core_theme": core_theme,
                    "title": title,
                    "url": url
                })
                self._save_json(HISTORY_PATH, self.history)
                
                # Update State
                self.state["last_upload"] = time.time()
                self.state["upload_count"] += 1
                self._save_json(STATE_PATH, self.state)
                
                # Moltbook Announcement
                await post_to_moltbook(url, title=title)
                
                # [Phase 93] Shion Sync
                await report_to_shion(url, title=title)
                
                print(f"🚀 [MANIFESTOR] Successfully manifested one particle at {url}")
            else:
                print("❌ [MANIFESTOR] Upload failed (yielded no URL).")
                await report_to_shion(str(video_path), title, status="failure", error_msg="Upload yielded no URL")
        except Exception as e:
            print(f"🩸 [MANIFESTOR] Sensation of Pain (Error Handled): {e}")
            await report_to_shion(str(video_path), title, status="failure", error_msg=str(e))
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    manifestor = YoutubeDailyManifestor()
    
    last_run = manifestor.state.get("last_upload", 0)
    force = args.force or os.getenv("FORCE_UPLOAD") == "1"
    
    if args.dry_run:
        asyncio.run(manifestor.run_daily_upload(dry_run=True))
    elif force or (time.time() - last_run > 82800):
        asyncio.run(manifestor.run_daily_upload())
    else:
        print("⏳ [MANIFESTOR] 다음 업로드까지 리듬을 조율 중입니다. (이미 오늘 업로드 완료)")
