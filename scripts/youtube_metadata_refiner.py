import os
import json
import time
from pathlib import Path
import asyncio
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# --- Config ---
AGI_ROOT = Path("C:/workspace/agi")
CRED_DIR = AGI_ROOT / "credentials"
YT_TOKEN = CRED_DIR / "youtube_token.json"
HISTORY_PATH = AGI_ROOT / "outputs" / "youtube_manifestation_history.json"

PHASES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Omega", "Prime", "Recursion", "Resonance"]

class YoutubeMetadataRefiner:
    def __init__(self):
        self.history = self._load_json(HISTORY_PATH, default=[])
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

    def generate_vibe_metadata(self, core_theme, count=0):
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
        return title, description

    async def refine_existing_videos(self, dry_run=False):
        if not self.history:
            print("❌ No history found.")
            return

        print(f"🔍 [REFINER] Found {len(self.history)} videos in history.")
        
        # Deduplicate themes for Evolution phase calculation if needed, 
        # but here we can just process each entry
        
        for entry in self.history:
            video_url = entry.get('url')
            if not video_url: continue
            
            video_id = video_url.split('/')[-1]
            core_theme = entry.get('core_theme')
            
            # Simple count calculation based on current history index for phase
            # (Though history might already have 'title', we regenerate for consistency)
            # Find how many times this theme appeared *before* this entry
            idx = self.history.index(entry)
            prior_count = sum(1 for e in self.history[:idx] if e.get('core_theme') == core_theme)
            
            new_title, new_description = self.generate_vibe_metadata(core_theme, count=prior_count)
            
            print(f"🎬 [REFINER] Processing: {video_id} ({core_theme})")
            print(f"   ✨ New Title: {new_title}")
            
            if dry_run:
                print("   🧪 [DRY RUN] Would update now.")
                continue

            try:
                # Update YouTube Metadata
                # Note: We must first get current status to preserve categories/tags if possible, 
                # but simplest update is re-sending snippet.
                request = self.youtube.videos().update(
                    part="snippet",
                    body={
                        "id": video_id,
                        "snippet": {
                            "title": new_title,
                            "description": new_description,
                            "categoryId": "28" # Science & Tech
                        }
                    }
                )
                request.execute()
                print(f"   ✅ SUCCESS: Updated {video_id}")
                await asyncio.sleep(1) # Rate limit safety
                
            except Exception as e:
                print(f"   ❌ FAILED to update {video_id}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    refiner = YoutubeMetadataRefiner()
    asyncio.run(refiner.refine_existing_videos(dry_run=args.dry_run))
