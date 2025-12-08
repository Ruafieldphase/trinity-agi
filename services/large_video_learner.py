
"""
Large OBS Video Processor (ARI Interface)
=========================================
Handles large video files (>1GB) by extracting keyframes and creating a visual summary
for the Multi-modal LLM, bypassing file size limits and bandwidth constraints.
"""
import os
import cv2  # OpenCV for frame extraction
import time
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from PIL import Image

import sys

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Integration with ARI
from services.ari_engine import get_ari_engine

# Configuration
INPUT_DIR = Path("C:/workspace/agi/input/obs_recode")
PROCESSED_LOG = INPUT_DIR / "processed_large_videos.json"
FRAME_INTERVAL_SEC = 30  # Extract 1 frame every 30 seconds
MAX_FRAMES = 100         # Cap at 100 frames to fit in context efficiently

logger = logging.getLogger("LargeVideoProcessor")
logging.basicConfig(level=logging.INFO)

class LargeVideoLearner:
    def __init__(self):
        self.ari_engine = get_ari_engine()
        self.processed_files = self._load_log()
        
    def _load_log(self):
        if PROCESSED_LOG.exists():
            try:
                with open(PROCESSED_LOG, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: 
                return []
        return []

    def _save_log(self):
        with open(PROCESSED_LOG, 'w', encoding='utf-8') as f:
            json.dump(self.processed_files, f)

    def extract_frames(self, video_path):
        """Extracts frames from the video at regular intervals."""
        logger.info(f"Extracting frames from {video_path.name}...")
        cam = cv2.VideoCapture(str(video_path))
        fps = cam.get(cv2.CAP_PROP_FPS)
        total_frames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        frames = []
        current_time = 0
        
        while current_time < duration:
            cam.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
            ret, frame = cam.read()
            if ret:
                # Convert BGR to RGB (PIL compatible)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                
                # Resize for efficiency (e.g., 640px width)
                pil_img.thumbnail((640, 640))
                frames.append(pil_img)
            
            current_time += FRAME_INTERVAL_SEC
            if len(frames) >= MAX_FRAMES:
                break
                
        cam.release()
        logger.info(f"Extracted {len(frames)} frames.")
        return frames

    async def analyze_frames(self, frames, original_filename):
        """Sends frames to Gemini for analysis."""
        logger.info("Sending frames to Gemini for analysis...")
        
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        prompt = [
            "Analyze this sequence of screenshots from a user's computer session.",
            "This is a large video summarized into keyframes.",
            "Identify the main user workflow, specific tools used, and the overall goal.",
            "Output JSON:",
            "{ 'goal': '...', 'steps': [ ... ], 'success': true }"
        ]
        
        # Interleave prompt and images
        content = prompt + frames
        
        try:
            response = model.generate_content(content)
            json_str = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return None

    def inject_to_ari(self, analysis, filename):
        """Injects the learned pattern into ARI."""
        if not analysis: return
        
        experience = {
            "goal": analysis.get("goal", "Large Video Analysis"),
            "source_file": filename,
            "type": "large_video_summary",
            "steps": analysis.get("steps", []),
            "timestamp": datetime.now().isoformat()
        }
        
        # Inject into ARI Engine
        self.ari_engine.learning.experiences.append(experience)
        self.ari_engine.learning._save_buffer()
        logger.info(f"✅ ARI Learned from Large Video: {filename}")

    async def process_all(self):
        videos = list(INPUT_DIR.glob("*.mp4"))
        sorted_videos = sorted(videos, key=lambda x: x.stat().st_size) # Smallest of the large ones first
        
        for video in sorted_videos:
            if video.name in self.processed_files:
                continue
            
            # Simple check: Only process files > 1GB
            if video.stat().st_size < (1024 * 1024 * 1024):
                continue
                
            logger.info(f"Processing Large Video: {video.name}")
            frames = self.extract_frames(video)
            if frames:
                analysis = await self.analyze_frames(frames, video.name)
                self.inject_to_ari(analysis, video.name)
                self.processed_files.append(video.name)
                self._save_log()
                
            await asyncio.sleep(5)

if __name__ == "__main__":
    # Ensure logs directory exists
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        filename=log_dir / "large_video_learner.log",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    learner = LargeVideoLearner()
    try:
        logging.info("Starting Large Video Learner Loop...")
        asyncio.run(learner.process_all())
    except Exception as e:
        logging.error(f"Fatal error: {e}")
