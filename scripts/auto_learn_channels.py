#!/usr/bin/env python3
"""
Automated YouTube Channel Learning Pipeline
============================================

Continuously learns from all educational channels evenly.

Features:
- Incremental learning (skips already learned videos)
- Multi-channel support with fair rotation
- Automatic RAG integration
- Background execution friendly
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

# Add workspace to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from fdo_agi_repo.rpa.youtube_learner import YouTubeLearner, YouTubeLearnerConfig

# Configuration
CHANNELS_FILE = WORKSPACE_ROOT / "scripts" / "youtube_channels.json"
LEARNED_INDEX = WORKSPACE_ROOT / "outputs" / "youtube_learner" / "learned_index.json"
YOUTUBE_LEDGER = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "youtube_knowledge.jsonl"

# Default channel list (Korean educational creators)
DEFAULT_CHANNELS = {
    "박문호의 자연과학 세상": "UCxqUWLQVUjamPGulNT6XSZA",
    "김영한의 도올TV": "UCOYrWHn3CRSLXzQxRLqJmKg",
    "안될과학 Unrealscience": "UCOxqgCwKY-VbLnv8Db7eEZQ",
    "김주환의 회복탄력성": "UCbOKdmB8YeWW0N6xwDGr4zg",
}

class ChannelLearningPipeline:
    """Automated channel learning pipeline"""
    
    def __init__(self, max_videos_per_run: int = 10):
        self.max_videos_per_run = max_videos_per_run
        self.learner = YouTubeLearner(YouTubeLearnerConfig(
            max_frames=3,  # Keep lightweight
            enable_ocr=False,
            frame_interval=30.0
        ))
        
        self.channels = self._load_channels()
        self.learned_videos = self._load_learned_index()
    
    def _load_channels(self) -> Dict[str, str]:
        """Load channel list from config file"""
        if CHANNELS_FILE.exists():
            with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default config
            CHANNELS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CHANNELS, f, indent=2, ensure_ascii=False)
            return DEFAULT_CHANNELS
    
    def _load_learned_index(self) -> Set[str]:
        """Load list of already learned video IDs"""
        if LEARNED_INDEX.exists():
            with open(LEARNED_INDEX, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('learned_videos', []))
        return set()
    
    def _save_learned_index(self):
        """Save updated learned index"""
        LEARNED_INDEX.parent.mkdir(parents=True, exist_ok=True)
        with open(LEARNED_INDEX, 'w', encoding='utf-8') as f:
            json.dump({
                'learned_videos': list(self.learned_videos),
                'last_updated': datetime.now().isoformat(),
                'total_count': len(self.learned_videos)
            }, f, indent=2)
    
    async def get_channel_videos(self, channel_id: str) -> List[str]:
        """Get all video URLs from a channel"""
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # Only get video list, don't download
                'playlistend': 50,  # Limit to 50 most recent per channel per run
            }
            
            channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                
                if 'entries' in info:
                    return [
                        f"https://youtube.com/watch?v={entry['id']}"
                        for entry in info['entries']
                        if entry and 'id' in entry
                    ]
        except Exception as e:
            print(f"⚠️ Failed to fetch videos from {channel_id}: {e}")
        
        return []
    
    async def learn_new_videos(self, channel_name: str, channel_id: str) -> int:
        """Learn new videos from a channel"""
        print(f"\n📺 Channel: {channel_name}")
        
        # Get video list
        print(f"   Fetching video list...")
        video_urls = await self.get_channel_videos(channel_id)
        
        if not video_urls:
            print(f"   ❌ No videos found")
            return 0
        
        # Filter out already learned
        new_videos = [
            url for url in video_urls
            if self.learner._extract_video_id(url) not in self.learned_videos
        ]
        
        print(f"   Found {len(video_urls)} videos, {len(new_videos)} are new")
        
        if not new_videos:
            return 0
        
        # Learn videos (limited per run)
        learned_count = 0
        for i, video_url in enumerate(new_videos[:self.max_videos_per_run]):
            try:
                print(f"   [{i+1}/{min(len(new_videos), self.max_videos_per_run)}] Learning...")
                
                # Analyze video
                analysis = await self.learner.analyze_video(video_url)
                
                # Convert to RAG memory
                await self._add_to_rag(analysis, channel_name)
                
                # Mark as learned
                self.learned_videos.add(analysis.video_id)
                learned_count += 1
                
                print(f"       ✅ {analysis.title[:50]}...")
                
            except Exception as e:
                print(f"       ❌ Failed: {e}")
                continue
        
        return learned_count
    
    async def _add_to_rag(self, analysis, channel_name: str):
        """Add video analysis to RAG memory"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Load model
            model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
            
            # Create content
            transcript = " ".join([sub.text for sub in analysis.subtitles[:100]])
            content = f"{analysis.title}. {transcript}"
            
            # Generate vector
            vector = model.encode(content, convert_to_numpy=True).tolist()
            
            # Create entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "youtube_memory",
                "summary": f"[YouTube] {analysis.title}",
                "narrative": transcript[:2000],
                "vector": vector,
                "metadata": {
                    "video_id": analysis.video_id,
                    "duration_minutes": round(analysis.duration / 60, 1),
                    "url": f"https://youtube.com/watch?v={analysis.video_id}",
                    "channel": channel_name,
                    "keywords": analysis.keywords
                }
            }
            
            # Append to ledger
            with open(YOUTUBE_LEDGER, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"       ⚠️ RAG integration failed: {e}")
    
    async def run(self):
        """Run learning pipeline"""
        print("=" * 60)
        print("🎓 Automated YouTube Channel Learning Pipeline")
        print("=" * 60)
        print(f"\n📊 Channels: {len(self.channels)}")
        print(f"📚 Already learned: {len(self.learned_videos)} videos")
        print(f"🎯 Max per channel this run: {self.max_videos_per_run}")
        
        total_learned = 0
        
        # Process channels evenly (round-robin)
        for channel_name, channel_id in self.channels.items():
            try:
                count = await self.learn_new_videos(channel_name, channel_id)
                total_learned += count
            except Exception as e:
                print(f"   ❌ Channel error: {e}")
                continue
        
        # Save progress
        self._save_learned_index()
        
        print(f"\n✨ Session complete!")
        print(f"   New videos learned: {total_learned}")
        print(f"   Total learned: {len(self.learned_videos)}")
        print(f"\n💡 Run again to continue learning more videos!")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated YouTube Channel Learning")
    parser.add_argument('--max-per-channel', type=int, default=10,
                       help='Max videos to learn per channel per run')
    args = parser.parse_args()
    
    pipeline = ChannelLearningPipeline(max_videos_per_run=args.max_per_channel)
    await pipeline.run()

if __name__ == "__main__":
    asyncio.run(main())
