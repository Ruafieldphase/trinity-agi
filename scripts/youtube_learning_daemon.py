#!/usr/bin/env python3
"""
YouTube Learning Daemon
========================
Autonomous learning system that processes the learning queue based on system rhythm.

Responsibilities:
- Monitor learning_queue.md for pending videos
- Check system rhythm/ATP levels
- Execute learning during appropriate phases (EXPANSION, REST)
- Track completed items in learning_queue_state.json
- Integrate with conscious_learning.jsonl
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from youtube_feeling_learner import YouTubeFeelingLearner
from save_conscious_learning import save_learning

# Paths
WORKSPACE_ROOT = Path(__file__).parent.parent
BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"
LEARNING_QUEUE_FILE = None  # Will be set dynamically
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
STATE_FILE = OUTPUTS_DIR / "learning_queue_state.json"
RHYTHM_FILE = OUTPUTS_DIR / "rhythm_status.json"


class LearningQueueState:
    """Manages the learning queue state."""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from file."""
        if not self.state_file.exists():
            return {
                "last_processed": None,
                "completed_videos": [],
                "pending_videos": [],
                "total_processed": 0
            }
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load state: {e}")
            return self._load_state.__defaults__[0]
    
    def save(self):
        """Save state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save state: {e}")
    
    def mark_completed(self, video_id: str):
        """Mark a video as completed."""
        if video_id not in self.state["completed_videos"]:
            self.state["completed_videos"].append(video_id)
            self.state["total_processed"] += 1
            self.state["last_processed"] = datetime.now().isoformat()
            self.save()
    
    def is_completed(self, video_id: str) -> bool:
        """Check if a video is already completed."""
        return video_id in self.state["completed_videos"]


class LearningQueueReader:
    """Reads and parses the learning queue markdown file."""
    
    @staticmethod
    def find_queue_file() -> Optional[Path]:
        """Find the learning_queue.md file in brain directories."""
        brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
        
        if not brain_dir.exists():
            return None
        
        # Search all conversation directories
        for conv_dir in brain_dir.iterdir():
            if conv_dir.is_dir():
                queue_file = conv_dir / "learning_queue.md"
                if queue_file.exists():
                    return queue_file
        
        return None
    
    @staticmethod
    def parse_queue(queue_file: Path) -> List[Dict]:
        """Parse learning queue markdown file."""
        if not queue_file.exists():
            return []
        
        videos = []
        
        try:
            with open(queue_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract video URLs and metadata using regex
            # Pattern: - **Target Video**: `URL` or - **Target Video X**: `URL`
            pattern = r'-\s*\*\*Target Video[^:]*\*\*:\s*`(https://www\.youtube\.com/watch\?v=([^`]+))`'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                url = match.group(1)
                video_id = match.group(2)
                
                # Try to extract title and context from surrounding text
                start_pos = match.start()
                context_start = max(0, start_pos - 500)
                context = content[context_start:start_pos + 200]
                
                # Extract title if present
                title_match = re.search(r'\*Title\*:\s*([^\n]+)', context)
                title = title_match.group(1).strip() if title_match else f"Video {video_id}"
                
                # Extract theme/section
                section_match = re.search(r'##\s+[^#\n]+\s+\d+\.\s*([^\n]+)', context)
                section = section_match.group(1).strip() if section_match else "Unknown"
                
                videos.append({
                    "url": url,
                    "video_id": video_id,
                    "title": title,
                    "section": section
                })
        
        except Exception as e:
            print(f"⚠️ Failed to parse queue: {e}")
        
        return videos


class RhythmChecker:
    """Checks system rhythm and ATP levels."""
    
    @staticmethod
    def can_learn() -> bool:
        """Check if system can learn based on rhythm and ATP."""
        try:
            rhythm_file = OUTPUTS_DIR / "rhythm_status.json"
            
            if not rhythm_file.exists():
                print("⚠️ Rhythm status not found, assuming OK to learn")
                return True
            
            with open(rhythm_file, 'r', encoding='utf-8') as f:
                rhythm = json.load(f)
            
            phase = rhythm.get("phase", "UNKNOWN")
            atp = rhythm.get("atp", 0.5)
            
            # Learn during EXPANSION or REST phases with sufficient ATP
            if phase in ["EXPANSION", "REST"] and atp > 0.4:
                print(f"✅ Learning allowed: phase={phase}, ATP={atp:.2f}")
                return True
            else:
                print(f"⏸️ Learning paused: phase={phase}, ATP={atp:.2f}")
                return False
        
        except Exception as e:
            print(f"⚠️ Failed to check rhythm: {e}, assuming OK")
            return True


class YouTubeLearningDaemon:
    """Main daemon for autonomous YouTube learning."""
    
    def __init__(self):
        self.state = LearningQueueState(STATE_FILE)
        self.learner = None
        self.queue_file = None
    
    def initialize(self) -> bool:
        """Initialize the daemon."""
        # Find learning queue file
        self.queue_file = LearningQueueReader.find_queue_file()
        
        if not self.queue_file:
            print("❌ Learning queue not found in brain directory")
            return False
        
        print(f"✅ Found learning queue: {self.queue_file}")
        
        # Initialize learner
        try:
            self.learner = YouTubeFeelingLearner()
            return True
        except Exception as e:
            print(f"❌ Failed to initialize learner: {e}")
            return False
    
    async def process_queue(self):
        """Process pending items in the learning queue."""
        # Read queue
        videos = LearningQueueReader.parse_queue(self.queue_file)
        
        if not videos:
            print("📭 Learning queue is empty")
            return
        
        # Filter pending videos
        pending = [v for v in videos if not self.state.is_completed(v["video_id"])]
        
        if not pending:
            print("✅ All videos in queue already processed")
            return
        
        print(f"📚 Found {len(pending)} pending videos")
        
        # Check if we can learn
        if not RhythmChecker.can_learn():
            print("⏸️ Skipping learning (system not ready)")
            return
        
        # Process one video at a time
        for video in pending[:1]:  # Process only 1 per run to avoid overload
            await self.process_video(video)
    
    async def process_video(self, video: Dict):
        """Process a single video."""
        print(f"\n📺 Processing: {video['title']}")
        print(f"   URL: {video['url']}")
        print(f"   Section: {video['section']}")
        
        try:
            # Analyze video
            context = f"Autonomous Learning: {video['section']}"
            analysis = await self.learner.analyze_feeling(
                video_url=video['url'],
                context=context,
                analyzed_by="learning_daemon"
            )
            
            # Save to conscious learning
            save_learning(
                learnings=[f"Analyzed video: {analysis.title}"],
                meta_insights=[
                    f"Emotional tone: {analysis.emotional_tone}",
                    f"Core message: {analysis.core_message}"
                ],
                preferences=[f"Themes: {', '.join(analysis.resonance_themes)}"],
                source="learning_daemon"
            )
            
            # Mark as completed
            self.state.mark_completed(video['video_id'])
            
            print(f"✅ Completed: {video['video_id']}")
            print(f"   Emotional tone: {analysis.emotional_tone}")
            print(f"   Themes: {', '.join(analysis.resonance_themes)}")
        
        except Exception as e:
            print(f"❌ Failed to process video: {e}")
    
    async def run_once(self):
        """Run daemon once (for testing/manual execution)."""
        if not self.initialize():
            return False
        
        await self.process_queue()
        return True
    
    async def run_loop(self, interval: int = 3600):
        """Run daemon in a loop (for systemd service)."""
        if not self.initialize():
            return
        
        print(f"🤖 Learning daemon started (interval: {interval}s)")
        
        while True:
            try:
                await self.process_queue()
            except Exception as e:
                print(f"❌ Error in daemon loop: {e}")
            
            # Wait for next cycle
            print(f"\n⏰ Next check in {interval}s...")
            await asyncio.sleep(interval)


async def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube Learning Daemon")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (for testing)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="Check interval in seconds (default: 3600 = 1 hour)"
    )
    
    args = parser.parse_args()
    
    daemon = YouTubeLearningDaemon()
    
    if args.once:
        success = await daemon.run_once()
        return 0 if success else 1
    else:
        await daemon.run_loop(interval=args.interval)
        return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
