"""
API 통합 라우터

v1 및 v2 엔드포인트 통합 관리
- 버전 감지
- 자동 호환성
- 마이그레이션 지원
"""

import logging
from typing import Optional

from fastapi import APIRouter, Header

logger = logging.getLogger(__name__)

# Import v1 and v2 routes
# from . import v1_routes
from .v2_routes import router as v2_router


def create_api_router() -> APIRouter:
    """
    API 통합 라우터 생성

    v1과 v2를 모두 지원하며 자동 버전 감지
    """
    main_router = APIRouter()

    # v2 라우트 추가
    main_router.include_router(v2_router)

    # v1 라우트는 호환성을 위해 v2로 리디렉션 (나중에 구현)
    # main_router.include_router(v1_router)

    return main_router


# 버전 감지 미들웨어
class APIVersionMiddleware:
    """API 버전 감지 및 관리"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]

            # 버전 감지
            if "/api/v1/" in path:
                scope["api_version"] = "v1"
            elif "/api/v2/" in path:
                scope["api_version"] = "v2"
            else:
                # 기본값: 최신 버전 (v2)
                if "/api/" in path and not path.startswith("/api/v"):
                    # /api/... 형태는 v2로 간주
                    scope["api_version"] = "v2"
                scope["api_version"] = "unknown"

        await self.app(scope, receive, send)


def get_api_version_from_header(
    x_api_version: Optional[str] = Header(None), accept: Optional[str] = Header(None)
) -> str:
    """
    헤더에서 API 버전 감지

    Priority:
    1. X-API-Version 헤더
    2. Accept 헤더의 버전 정보
    3. 기본값: v2
    """
    if x_api_version:
        if x_api_version in ["v1", "v2"]:
            return x_api_version
        logger.warning(f"Invalid API version header: {x_api_version}")

    if accept and "version=" in accept:
        try:
            version = accept.split("version=")[1].split(";")[0].strip()
            if version in ["v1", "v2"]:
                return version
        except (IndexError, AttributeError):
            pass

    # 기본값
    return "v2"
