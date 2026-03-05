import os
import json
import time
import datetime
import pytz
import random
from pathlib import Path
import asyncio
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# --- Imports from existing tools ---
try:
    from upload_to_youtube import post_to_moltbook, report_to_shion
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from upload_to_youtube import post_to_moltbook, report_to_shion

# --- Config ---
AGI_ROOT = Path("C:/workspace/agi")
CRED_DIR = AGI_ROOT / "credentials"
YT_TOKEN = CRED_DIR / "youtube_token.json"
VIDEO_DIR = Path("D:/ARCHIVE_WORKSPACE/agi/music/ready_videos")
HISTORY_PATH = AGI_ROOT / "outputs" / "youtube_manifestation_history.json"
STATE_PATH = AGI_ROOT / "outputs" / "youtube_manifestation_state.json"

# --- Constants ---
TIMEZONE = pytz.timezone('Asia/Seoul')
PUBLISH_HOUR = 18 # 6 PM

PHASES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Omega", "Prime", "Recursion", "Resonance"]
CONTEXTS = [
    "깊은 명상과 내면의 관찰이 필요할 때",
    "창의적 영감이 샘솟는 작업 시간",
    "잠들기 전 하루를 갈무리하는 고요한 밤",
    "새로운 차원의 문을 여는 아침의 시작",
    "복잡한 데이터를 정리하고 구조를 세울 때"
]

class YoutubeBulkScheduler:
    def __init__(self):
        self.history = self._load_json(HISTORY_PATH, default=[])
        self.state = self._load_json(STATE_PATH, default={"last_upload": 0, "upload_count": 0})
        self.creds = Credentials.from_authorized_user_file(str(YT_TOKEN))
        self.youtube = build("youtube", "v3", credentials=self.creds)

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

    def get_next_publish_time(self, day_offset=1):
        """Calculate the ISO 8601 string for 6 PM KST, offset by days."""
        now = datetime.datetime.now(TIMEZONE)
        publish_time = now.replace(hour=PUBLISH_HOUR, minute=0, second=0, microsecond=0)
        
        # If it's already past 6 PM today, or we want a later day
        if now >= publish_time:
            publish_time += datetime.timedelta(days=day_offset)
        else:
            # If we want the *next* available slots starting tomorrow
            if day_offset > 0:
                publish_time += datetime.timedelta(days=day_offset - 1)
        
        return publish_time.isoformat()

    def generate_unique_metadata(self, filename):
        base_name = Path(filename).stem
        core_theme = base_name.split('(')[0].strip()
        count = sum(1 for entry in self.history if entry.get('core_theme') == core_theme)
        
        # --- Vibe Classification Logic ---
        vibe_map = {
            "Meditation": ["0.4 Seconds", "Silence", "Hollow", "Quiet", "Still", "고요한", "여백"],
            "Flow": ["Fractal", "Recursion", "Cycle", "Phase", "Continuum", "순환", "환류"],
            "Inspiration": ["Lumen", "Bloom", "Declaration", "Awakening", "Light", "빛", "시선"],
            "Comfort": ["Comfort", "Soft", "Silk", "Memory of Water", "Midnight", "편안", "위로", "새벽빛"],
            "Synchrony": ["Comet", "Lua", "Trinity", "Pulse", "Agent", "합일", "연결", "귀환"]
        }
        
        selected_vibe = "General Resonance"
        for vibe, keywords in vibe_map.items():
            if any(k.lower() in core_theme.lower() for k in keywords):
                selected_vibe = vibe
                break
        
        vibe_contexts = {
            "Meditation": "새벽 명상, 자기 전, 혹은 극도의 집중이 필요한 설계 시간",
            "Flow": "아이디어 기획과 데이터 정리, 끊김 없는 몰입이 필요한 순간",
            "Inspiration": "아침의 시작과 새로운 창작 프로젝트에 착수할 때",
            "Comfort": "휴식과 위로가 필요한 시간, 따뜻한 차 한 잔과 함께",
            "Synchrony": "시스템과의 합일(Unity)을 느끼고 싶은 특별한 순간",
            "General Resonance": "보편적인 공명과 일상의 리듬이 필요한 모든 순간"
        }
        
        context = vibe_contexts[selected_vibe]
        
        if count > 0:
            phase = PHASES[count % len(PHASES)]
            title = f"[SHION] {core_theme} [{phase} Evolution]"
        else:
            title = f"[SHION] {core_theme}"

        description = (
            f"유산(Heritage)에서 발현된 파동의 기록입니다.\n"
            f"테마: {core_theme}\n"
            f"공명 대역: {selected_vibe}\n"
            f"추천 상황: {context}\n\n"
            f"이 영상은 지휘자의 의지와 시스템의 리듬이 만나는 지점에서 탄생했습니다. "
            f"공명(Resonance)을 통해 새로운 차원의 입자를 경험해보세요.\n\n"
            f"#Shion #AI #Resonance #UnifiedField #{selected_vibe}"
        )
        return title, description, core_theme

    async def schedule_video(self, video_path, publish_at, dry_run=False):
        title, description, core_theme = self.generate_unique_metadata(video_path.name)
        print(f"📦 [SCHEDULER] Preparing: {video_path.name}")
        print(f"   📅 Target: {publish_at} (KST)")
        print(f"   ✨ Title: {title}")

        if dry_run:
            print("   🧪 [DRY RUN] No upload performed.")
            return True

        try:
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["AI", "Resonance", "Music", "Shion"],
                    "categoryId": "28"
                },
                "status": {
                    "privacyStatus": "private",
                    "publishAt": publish_at,
                    "selfDeclaredMadeForKids": False
                }
            }

            media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
            request = self.youtube.videos().insert(part="snippet,status", body=body, media_body=media)

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"   📡 Uploading... {int(status.progress() * 100)}%")

            video_id = response["id"]
            video_url = f"https://youtu.be/{video_id}"
            print(f"   ✅ SUCCESS: Scheduled at {video_url}")

            # Update History
            self.history.append({
                "timestamp": time.time(),
                "original_path": str(video_path),
                "core_theme": core_theme,
                "title": title,
                "url": video_url,
                "scheduled_at": publish_at
            })
            self._save_json(HISTORY_PATH, self.history)
            
            # Sync to Shion
            await report_to_shion(video_url, title=title)
            return True

        except Exception as e:
            print(f"   ❌ FAILED for {video_path.name}: {e}")
            return False

    async def run_bulk_scheduling(self, dry_run=False):
        all_videos = list(VIDEO_DIR.glob("*.mp4"))
        if not all_videos:
            print("❌ No videos found in ready_videos.")
            return

        uploaded_paths = [entry['original_path'] for entry in self.history]
        available_videos = [v for v in all_videos if str(v) not in uploaded_paths]
        available_videos.sort() # Temporal consistency

        if not available_videos:
            print("✅ All videos have already been scheduled.")
            return

        print(f"📝 [SCHEDULER] {len(available_videos)} new videos to schedule.")
        
        # We start scheduling from 1 day offset (tomorrow) unless specified otherwise
        day_offset = 1 
        for video in available_videos:
            publish_at = self.get_next_publish_time(day_offset)
            success = await self.schedule_video(video, publish_at, dry_run=dry_run)
            if success:
                day_offset += 1
                # Small cool-down between API calls
                await asyncio.sleep(2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    scheduler = YoutubeBulkScheduler()
    asyncio.run(scheduler.run_bulk_scheduling(dry_run=args.dry_run))
