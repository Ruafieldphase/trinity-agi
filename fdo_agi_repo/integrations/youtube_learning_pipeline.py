#!/usr/bin/env python3
"""
YouTube Learning Pipeline - Simplified Entry Point

간소화된 YouTube 학습 파이프라인:
1. YouTube URL 입력
2. 비디오 분석 (기존 youtube_learner.py 사용)
3. JSON + Markdown 리포트 생성
4. (선택) Comet 통합 준비

Phase 2.5 Day 1-2 Milestone:
- Comet 없이도 작동하는 기본 파이프라인 완성
- 나중에 Comet 검색 기능 추가 가능
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.youtube_handler import YouTubeHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class YouTubeLearningPipeline:
    """
    간소화된 YouTube 학습 파이프라인
    
    Usage:
        pipeline = YouTubeLearningPipeline()
        pipeline.learn_from_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    """
    
    def __init__(
        self,
        output_dir: Optional[Path] = None,
        max_frames: int = 5,
        frame_interval: int = 30
    ):
        """
        Initialize pipeline
        
        Args:
            output_dir: Directory for outputs (default: fdo_agi_repo/outputs/youtube)
            max_frames: Maximum frames to capture
            frame_interval: Seconds between frames
        """
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "outputs" / "youtube"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_frames = max_frames
        self.frame_interval = frame_interval
        
        logger.info(f"Pipeline initialized. Output: {self.output_dir}")
    
    def learn_from_url(
        self,
        url: str,
        clip_seconds: int = 30,
        enable_ocr: bool = False
    ) -> Optional[Path]:
        """
        YouTube URL에서 학습
        
        Args:
            url: YouTube video URL
            clip_seconds: How many seconds to analyze
            enable_ocr: Enable OCR on frames
            
        Returns:
            Path to generated report (JSON)
        """
        logger.info(f"🎬 Learning from: {url}")
        logger.info(f"   Clip: {clip_seconds}s, Max Frames: {self.max_frames}")
        
        # Use Task Queue + RPA Worker (existing system)
        try:
            # Enqueue task via existing script
            script_path = Path(__file__).parent.parent.parent / "scripts" / "enqueue_youtube_learn.ps1"
            
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", str(script_path),
                "-Url", url,
                "-ClipSeconds", str(clip_seconds),
                "-MaxFrames", str(self.max_frames),
                "-FrameInterval", str(self.frame_interval)
            ]
            
            if enable_ocr:
                cmd.append("-EnableOcr")
            
            logger.info(f"📤 Enqueueing task via: {script_path.name}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode != 0:
                logger.error(f"❌ Enqueue failed: {result.stderr}")
                return None
            
            logger.info("✅ Task enqueued successfully")
            logger.info("⏳ Waiting for RPA Worker to process...")
            
            # Wait and check results
            import time
            time.sleep(5)
            
            # Get results from Task Queue Server
            import requests
            try:
                response = requests.get(
                    "http://localhost:8091/api/results",
                    timeout=5
                )
                
                if response.status_code != 200:
                    logger.warning("Could not fetch results from server")
                    return None
                
                results = response.json().get("results", [])
                if not results:
                    logger.warning("No results yet. Check later.")
                    return None
                
                # Find latest result
                latest = results[0]  # Assuming most recent first
                result = latest
                
            except Exception as e:
                logger.warning(f"Could not fetch results: {e}")
                return None
            
            if not result or not result.get("success"):
                error = result.get("error") if result else "Unknown error"
                logger.error(f"❌ Analysis failed: {error}")
                return None
            
            # Extract video ID for filename
            video_id = self._extract_video_id(url)
            
            # Save JSON report
            json_path = self.output_dir / f"{video_id}_analysis.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ JSON report saved: {json_path}")
            
            # Generate Markdown report
            md_path = self._generate_markdown_report(result, video_id)
            logger.info(f"✅ Markdown report saved: {md_path}")
            
            return json_path
            
        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def learn_from_search(
        self,
        query: str,
        max_videos: int = 3
    ) -> List[Path]:
        """
        검색어로 YouTube 비디오 찾아서 학습 (Comet 필요)
        
        Args:
            query: Search query
            max_videos: Maximum videos to analyze
            
        Returns:
            List of report paths
        """
        logger.warning("⚠️ Search feature requires Comet Browser Worker")
        logger.warning("   For now, please provide YouTube URLs directly")
        return []
    
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from URL"""
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        else:
            return "unknown"
    
    def _generate_markdown_report(
        self,
        result: dict,
        video_id: str
    ) -> Path:
        """Generate Markdown report from JSON result"""
        md_path = self.output_dir / f"{video_id}_report.md"
        
        title = result.get("metadata", {}).get("title", "Unknown Video")
        url = result.get("metadata", {}).get("url", "")
        duration = result.get("metadata", {}).get("duration", "Unknown")
        transcript = result.get("transcript", {}).get("text", "No transcript available")
        
        frames_info = result.get("frames", {})
        frame_count = len(frames_info.get("paths", []))
        
        md_content = f"""# YouTube Learning Report

## Video Info
- **Title**: {title}
- **URL**: {url}
- **Duration**: {duration}
- **Analyzed**: {frame_count} frames

## Transcript
```
{transcript[:500]}...
```

## Frames Captured
- Total: {frame_count}
- Interval: {self.frame_interval}s
- Paths: {json.dumps(frames_info.get("paths", []), indent=2)}

## Analysis Summary
- Success: {result.get("success")}
- Timestamp: {result.get("timestamp")}

---
*Generated by YouTube Learning Pipeline*
"""
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return md_path


def main():
    """CLI Interface"""
    parser = argparse.ArgumentParser(
        description="YouTube Learning Pipeline - Learn from YouTube videos"
    )
    
    parser.add_argument(
        "--url",
        required=True,
        help="YouTube video URL"
    )
    parser.add_argument(
        "--clip-seconds",
        type=int,
        default=30,
        help="Seconds of video to analyze (default: 30)"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=5,
        help="Maximum frames to capture (default: 5)"
    )
    parser.add_argument(
        "--frame-interval",
        type=int,
        default=30,
        help="Seconds between frames (default: 30)"
    )
    parser.add_argument(
        "--enable-ocr",
        action="store_true",
        help="Enable OCR on frames (slower)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: fdo_agi_repo/outputs/youtube)"
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = YouTubeLearningPipeline(
        output_dir=args.output_dir,
        max_frames=args.max_frames,
        frame_interval=args.frame_interval
    )
    
    # Learn from URL
    print(f"\n🚀 YouTube Learning Pipeline")
    print("━" * 70)
    print(f"URL: {args.url}")
    print(f"Clip: {args.clip_seconds}s")
    print(f"Frames: {args.max_frames} (every {args.frame_interval}s)")
    print(f"OCR: {'Enabled' if args.enable_ocr else 'Disabled'}")
    print("━" * 70)
    print()
    
    result_path = pipeline.learn_from_url(
        url=args.url,
        clip_seconds=args.clip_seconds,
        enable_ocr=args.enable_ocr
    )
    
    if result_path:
        print(f"\n✅ Success! Report: {result_path}")
        print(f"📊 View with: code {result_path}")
        return 0
    else:
        print(f"\n❌ Failed to analyze video")
        return 1


if __name__ == "__main__":
    exit(main())
