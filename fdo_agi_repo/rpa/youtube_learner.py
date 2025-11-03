"""
YouTube Learner Module
Phase 2.5 Day 3-4: YouTube 영상 분석 및 학습

Features:
1. 자막 추출 (PyTube + youtube-transcript-api)
2. 프레임 추출 및 분석 (OpenCV)
3. OCR 기반 화면 텍스트 인식 (EasyOCR)
4. 키워드 추출 및 콘텐츠 요약
5. 실행 절차 JSON 생성

Design:
- Async/Await 기반 비동기 처리
- Retry 메커니즘 (네트워크 오류 대응)
- Resonance Ledger 통합 (학습 기록)
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Lumen Gateway 클라이언트 임포트
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (LLM_Unified가 있는 곳)
# 이 파일의 위치: fdo_agi_repo/rpa/youtube_learner.py
# 프로젝트 루트: fdo_agi_repo/../
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Optional Lumen client import (path contains hyphen; use dynamic import)
get_lumen_client = None  # type: ignore
lumen_client_available = False
try:
    import importlib
    # Attempt import via safe path; repository may use hyphenated folder names
    # which are not valid Python packages. We handle failure gracefully.
    mod = importlib.import_module(
        "LLM_Unified.ion_mentoring.app.integrations.lumen_client"
    )
    get_lumen_client = getattr(mod, "get_lumen_client", None)
    lumen_client_available = get_lumen_client is not None
except Exception as e:
    # Keep optional dependency disabled; unit tests that don't need it can proceed
    lumen_client_available = False
    print(f"[Warning] Lumen Client not available: {e}")


from typing import TYPE_CHECKING

# 지연 임포트 전략: 무거운/선택적 의존성은 런타임에 필요할 때만 임포트합니다.
if TYPE_CHECKING:
    import numpy as np  # type: ignore
else:
    np = None  # type: ignore

# Ensure UTF-8 friendliness inside Python process (defensive)
try:
    from rpa.utf8_utils import force_utf8  # type: ignore
    force_utf8()
except Exception:
    pass


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class YouTubeLearnerConfig:
    """YouTube Learner 설정"""
    output_dir: Path = Path("outputs/youtube_learner")
    subtitle_format: str = "srt"  # srt, vtt, json
    frame_interval: float = 5.0  # 프레임 추출 간격 (초)
    max_frames: int = 50  # 최대 추출 프레임 수
    enable_ocr: bool = False  # OCR 활성화 (EasyOCR 필요)
    max_ocr_frames: int = 3  # OCR 수행 프레임 상한 (성능 보호)
    sample_clip_seconds: int = 0  # yt-dlp 앞부분만 다운로드(초). 0이면 전체
    retry_attempts: int = 3
    retry_delay: float = 2.0
    log_level: str = "INFO"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Subtitle:
    """자막 데이터"""
    text: str
    start: float  # 시작 시간 (초)
    duration: float  # 지속 시간 (초)
    language: str = "en"


@dataclass
class VideoFrame:
    """비디오 프레임"""
    timestamp: float  # 타임스탬프 (초)
    frame: Any  # OpenCV 이미지 (런타임 의존성 회피를 위해 Any)
    description: Optional[str] = None  # 프레임 설명


@dataclass
class VideoAnalysis:
    """영상 분석 결과"""
    video_id: str
    title: str
    duration: float  # 전체 길이 (초)
    subtitles: List[Subtitle]
    frames: List[VideoFrame]
    keywords: List[str]
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# YouTube Learner
# ============================================================================

class YouTubeLearner:
    """YouTube 영상 분석 및 학습"""
    
    def __init__(self, config: Optional[YouTubeLearnerConfig] = None):
        self.config = config or YouTubeLearnerConfig()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.config.log_level)
        
        # Output 디렉토리 생성
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def analyze_video(self, video_url: str) -> VideoAnalysis:
        """YouTube 영상 분석 (전체 파이프라인)"""
        self.logger.info(f"Analyzing video: {video_url}")
        
        # 1. 비디오 메타데이터 추출
        video = await self._fetch_video_metadata(video_url)
        video_id = self._extract_video_id(video_url)
        
        # 2. 자막 추출
        subtitles = await self._extract_subtitles(video_id)
        
        # 3. 프레임 추출
        frames = await self._extract_frames(video)
        
        # 4. 키워드 추출 (자막 기반)
        keywords = self._extract_keywords(subtitles)
        
        # 4-1. 선택: OCR 키워드 보강
        if self.config.enable_ocr and frames:
            try:
                ocr_words = await self._extract_ocr_words(frames)
                # 자막 키워드 우선 순위를 유지하며 OCR 키워드 병합
                merged = list(dict.fromkeys(keywords + ocr_words))
                # 길이 제한 (너무 길어지지 않게)
                keywords = merged[:15]
            except Exception as e:
                self.logger.warning(f"OCR keyword merge skipped due to error: {e}")
        
        # 5. 콘텐츠 요약
        summary = self._generate_summary(subtitles, keywords)
        
        analysis = VideoAnalysis(
            video_id=video_id,
            title=video.title,
            duration=video.length,
            subtitles=subtitles,
            frames=frames,
            keywords=keywords,
            summary=summary,
            metadata={
                "author": video.author,
                "views": video.views,
                "publish_date": str(video.publish_date),
            }
        )
        
        # 6. 결과 저장
        await self._save_analysis(analysis)
        
        self.logger.info(f"Analysis complete: {video_id}")
        return analysis
    
    async def _fetch_video_metadata(self, video_url: str) -> Any:
        """비디오 메타데이터 추출 (PyTube)"""
        # 1) 우선 pytubefix 사용
        try:
            from pytubefix import YouTube  # type: ignore
            for attempt in range(self.config.retry_attempts):
                try:
                    video = YouTube(video_url)
                    _ = video.title  # 트리거하여 메타데이터 로드
                    return video
                except Exception as e:
                    self.logger.warning(f"Attempt {attempt + 1} (pytubefix) failed: {e}")
                    if attempt < self.config.retry_attempts - 1:
                        await asyncio.sleep(self.config.retry_delay)
                    else:
                        raise
        except Exception as e:
            self.logger.warning(f"pytubefix unavailable: {e}")

        # 2) 대안: yt-dlp로 메타데이터 수집
        self.logger.info("Falling back to yt-dlp for metadata")
        try:
            import yt_dlp  # type: ignore
        except Exception as e:
            self.logger.error(f"yt-dlp is not available: {e}")
            raise

        ydl_opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        for attempt in range(self.config.retry_attempts):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                    info = ydl.extract_info(video_url, download=False)
                # 간단한 비디오 객체 생성
                class SimpleVideo:
                    def __init__(self, info: Dict[str, Any]):
                        self.title = info.get("title") or ""
                        self.length = float(info.get("duration") or 0.0)
                        self.author = info.get("uploader") or info.get("channel") or ""
                        self.views = int(info.get("view_count") or 0)
                        self.publish_date = info.get("upload_date")  # YYYYMMDD
                        self.video_id = info.get("id") or ""
                        self.webpage_url = info.get("webpage_url") or video_url
                        self._source = "yt_dlp"

                return SimpleVideo(dict(info))
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} (yt-dlp) failed: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    raise
    
    async def _extract_subtitles(self, video_id: str) -> List[Subtitle]:
        """자막 추출 (youtube-transcript-api)"""
        # 지연 임포트
        try:
            from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
        except Exception as e:
            self.logger.warning(f"youtube-transcript-api not available: {e}")
            return []

        try:
            # list() 메서드로 TranscriptList 가져오기
            transcript_list = YouTubeTranscriptApi().list(video_id)
            
            # 영어 또는 한글 자막 찾기
            try:
                transcript = transcript_list.find_transcript(['en', 'ko'])
            except Exception:
                # 사용 가능한 첫 번째 자막 사용 (공개 API로 변환)
                available = list(transcript_list)
                transcript = available[0] if available else None
            
            if not transcript:
                self.logger.warning("No transcripts available")
                return []
            
            # fetch()로 실제 자막 데이터 가져오기
            fetched = transcript.fetch()
            
            subtitles = [
                Subtitle(
                    text=item.text,
                    start=item.start,
                    duration=item.duration
                )
                for item in fetched
            ]
            
            self.logger.info(f"Extracted {len(subtitles)} subtitles")
            return subtitles
        
        except Exception as e:
            self.logger.error(f"Subtitle extraction failed: {e}")
            return []
    
    async def _extract_frames(self, video: Any) -> List[VideoFrame]:
        """프레임 추출 (OpenCV)"""
        try:
            import cv2  # type: ignore
        except Exception as e:
            self.logger.warning(f"OpenCV not available, skipping frame extraction: {e}")
            return []

        video_path = self.config.output_dir / f"{getattr(video, 'video_id', 'video')}_temp.mp4"

        # 1) pytube 객체인 경우
        if hasattr(video, "streams"):
            stream = video.streams.filter(file_extension='mp4').order_by('resolution').first()
            if not stream:
                self.logger.warning("No video stream available (pytube)")
                return []
            stream.download(output_path=str(self.config.output_dir), filename=video_path.name)
        else:
            # 2) yt-dlp 로 다운로드
            try:
                import yt_dlp  # type: ignore
            except Exception as e:
                self.logger.warning(f"yt-dlp not available, skipping frame extraction: {e}")
                return []

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "outtmpl": str(video_path),
                # Prefer lowest reasonable resolution in mp4 to speed up download
                # Fallback to generic worst when mp4 unavailable
                "format": "worst[ext=mp4]/worst",
                "merge_output_format": "mp4",
            }
            # Optionally clip the download to the first N seconds for faster smoke runs
            try:
                clip = int(getattr(self.config, "sample_clip_seconds", 0) or 0)
                if clip > 0:
                    ydl_opts["download_sections"] = {"*": f"0-{clip}"}
            except Exception:
                pass
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                    ydl.download([getattr(video, "webpage_url", "")])
            except Exception as e:
                self.logger.warning(f"yt-dlp download failed: {e}")
                return []
        
        # OpenCV로 프레임 추출
        frames = []
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        if fps <= 0:
            fps = 30.0  # 합리적 기본값
        frame_interval = max(1, int(fps * self.config.frame_interval))
        
        frame_count = 0
        while cap.isOpened() and len(frames) < self.config.max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                frames.append(VideoFrame(
                    timestamp=timestamp,
                    frame=frame
                ))
            
            frame_count += 1
        
        cap.release()
        
        # 임시 파일 삭제
        video_path.unlink(missing_ok=True)
        
        self.logger.info(f"Extracted {len(frames)} frames")
        return frames
    
    def _extract_keywords(self, subtitles: List[Subtitle]) -> List[str]:
        """키워드 추출 (간단한 빈도 기반)"""
        if not subtitles:
            return []
        
        # 모든 자막 텍스트 결합
        text = " ".join([sub.text for sub in subtitles]).lower()
        
        # 단어 빈도 계산 (간단한 구현)
        words = text.split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # 3글자 이상
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 상위 10개 키워드
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        return [word for word, _ in keywords]

    async def _extract_ocr_words(self, frames: List[VideoFrame]) -> List[str]:
        """프레임에서 OCR 실행 후 키워드 후보 추출 (경량 실행)
        - EasyOCR 없으면 빈 리스트 반환
        - 상위 N프레임만 처리하여 성능 보호
        """
        try:
            import easyocr  # type: ignore
        except Exception as e:
            self.logger.warning(f"EasyOCR not available, skipping OCR: {e}")
            return []

        # 리더 생성 (GPU 비활성화로 호환성 우선)
        try:
            reader = easyocr.Reader(["en", "ko"], gpu=False)  # type: ignore
        except Exception as e:
            self.logger.warning(f"EasyOCR reader init failed: {e}")
            return []

        texts: List[str] = []
        limit = max(0, min(self.config.max_ocr_frames, len(frames)))
        for i in range(limit):
            try:
                result = reader.readtext(frames[i].frame)  # type: ignore
                # result: List[ [bbox, text, conf] ]
                if not result:
                    continue
                # 프레임 설명 보강(상위 1~2개만)
                top_texts = []
                for entry in result[:2]:
                    if isinstance(entry, (list, tuple)) and len(entry) >= 2:
                        text_val = entry[1]
                        if isinstance(text_val, str) and text_val.strip():
                            top_texts.append(text_val.strip())
                            texts.append(text_val.strip())
                if top_texts:
                    base_desc = frames[i].description if isinstance(frames[i].description, str) else ""
                    desc = (base_desc + " | " if base_desc else "") + ", ".join(top_texts)
                    frames[i].description = desc[:200]
            except Exception as e:
                # 프레임 단위 실패는 무시하고 다음으로 진행
                self.logger.debug(f"OCR on frame {i} failed: {e}")

        # 간단 빈도 기반으로 Top 5 단어 추출
        if not texts:
            return []
        merged_text = " ".join(texts).lower()
        words = merged_text.split()
        freq = {}
        for w in words:
            if len(w) > 3:
                freq[w] = freq.get(w, 0) + 1
        top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [w for (w, _) in top]
    
    def _generate_summary(self, subtitles: List[Subtitle], keywords: List[str]) -> str:
        """콘텐츠 요약 생성"""
        if not subtitles:
            return "No subtitles available"
        
        # 키워드 기반 간단한 요약
        keyword_str = ", ".join(keywords[:5])
        duration_min = len(subtitles) * 5 / 60  # 대략적인 길이
        
        return f"Video covers topics related to: {keyword_str}. Duration: ~{duration_min:.1f} minutes."
    
    async def _save_analysis(self, analysis: VideoAnalysis):
        """분석 결과 저장"""
        output_file = self.config.output_dir / f"{analysis.video_id}_analysis.json"
        
        # JSON 직렬화 가능한 형식으로 변환
        data = {
            "video_id": analysis.video_id,
            "title": analysis.title,
            "duration": analysis.duration,
            "subtitles_count": len(analysis.subtitles),
            "subtitles": [
                {
                    "start": sub.start,
                    "duration": sub.duration,
                    "text": sub.text
                }
                for sub in analysis.subtitles
            ],
            "frames_count": len(analysis.frames),
            "keywords": analysis.keywords,
            "summary": analysis.summary,
            "metadata": analysis.metadata,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Analysis saved: {output_file}")
    
    @staticmethod
    def _extract_video_id(video_url: str) -> str:
        """YouTube URL에서 video_id 추출"""
        if "youtube.com/watch?v=" in video_url:
            return video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            return video_url.split("youtu.be/")[1].split("?")[0]
        else:
            raise ValueError(f"Invalid YouTube URL: {video_url}")


# ============================================================================
# Playlist Learner (Phase 3)
# ============================================================================

@dataclass
class PlaylistAnalysis:
    """플레이리스트 분석 결과"""
    playlist_title: str
    video_analyses: List[VideoAnalysis]
    combined_summary: str
    total_duration: float

class PlaylistLearner:
    """YouTube 플레이리스트 전체를 학습하고 요약"""
    
    def __init__(self, config: Optional[YouTubeLearnerConfig] = None):
        self.config = config or YouTubeLearnerConfig()
        self.youtube_learner = YouTubeLearner(self.config)
        self.logger = logging.getLogger(__name__)
    
    async def _get_video_urls_from_playlist(self, playlist_url: str) -> Tuple[str, List[str]]:
        """플레이리스트에서 모든 비디오 URL 추출"""
        try:
            from pytubefix import Playlist
        except Exception as e:
            self.logger.error(f"pytubefix not available for Playlist: {e}")
            return "Unknown Playlist", []
        
        playlist = Playlist(playlist_url)
        self.logger.info(f"Fetching videos from playlist: {playlist.title}")
        
        # video_urls는 제너레이터이므로 리스트로 변환
        return playlist.title, list(playlist.video_urls)

    async def learn_series(self, playlist_url: str) -> PlaylistAnalysis:
        """플레이리스트 전체를 학습하고 분석 결과를 반환"""
        playlist_title, video_urls = await self._get_video_urls_from_playlist(playlist_url)
        
        if not video_urls:
            raise ValueError("No videos found in the playlist or playlist is private.")
        
        analyses: List[VideoAnalysis] = []
        total_duration = 0.0
        
        self.logger.info(f"Starting analysis of {len(video_urls)} videos in '{playlist_title}'...")
        
        for i, video_url in enumerate(video_urls):
            try:
                self.logger.info(f"[{i+1}/{len(video_urls)}] Analyzing video: {video_url}")
                analysis = await self.youtube_learner.analyze_video(video_url)
                analyses.append(analysis)
                total_duration += analysis.duration
            except Exception as e:
                self.logger.error(f"Failed to analyze video {video_url}: {e}")
                # Continue with the next video
        
        summary = self._synthesize_knowledge(analyses, playlist_title)
        
        return PlaylistAnalysis(
            playlist_title=playlist_title,
            video_analyses=analyses,
            combined_summary=summary,
            total_duration=total_duration
        )

        def _synthesize_knowledge(self, analyses: List[VideoAnalysis], playlist_title: str) -> str:
            """여러 영상 분석 결과로부터 종합적인 요약 생성 (Lumen Gateway 연동)"""
            if not analyses:
                return "No videos were successfully analyzed."
    
            # Lumen Gateway 사용 가능 시 AI 요약
            if lumen_client_available and get_lumen_client:
                self.logger.info("Synthesizing knowledge with Lumen Gateway...")
                try:
                    client = get_lumen_client()
                    
                    # 모든 자막을 하나의 텍스트로 결합
                    full_transcript = "\n\n".join(
                        " ".join(sub.text for sub in analysis.subtitles)
                        for analysis in analyses if analysis.subtitles
                    )
    
                    if not full_transcript.strip():
                        raise ValueError("No subtitles available to summarize.")
    
                    # Lumen에 보낼 프롬프트 생성
                    prompt = (
                        f"'{playlist_title}'라는 제목의 YouTube 재생목록 전체 자막입니다. "
                        f"이 내용을 바탕으로, 재생목록 전체를 관통하는 핵심 주제, 주요 개념, 그리고 학습 흐름을 "
                        f"3-4 문장으로 요약해주세요.\n\n---\n\n{full_transcript[:8000]}" # 토큰 제한 고려
                    )
                    
                    lumen_response = client.infer(message=prompt, persona_key="square") # '엘로'가 요약에 적합
                    
                    if lumen_response.success:
                        self.logger.info("Lumen Gateway summarization successful.")
                        return f"[AI Summary by {lumen_response.persona.emoji}] {lumen_response.response}"
                    else:
                        self.logger.warning("Lumen Gateway summarization failed, falling back to keyword summary.")
                except Exception as e:
                    self.logger.error(f"Lumen Gateway call failed: {e}, falling back to keyword summary.")
    
            # Fallback: 기존 키워드 기반 요약
            self.logger.info("Falling back to keyword-based summary.")
            all_keywords = []
            for analysis in analyses:
                all_keywords.extend(analysis.keywords)
            
            unique_keywords = list(dict.fromkeys(all_keywords))
            top_keywords = unique_keywords[:10]
            
            summary = (
                f"Playlist '{playlist_title}' contains {len(analyses)} videos. "
                f"Key topics include: {', '.join(top_keywords)}. "
                f"The series covers concepts from '{analyses[0].title}' to '{analyses[-1].title}'."
            )
            
            return f"[Keyword Summary] {summary}"

# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """CLI 테스트"""
    logging.basicConfig(level=logging.INFO)
    
    learner = YouTubeLearner()
    
    # 테스트 영상
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    
    analysis = await learner.analyze_video(test_url)
    
    print(f"\n✅ Analysis Complete:")
    print(f"   Title: {analysis.title}")
    print(f"   Duration: {analysis.duration}s")
    print(f"   Subtitles: {len(analysis.subtitles)}")
    print(f"   Frames: {len(analysis.frames)}")
    print(f"   Keywords: {', '.join(analysis.keywords)}")
    print(f"   Summary: {analysis.summary}")


async def cli_main():
    """CLI 엔트리포인트 (인자 파싱) - PlaylistLearner 테스트"""
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="YouTube Playlist Learner")
    # A short, stable playlist is good for testing.
    parser.add_argument("--playlist-url", default="https://www.youtube.com/playlist?list=PL-gS-8J9C_z-P-3s1hS-t3Wn1-JCRp1nK", help="YouTube playlist URL")
    args = parser.parse_args()

    cfg = YouTubeLearnerConfig(
        max_frames=1, # Keep it low for testing
        frame_interval=60.0,
        enable_ocr=False,
    )
    
    playlist_learner = PlaylistLearner(cfg)

    try:
        playlist_analysis = await playlist_learner.learn_series(args.playlist_url)
        
        print("\n✅ Playlist Analysis Complete:")
        print(f"   Playlist Title: {playlist_analysis.playlist_title}")
        print(f"   Videos Analyzed: {len(playlist_analysis.video_analyses)}")
        print(f"   Total Duration: {playlist_analysis.total_duration / 60:.2f} minutes")
        print(f"\n   Combined Summary:")
        print(f"   {playlist_analysis.combined_summary}")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(cli_main())
