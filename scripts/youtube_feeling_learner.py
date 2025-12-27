#!/usr/bin/env python3
"""
YouTube Feeling Learner - Vertex AI Native
==========================================
Lightweight, feeling-based YouTube learning using Vertex AI (Google Cloud).

Key Features:
- Uses Vertex AI (140만원 크레딧 활용)
- Feeling extraction (emotional tone, not just keywords)
- Resonance integration (stores in resonance_ledger.jsonl)
- Context-aware (WWW metadata: When, Where, Who)

Usage:
    python youtube_feeling_learner.py --url "https://youtube.com/watch?v=..."
"""

import argparse
import asyncio
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

import numpy as np

# Optional backends (Vertex AI / GenAI)
VERTEX_AVAILABLE = False
GENAI_AVAILABLE = False
try:  # Vertex AI
    import vertexai  # type: ignore
    from vertexai.generative_models import GenerativeModel, Part  # type: ignore
    from vertexai.language_models import TextEmbeddingModel  # type: ignore

    VERTEX_AVAILABLE = True
except Exception:
    VERTEX_AVAILABLE = False

try:  # Google AI Studio (GenAI)
    import google.generativeai as genai  # type: ignore

    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False

from youtube_transcript_api import YouTubeTranscriptApi

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
OUTPUT_DIR = WORKSPACE_ROOT / "outputs" / "youtube_feelings"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_dotenv_value(key: str) -> str:
    try:
        for env_path in (WORKSPACE_ROOT / ".env_credentials", WORKSPACE_ROOT / ".env"):
            if not env_path.exists():
                continue
            for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() != key:
                    continue
                v = v.strip().strip("'").strip('"')
                return v
    except Exception:
        return ""
    return ""


@dataclass
class FeelingAnalysis:
    """YouTube video feeling analysis result"""
    video_id: str
    title: str
    duration: float
    
    # Gemini-extracted feelings
    emotional_tone: str           # e.g., "차분한", "열정적", "우울한"
    core_message: str             # 1-2 sentence summary
    resonance_themes: List[str]   # e.g., ["배경자아", "리듬", "공명"]
    
    # Feeling vector (768-dim from Gemini embedding)
    feeling_vector: List[float]
    
    # Context metadata (WWW)
    timestamp: str
    analyzed_by: str = "sian"
    context: str = ""
    
    # Raw data
    subtitle_text: str = ""
    metadata: Dict[str, Any] = None


class YouTubeFeelingLearner:
    """Vertex AI-native YouTube feeling learner (using Ion Mentoring config)"""
    
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        """
        Initialize learner with Vertex AI.
        
        Args:
            project_id: GCP project ID (defaults to ion_mentoring config)
            location: GCP region (default: us-central1)
        """
        # Use ion_mentoring config priority
        if not project_id:
            project_id = (
                os.getenv("VERTEX_PROJECT_ID") 
                or os.getenv("GOOGLE_CLOUD_PROJECT")
                or os.getenv("GCP_PROJECT")
                or "naeda-genesis"  # Ion Mentoring default
            )
        
        location = (
            os.getenv("VERTEX_LOCATION")
            or os.getenv("GCP_LOCATION") 
            or location
        )
        
        self.backend = "none"  # 'genai' | 'vertex' | 'none'
        self.model = None
        self.embedding_model = None

        # Prefer GenAI when API key exists (works without service account / ADC).
        api_key = (
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("GENAI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or _load_dotenv_value("GOOGLE_API_KEY")
            or _load_dotenv_value("GENAI_API_KEY")
            or _load_dotenv_value("GEMINI_API_KEY")
            or ""
        ).strip()

        # Vertex is opt-in to avoid noisy failures on machines without ADC/service-account.
        use_vertex = str(os.getenv("AGI_USE_VERTEX", "")).strip().lower() in ("1", "true", "yes", "on")

        if api_key and GENAI_AVAILABLE:
            try:
                genai.configure(api_key=api_key)
                # Prefer 2.5 flash; fallback to 2.0 flash (GenAI에서 1.5 계열이 비활성인 환경이 있어 제외).
                preferred = (
                    os.getenv("GEMINI_FAST_MODEL")
                    or os.getenv("GEMINI_MODEL")
                    or "gemini-2.5-flash"
                ).strip()
                candidates = [
                    preferred,
                    "gemini-2.5-flash",
                    "gemini-2.0-flash-001",
                    "gemini-2.0-flash",
                ]
                model_name = ""
                for cand in candidates:
                    try:
                        if not cand:
                            continue
                        self.model = genai.GenerativeModel(cand)
                        model_name = cand
                        break
                    except Exception:
                        continue
                if not self.model:
                    raise RuntimeError("No available GenAI model (tried: " + ", ".join([c for c in candidates if c]) + ")")
                self.backend = "genai"
                print("✅ YouTube Feeling Learner initialized (GenAI)")
                print(f"   Model: {model_name}")
                return
            except Exception as e:
                print(f"⚠️ GenAI initialization failed: {e}")

        if use_vertex and VERTEX_AVAILABLE:
            try:
                vertexai.init(project=project_id, location=location)
                vertex_model = (os.getenv("VERTEX_MODEL_GEMINI") or "gemini-2.5-flash").strip()
                self.model = GenerativeModel(vertex_model)
                self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
                self.backend = "vertex"
                print("✅ YouTube Feeling Learner initialized (Vertex AI)")
                print(f"   Project: {project_id}")
                print(f"   Location: {location}")
                print(f"   Model: {vertex_model}")
                return
            except Exception as e:
                print(f"⚠️ Vertex AI initialization failed: {e}")

        raise RuntimeError(
            "No usable LLM backend for YouTubeFeelingLearner (need GenAI API key or AGI_USE_VERTEX=1 with Vertex credentials)."
        )
    
    async def analyze_feeling(
        self, 
        video_url: str, 
        context: str = "",
        analyzed_by: str = "sian"
    ) -> FeelingAnalysis:
        """
        Analyze YouTube video feeling.
        
        Args:
            video_url: YouTube video URL
            context: Optional context (e.g., "배경자아 연구 중")
            analyzed_by: Who is analyzing (default: "sian")
        
        Returns:
            FeelingAnalysis object
        """
        video_id = self._extract_video_id(video_url)
        print(f"\n📺 Analyzing: {video_url}")
        print(f"   Video ID: {video_id}")
        
        # 1. Get subtitles
        print("   [1/4] Fetching subtitles...")
        subtitles = self._get_subtitles(video_id)
        subtitle_text = " ".join([s['text'] for s in subtitles])
        
        video_info = {}
        if not subtitle_text:
            print("   ⚠️ No subtitles found, trying yt-dlp fallback...")
            video_info = self._get_video_info_fallback(video_url)
            if video_info:
                subtitle_text = f"Title: {video_info.get('title')}\nDescription: {video_info.get('description')}"
                print(f"   ✅ Retrieved metadata via yt-dlp: {video_info.get('title')}")
        
        # 2. Extract feeling with Gemini
        print("   [2/4] Extracting feeling (Gemini)...")
        feeling_data = self._extract_feeling_with_gemini(video_url, subtitle_text[:3000])
        
        # 3. Create feeling vector
        print("   [3/4] Creating feeling vector...")
        feeling_vector = self._create_feeling_vector(feeling_data, subtitle_text[:1500])
        
        # 4. Get video metadata
        print("   [4/4] Gathering metadata...")
        if video_info:
            title = video_info.get('title', f"YouTube Video {video_id}")
            duration = video_info.get('duration', 0.0)
        else:
            title, duration = self._get_video_metadata(video_id, subtitle_text)
        
        # Create analysis
        analysis = FeelingAnalysis(
            video_id=video_id,
            title=title,
            duration=duration,
            emotional_tone=feeling_data['emotional_tone'],
            core_message=feeling_data['core_message'],
            resonance_themes=feeling_data['resonance_themes'],
            feeling_vector=feeling_vector.tolist(),
            timestamp=datetime.now().isoformat(),
            analyzed_by=analyzed_by,
            context=context,
            subtitle_text=subtitle_text[:500],  # First 500 chars for reference
            metadata={
                'video_url': video_url,
                'subtitle_count': len(subtitles)
            }
        )
        
        # 5. Save to resonance ledger
        self._save_to_resonance_ledger(analysis)
        
        # 6. Cache analysis
        self._cache_analysis(analysis)
        
        print(f"\n✅ Analysis complete!")
        print(f"   Emotional tone: {analysis.emotional_tone}")
        print(f"   Core message: {analysis.core_message}")
        print(f"   Themes: {', '.join(analysis.resonance_themes)}")
        
        return analysis

    def _hash_embedding(self, text: str, dim: int = 768) -> np.ndarray:
        import hashlib

        base = (text or "").encode("utf-8", errors="ignore")
        out: list[float] = []
        counter = 0
        while len(out) < dim:
            h = hashlib.sha256(base + b"|" + str(counter).encode("ascii")).digest()
            for b in h:
                # Map 0..255 -> -1..1
                out.append((b / 127.5) - 1.0)
                if len(out) >= dim:
                    break
            counter += 1
        return np.array(out[:dim], dtype=np.float32)
    
    def _extract_video_id(self, video_url: str) -> str:
        """Extract video ID from YouTube URL"""
        if "youtube.com/watch?v=" in video_url:
            return video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            return video_url.split("youtu.be/")[1].split("?")[0]
        else:
            raise ValueError(f"Invalid YouTube URL: {video_url}")
    
    def _get_subtitles(self, video_id: str) -> List[Dict]:
        """Get video subtitles using youtube-transcript-api"""
        try:
            # Some environments ship an older youtube-transcript-api that does not provide
            # list_transcripts(). Prefer it when available; otherwise fall back to get_transcript().
            if hasattr(YouTubeTranscriptApi, "list_transcripts"):
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)  # type: ignore[attr-defined]

                # Try to get Korean or English subtitles
                try:
                    transcript = transcript_list.find_transcript(['ko', 'en'])
                except Exception:
                    # Fall back to first available
                    available = list(transcript_list)
                    if not available:
                        return []
                    transcript = available[0]

                return transcript.fetch()

            # Fallback: get_transcript (older api surface)
            if hasattr(YouTubeTranscriptApi, "get_transcript"):
                for langs in (['ko'], ['en'], ['ko', 'en']):
                    try:
                        return YouTubeTranscriptApi.get_transcript(video_id, languages=langs)  # type: ignore[attr-defined]
                    except Exception:
                        continue
                return []

            return []
        
        except Exception as e:
            print(f"   ⚠️ Subtitle extraction failed: {e}")
            return []
    
    def _extract_feeling_with_gemini(self, video_url: str, subtitle_text: str) -> Dict:
        """Extract feeling using Gemini"""
        
        prompt = f"""당신은 비노체의 "느낌 분석가"입니다.

이 YouTube 영상을 분석하여 다음을 추출하세요:

1. **감정적 톤** (한 단어로): 차분한, 열정적, 우울한, 긴장된, 명상적, 활기찬 등
2. **핵심 메시지** (1-2문장): 영상의 가장 중요한 메시지
3. **공명하는 주제들** (5개 키워드): 배경자아, 리듬, 공명, 존재, 의식 등과 관련된 주제

영상 URL: {video_url}

자막 (일부):
{subtitle_text if subtitle_text else "자막 없음 - URL로 판단"}

반드시 다음 JSON 형식으로만 답변하세요 (다른 설명 없이):
{{
  "emotional_tone": "...",
  "core_message": "...",
  "resonance_themes": ["...", "...", "...", "...", "..."]
}}"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            feeling_data = json.loads(text)
            
            # Validate
            required_keys = ['emotional_tone', 'core_message', 'resonance_themes']
            if not all(k in feeling_data for k in required_keys):
                raise ValueError("Missing required keys in response")
            
            return feeling_data
        
        except Exception as e:
            print(f"   ⚠️ Feeling extraction failed: {e}, using defaults")
            return {
                'emotional_tone': '중립적',
                'core_message': subtitle_text[:200] if subtitle_text else "내용 분석 불가",
                'resonance_themes': ['youtube', 'content', 'learning', 'media', 'analysis']
            }
    
    def _create_feeling_vector(self, feeling_data: Dict, subtitle_text: str) -> np.ndarray:
        """Create feeling embedding vector (Vertex if available, else deterministic hash)."""
        
        # Combine feeling data for embedding
        combined_text = f"{feeling_data['emotional_tone']}. {feeling_data['core_message']}. "
        combined_text += f"주제: {', '.join(feeling_data['resonance_themes'])}. "
        combined_text += subtitle_text
        
        if self.backend == "vertex" and self.embedding_model is not None:
            try:
                embeddings = self.embedding_model.get_embeddings([combined_text])
                vector = np.array(embeddings[0].values)
                if vector.shape[0] != 768:
                    v = np.zeros(768, dtype=np.float32)
                    v[: min(768, vector.shape[0])] = vector[: min(768, vector.shape[0])]
                    return v
                return vector
            except Exception as e:
                print(f"   ⚠️ Vertex embedding failed: {e}, using hash embedding")

        return self._hash_embedding(combined_text, dim=768)
    
    def _get_video_metadata(self, video_id: str, subtitle_text: str) -> tuple:
        """
        Get video metadata (title, duration).
        Falls back to subtitle-based estimation if API unavailable.
        """
        # For now, use simple estimation
        # TODO: Add YouTube Data API v3 integration if needed
        
        title = f"YouTube Video {video_id}"
        
        # Estimate duration from subtitle length (rough: 150 words/min)
        word_count = len(subtitle_text.split())
        duration = (word_count / 150) * 60 if word_count > 0 else 0.0
        
        return title, duration

    def _get_video_info_fallback(self, video_url: str) -> Dict:
        """Fetch video metadata using yt-dlp as fallback (Host Relay supported)"""
        video_id = self._extract_video_id(video_url)
        
        # 1. Check for Host-provided JSON in outputs dir
        host_json_path = OUTPUT_DIR.parent / f"{video_id}.info.json"
        if host_json_path.exists():
            print(f"   ✅ Found Host-provided metadata: {host_json_path.name}")
            try:
                with open(host_json_path, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    return {
                        'title': info.get('title', ''),
                        'description': info.get('description', ''),
                        'tags': info.get('tags', []),
                        'duration': info.get('duration', 0)
                    }
            except Exception as e:
                print(f"   ⚠️ Failed to read host JSON: {e}")

        # 2. Try local yt-dlp
        try:
            import yt_dlp
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'extract_flat': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return {
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'tags': info.get('tags', []),
                    'duration': info.get('duration', 0)
                }
        except Exception as e:
            print(f"   ⚠️ yt-dlp fallback failed: {e}")
            return {}

    
    def _save_to_resonance_ledger(self, analysis: FeelingAnalysis):
        """Save analysis to resonance_ledger.jsonl"""
        
        entry = {
            "type": "youtube_feeling",
            "timestamp": analysis.timestamp,
            "video_id": analysis.video_id,
            "summary": f"[YouTube] {analysis.title}",
            "narrative": analysis.core_message,
            "vector": analysis.feeling_vector,
            "metadata": {
                "emotional_tone": analysis.emotional_tone,
                "resonance_themes": analysis.resonance_themes,
                "duration": analysis.duration,
                "analyzed_by": analysis.analyzed_by,
                "context": analysis.context,
                "video_url": analysis.metadata.get('video_url', '')
            }
        }
        
        try:
            LEDGER_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LEDGER_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
            print(f"   ✅ Saved to resonance ledger: {LEDGER_FILE}")
        
        except Exception as e:
            print(f"   ⚠️ Failed to save to ledger: {e}")
    
    def _cache_analysis(self, analysis: FeelingAnalysis):
        """Cache analysis to local file"""
        
        cache_file = OUTPUT_DIR / f"{analysis.video_id}_feeling.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(analysis), f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Cached to: {cache_file}")
        
        except Exception as e:
            print(f"   ⚠️ Failed to cache: {e}")


async def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="YouTube Feeling Learner (Vertex AI)"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="YouTube video URL"
    )
    parser.add_argument(
        "--context",
        default="",
        help="Analysis context (e.g., '배경자아 연구 중')"
    )
    parser.add_argument(
        "--analyzed-by",
        default="sian",
        help="Who is analyzing (default: sian)"
    )
    parser.add_argument(
        "--project-id",
        default=None,
        help="GCP project ID (defaults to gcloud config)"
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="GCP region (default: us-central1)"
    )
    
    args = parser.parse_args()
    
    try:
        learner = YouTubeFeelingLearner(
            project_id=args.project_id,
            location=args.location
        )
        analysis = await learner.analyze_feeling(
            video_url=args.url,
            context=args.context,
            analyzed_by=args.analyzed_by
        )
        
        print("\n" + "="*80)
        print("📊 ANALYSIS SUMMARY")
        print("="*80)
        print(f"Title: {analysis.title}")
        print(f"Emotional Tone: {analysis.emotional_tone}")
        print(f"Core Message: {analysis.core_message}")
        print(f"Themes: {', '.join(analysis.resonance_themes)}")
        print(f"Duration: {analysis.duration:.1f}s")
        print(f"Context: {analysis.context or 'None'}")
        print("="*80)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
