"""
Comet-AGI Integration Layer
Phase 2.5: RPA + YouTube Learning

통합 모듈:
- comet_client: Comet Browser Worker HTTP/WebSocket Client
- youtube_handler: YouTube 메타데이터 및 자막 처리
- rpa_bridge: RPA 명령 전달 및 결과 수신
"""

from .comet_client import (
    CometConfig,
    CometHTTPClient,
    CometResponse,
)

from .youtube_handler import (
    YouTubeHandler,
    YouTubeVideoInfo,
    YouTubeSubtitle,
)

__all__ = [
    # Comet Client
    'CometConfig',
    'CometHTTPClient',
    'CometResponse',
    
    # YouTube Handler
    'YouTubeHandler',
    'YouTubeVideoInfo',
    'YouTubeSubtitle',
]

__version__ = "0.1.0"
