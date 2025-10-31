"""
YouTube Handler Module
Phase 2.5 Day 2: YouTube 자동화 학습 (yt-dlp 연동)

담당: yt-dlp로 비디오 메타데이터, 자막, 썸네일 추출
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import yt_dlp  # type: ignore


@dataclass
class YouTubeVideoInfo:
    """
    YouTube 비디오 메타데이터
    
    Attributes:
        video_id: YouTube 비디오 ID (예: dQw4w9WgXcQ)
        title: 제목
        description: 설명
        duration: 길이 (초)
        view_count: 조회수
        like_count: 좋아요 수
        channel: 채널명
        upload_date: 업로드 날짜 (YYYYMMDD)
        thumbnail_url: 썸네일 URL (최고 해상도)
        subtitles: 자막 언어 목록 (예: ['ko', 'en'])
        raw_data: yt-dlp 원본 데이터
    """
    video_id: str
    title: str
    description: str
    duration: int
    view_count: int
    like_count: int
    channel: str
    upload_date: str
    thumbnail_url: str
    subtitles: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_ytdlp(cls, info_dict: Dict[str, Any]) -> 'YouTubeVideoInfo':
        """
        yt-dlp info_dict → YouTubeVideoInfo 변환
        
        Args:
            info_dict: yt-dlp extract_info() 결과
        
        Returns:
            YouTubeVideoInfo 인스턴스
        """
        return cls(
            video_id=info_dict.get('id', 'unknown'),
            title=info_dict.get('title', 'No Title'),
            description=info_dict.get('description', ''),
            duration=info_dict.get('duration', 0),
            view_count=info_dict.get('view_count', 0),
            like_count=info_dict.get('like_count', 0),
            channel=info_dict.get('channel', info_dict.get('uploader', 'Unknown')),
            upload_date=info_dict.get('upload_date', ''),
            thumbnail_url=info_dict.get('thumbnail', ''),
            subtitles=list(info_dict.get('subtitles', {}).keys()),
            raw_data=info_dict
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화 가능한 dict 반환"""
        return {
            'video_id': self.video_id,
            'title': self.title,
            'description': self.description[:500],  # 설명 500자 제한
            'duration': self.duration,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'channel': self.channel,
            'upload_date': self.upload_date,
            'thumbnail_url': self.thumbnail_url,
            'subtitles': self.subtitles
        }


@dataclass
class YouTubeSubtitle:
    """
    YouTube 자막 데이터
    
    Attributes:
        video_id: YouTube 비디오 ID
        language: 자막 언어 코드 (예: 'ko', 'en')
        text: 전체 자막 텍스트
        segments: 타임스탬프 구간별 자막 리스트
        format: 자막 포맷 (예: 'srt', 'vtt')
    """
    video_id: str
    language: str
    text: str
    segments: List[Dict[str, Any]] = field(default_factory=list)
    format: str = 'srt'
    
    @property
    def line_count(self) -> int:
        """자막 라인 수"""
        return len(self.text.strip().split('\n'))
    
    @property
    def word_count(self) -> int:
        """단어 수 (공백 기준)"""
        return len(self.text.split())


class YouTubeHandler:
    """
    YouTube 비디오 정보 추출 및 자막 다운로드
    
    yt-dlp 기반 비동기 인터페이스 제공
    
    Usage:
        handler = YouTubeHandler(output_dir='outputs/youtube')
        
        # 메타데이터 추출
        info = await handler.get_video_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        print(info.title, info.duration, info.view_count)
        
        # 자막 다운로드
        subtitle = await handler.download_subtitle(
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            language='ko'
        )
        print(subtitle.text)
    """
    
    def __init__(
        self,
        output_dir: str = 'outputs/youtube',
        quiet: bool = True,
        extract_subtitles: bool = True
    ):
        """
        Args:
            output_dir: 자막/썸네일 저장 디렉토리
            quiet: yt-dlp 로그 출력 억제
            extract_subtitles: 자막 자동 추출 여부
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.quiet = quiet
        self.extract_subtitles = extract_subtitles
        
        self.logger = logging.getLogger("YouTubeHandler")
        
        # yt-dlp 기본 옵션
        self.ytdl_opts = {
            'quiet': self.quiet,
            'no_warnings': True,
            'extract_flat': False,
            'writesubtitles': self.extract_subtitles,
            'writeautomaticsub': True,
            'subtitleslangs': ['ko', 'en'],
            'skip_download': True,
            'outtmpl': str(self.output_dir / '%(id)s.%(ext)s')
        }
    
    async def get_video_info(self, url: str) -> Optional[YouTubeVideoInfo]:
        """
        비디오 메타데이터 추출 (다운로드 없음)
        
        Args:
            url: YouTube 비디오 URL 또는 video_id
        
        Returns:
            YouTubeVideoInfo 또는 None (실패 시)
        
        Example:
            info = await handler.get_video_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
            print(f"{info.title} ({info.duration}초, 조회수 {info.view_count:,})")
        """
        try:
            self.logger.info(f"[YouTube] Fetching info: {url}")
            
            # yt-dlp 동기 함수 → async 실행
            info_dict = await asyncio.to_thread(
                self._extract_info_sync, url
            )
            
            if not info_dict:
                return None
            
            video_info = YouTubeVideoInfo.from_ytdlp(info_dict)
            
            self.logger.info(
                f"[YouTube] ✅ {video_info.title} "
                f"(ID: {video_info.video_id}, {video_info.duration}초)"
            )
            
            return video_info
        
        except Exception as e:
            self.logger.error(f"[YouTube] ❌ Failed to fetch info: {e}")
            return None
    
    def _extract_info_sync(self, url: str) -> Optional[Dict[str, Any]]:
        """
        yt-dlp extract_info() 동기 래퍼
        
        Args:
            url: YouTube URL
        
        Returns:
            info_dict 또는 None
        """
        with yt_dlp.YoutubeDL(self.ytdl_opts) as ydl:  # type: ignore
            try:
                info = ydl.extract_info(url, download=False)
                return info  # type: ignore
            except Exception as e:
                self.logger.error(f"[YouTube] extract_info error: {e}")
                return None
    
    async def download_subtitle(
        self,
        url: str,
        language: str = 'ko',
        fallback: bool = True
    ) -> Optional[YouTubeSubtitle]:
        """
        자막 다운로드 (자동생성 자막 포함)
        
        Args:
            url: YouTube 비디오 URL
            language: 자막 언어 ('ko', 'en' 등)
            fallback: 해당 언어 없으면 영어(en) 시도
        
        Returns:
            YouTubeSubtitle 또는 None (자막 없음)
        
        Example:
            sub = await handler.download_subtitle(
                'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                language='ko'
            )
            if sub:
                print(f"자막 라인 수: {sub.line_count}, 단어 수: {sub.word_count}")
        """
        try:
            self.logger.info(f"[YouTube] Downloading subtitle ({language}): {url}")
            
            # 자막 다운로드 옵션
            opts = {
                **self.ytdl_opts,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': [language] if not fallback else [language, 'en'],
                'skip_download': True,
                'subtitlesformat': 'srt'
            }
            
            # yt-dlp 실행
            subtitle_text = await asyncio.to_thread(
                self._download_subtitle_sync, url, language, opts
            )
            
            if not subtitle_text:
                if fallback and language != 'en':
                    self.logger.warning(f"[YouTube] No {language} subtitle, trying en")
                    return await self.download_subtitle(url, language='en', fallback=False)
                return None
            
            # 비디오 ID 추출
            info = await self.get_video_info(url)
            video_id = info.video_id if info else 'unknown'
            
            subtitle = YouTubeSubtitle(
                video_id=video_id,
                language=language,
                text=subtitle_text,
                format='srt'
            )
            
            self.logger.info(
                f"[YouTube] ✅ Subtitle downloaded: "
                f"{subtitle.line_count} lines, {subtitle.word_count} words"
            )
            
            return subtitle
        
        except Exception as e:
            self.logger.error(f"[YouTube] ❌ Subtitle download failed: {e}")
            return None
    
    def _download_subtitle_sync(
        self,
        url: str,
        language: str,
        opts: Dict[str, Any]
    ) -> Optional[str]:
        """
        자막 다운로드 동기 래퍼
        
        Args:
            url: YouTube URL
            language: 자막 언어
            opts: yt-dlp 옵션
        
        Returns:
            자막 텍스트 또는 None
        """
        with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore
            try:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # 자막 파일 경로 추정
                video_id = info.get('id', 'unknown')
                subtitle_file = self.output_dir / f"{video_id}.{language}.srt"
                
                # yt-dlp는 자막을 자동 다운로드 (writesubtitles=True)
                # 하지만 skip_download=True면 파일 생성 안 함
                # 따라서 subtitles dict에서 직접 추출
                
                subtitles = info.get('subtitles', {})
                auto_subs = info.get('automatic_captions', {})
                
                # 수동 자막 우선, 없으면 자동 자막
                sub_data = subtitles.get(language) or auto_subs.get(language)
                
                if not sub_data:
                    return None
                
                # srt 형식 URL 찾기
                srt_url = None
                for fmt in sub_data:
                    if fmt.get('ext') == 'srt':
                        srt_url = fmt.get('url')
                        break
                
                if not srt_url:
                    return None
                
                # 자막 다운로드 (HTTP GET)
                import requests
                response = requests.get(srt_url, timeout=10)
                response.raise_for_status()
                
                return response.text
            
            except Exception as e:
                self.logger.error(f"[YouTube] Subtitle sync error: {e}")
                return None
    
    async def save_video_info_json(
        self,
        url: str,
        filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        비디오 메타데이터를 JSON 파일로 저장
        
        Args:
            url: YouTube URL
            filename: 저장 파일명 (기본값: {video_id}_info.json)
        
        Returns:
            저장된 파일 경로 또는 None
        
        Example:
            path = await handler.save_video_info_json('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
            print(f"Saved to: {path}")
        """
        try:
            info = await self.get_video_info(url)
            
            if not info:
                return None
            
            if not filename:
                filename = f"{info.video_id}_info.json"
            
            output_path = self.output_dir / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(info.to_dict(), f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"[YouTube] ✅ Saved info: {output_path}")
            
            return output_path
        
        except Exception as e:
            self.logger.error(f"[YouTube] ❌ Failed to save info: {e}")
            return None


# Standalone Test
if __name__ == "__main__":
    async def main():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        
        print("\n" + "=" * 60)
        print("YOUTUBE HANDLER TEST")
        print("=" * 60 + "\n")
        
        handler = YouTubeHandler(output_dir='outputs/youtube_test')
        
        # Test 1: 메타데이터 추출
        print("TEST 1: 메타데이터 추출")
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        info = await handler.get_video_info(test_url)
        
        if info:
            print(f"✅ 제목: {info.title}")
            print(f"   채널: {info.channel}")
            print(f"   길이: {info.duration}초")
            print(f"   조회수: {info.view_count:,}")
            print(f"   좋아요: {info.like_count:,}")
            print(f"   자막 언어: {', '.join(info.subtitles) if info.subtitles else '없음'}")
        else:
            print("❌ 메타데이터 추출 실패")
        
        # Test 2: 자막 다운로드 (영어)
        print(f"\nTEST 2: 자막 다운로드 (영어)")
        
        subtitle = await handler.download_subtitle(test_url, language='en')
        
        if subtitle:
            print(f"✅ 자막 언어: {subtitle.language}")
            print(f"   라인 수: {subtitle.line_count}")
            print(f"   단어 수: {subtitle.word_count}")
            print(f"   미리보기: {subtitle.text[:200]}...")
        else:
            print("❌ 자막 다운로드 실패")
        
        # Test 3: JSON 저장
        print(f"\nTEST 3: JSON 저장")
        
        path = await handler.save_video_info_json(test_url)
        
        if path:
            print(f"✅ 저장 완료: {path}")
        else:
            print("❌ JSON 저장 실패")
        
        print("\n" + "=" * 60)
    
    asyncio.run(main())
