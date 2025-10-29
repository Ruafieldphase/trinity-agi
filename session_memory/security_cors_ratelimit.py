#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORS 및 레이트 제한 정책 - API 보안

이 모듈은 CORS 설정과 고급 레이트 제한을 제공합니다.
"""

import sys
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from collections import defaultdict

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# CORS 정책
# ============================================================================

class CORSPolicy:
    """CORS (Cross-Origin Resource Sharing) 정책"""

    def __init__(
        self,
        allowed_origins: List[str] = None,
        allowed_methods: List[str] = None,
        allowed_headers: List[str] = None,
        exposed_headers: List[str] = None,
        max_age: int = 3600,
        allow_credentials: bool = True
    ):
        """
        초기화

        Args:
            allowed_origins: 허용 오리진 (예: ["https://example.com", "*"])
            allowed_methods: 허용 HTTP 메서드
            allowed_headers: 허용 요청 헤더
            exposed_headers: 노출할 응답 헤더
            max_age: preflight 캐시 시간 (초)
            allow_credentials: 자격 증명 허용 여부
        """
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or [
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "Accept"
        ]
        self.exposed_headers = exposed_headers or [
            "Content-Type",
            "X-Total-Count",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining"
        ]
        self.max_age = max_age
        self.allow_credentials = allow_credentials

    def is_origin_allowed(self, origin: str) -> bool:
        """
        오리진 허용 여부 확인

        Args:
            origin: 요청 오리진

        Returns:
            허용 여부
        """
        if "*" in self.allowed_origins:
            return True

        return origin in self.allowed_origins

    def get_response_headers(self, origin: str) -> Dict[str, str]:
        """
        CORS 응답 헤더 생성

        Args:
            origin: 요청 오리진

        Returns:
            CORS 헤더 딕셔너리
        """
        headers = {}

        if self.is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin if origin != "*" else "*"

        headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
        headers["Access-Control-Expose-Headers"] = ", ".join(self.exposed_headers)
        headers["Access-Control-Max-Age"] = str(self.max_age)

        if self.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"

        return headers

    def __repr__(self):
        return f"<CORSPolicy origins={len(self.allowed_origins)}, methods={len(self.allowed_methods)}>"


# ============================================================================
# 사전 정의된 CORS 정책
# ============================================================================

class CORSPolicies:
    """사전 정의된 CORS 정책"""

    @staticmethod
    def development() -> CORSPolicy:
        """개발 환경 CORS 정책"""
        return CORSPolicy(
            allowed_origins=["*"],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            allowed_headers=["*"],
            max_age=3600
        )

    @staticmethod
    def production() -> CORSPolicy:
        """프로덕션 환경 CORS 정책"""
        return CORSPolicy(
            allowed_origins=[
                "https://app.example.com",
                "https://dashboard.example.com"
            ],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allowed_headers=[
                "Content-Type",
                "Authorization",
                "X-API-Key",
                "Accept",
                "Accept-Language"
            ],
            exposed_headers=[
                "Content-Type",
                "X-Total-Count",
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset"
            ],
            max_age=7200,
            allow_credentials=True
        )

    @staticmethod
    def public_api() -> CORSPolicy:
        """공개 API CORS 정책"""
        return CORSPolicy(
            allowed_origins=["*"],
            allowed_methods=["GET", "OPTIONS"],
            allowed_headers=["Content-Type", "Accept"],
            exposed_headers=["Content-Type", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
            max_age=86400,
            allow_credentials=False
        )

    @staticmethod
    def internal_api() -> CORSPolicy:
        """내부 API CORS 정책"""
        return CORSPolicy(
            allowed_origins=[
                "http://localhost:3000",
                "http://localhost:5000",
                "http://internal-api.local"
            ],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            allowed_headers=["*"],
            max_age=3600,
            allow_credentials=True
        )


# ============================================================================
# 고급 레이트 제한
# ============================================================================

class RateLimitStrategy(Enum):
    """레이트 제한 전략"""
    FIXED_WINDOW = "fixed_window"          # 고정 시간 창
    SLIDING_WINDOW = "sliding_window"      # 슬라이딩 시간 창
    TOKEN_BUCKET = "token_bucket"          # 토큰 버킷


class AdvancedRateLimiter:
    """고급 레이트 제한"""

    def __init__(
        self,
        strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET,
        default_limit: int = 1000,
        window_seconds: int = 60
    ):
        """
        초기화

        Args:
            strategy: 제한 전략
            default_limit: 기본 제한 수
            window_seconds: 시간 창 (초)
        """
        self.strategy = strategy
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.request_history: Dict[str, List[datetime]] = defaultdict(list)
        self.tokens: Dict[str, float] = defaultdict(float)
        self.windows: Dict[str, datetime] = {}

    def check_rate_limit(self, key: str, limit: int = None) -> Tuple[bool, Dict[str, int]]:
        """
        레이트 제한 확인

        Args:
            key: 식별자 (API 키, 사용자 ID 등)
            limit: 요청 제한 (None이면 기본값 사용)

        Returns:
            (허용 여부, 제한 정보)
        """
        limit = limit or self.default_limit

        if self.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._check_fixed_window(key, limit)
        elif self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(key, limit)
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(key, limit)

        return True, {"limit": limit, "remaining": limit, "reset": 0}

    def _check_fixed_window(self, key: str, limit: int) -> Tuple[bool, Dict[str, int]]:
        """고정 시간 창 제한"""
        now = datetime.utcnow()

        if key not in self.windows:
            self.windows[key] = now
            self.request_history[key] = []
            count = 0
            window_start = now
        else:
            window_start = self.windows[key]
            window_end = window_start + timedelta(seconds=self.window_seconds)

            if now > window_end:
                # 새로운 시간 창
                self.windows[key] = now
                self.request_history[key] = []
                count = 0
            else:
                count = len(self.request_history[key])

        allowed = count < limit
        if allowed:
            self.request_history[key].append(now)
            count += 1

        window_end = self.windows[key] + timedelta(seconds=self.window_seconds)
        reset_in = int((window_end - now).total_seconds())

        return allowed, {
            "limit": limit,
            "used": count,
            "remaining": max(0, limit - count),
            "reset_in_seconds": reset_in
        }

    def _check_sliding_window(self, key: str, limit: int) -> Tuple[bool, Dict[str, int]]:
        """슬라이딩 시간 창 제한"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # 시간 창 벗어난 요청 제거
        self.request_history[key] = [
            req_time for req_time in self.request_history[key]
            if req_time > window_start
        ]

        count = len(self.request_history[key])
        allowed = count < limit

        if allowed:
            self.request_history[key].append(now)
            count += 1

        # 최초 요청 시간 기반 reset 시간 계산
        if self.request_history[key]:
            oldest_request = min(self.request_history[key])
            reset_time = oldest_request + timedelta(seconds=self.window_seconds)
            reset_in = int((reset_time - now).total_seconds())
        else:
            reset_in = 0

        return allowed, {
            "limit": limit,
            "used": count,
            "remaining": max(0, limit - count),
            "reset_in_seconds": reset_in
        }

    def _check_token_bucket(self, key: str, limit: int) -> Tuple[bool, Dict[str, int]]:
        """토큰 버킷 제한"""
        now = datetime.utcnow()

        if key not in self.tokens:
            self.tokens[key] = float(limit)
            self.windows[key] = now
        else:
            # 경과 시간에 따른 토큰 보충
            elapsed = (now - self.windows[key]).total_seconds()
            tokens_to_add = (elapsed / self.window_seconds) * limit
            self.tokens[key] = min(limit, self.tokens[key] + tokens_to_add)
            self.windows[key] = now

        allowed = self.tokens[key] >= 1

        if allowed:
            self.tokens[key] -= 1

        return allowed, {
            "limit": limit,
            "used": int(limit - self.tokens[key]),
            "remaining": max(0, int(self.tokens[key])),
            "reset_in_seconds": self.window_seconds
        }

    def reset_key(self, key: str):
        """특정 키 초기화"""
        if key in self.request_history:
            del self.request_history[key]
        if key in self.tokens:
            del self.tokens[key]
        if key in self.windows:
            del self.windows[key]


# ============================================================================
# 데모: CORS 및 레이트 제한
# ============================================================================

def demo_cors_and_ratelimit():
    """CORS 및 레이트 제한 데모"""
    print("=" * 80)
    print("CORS 및 레이트 제한 시스템 데모")
    print("=" * 80)

    # CORS 정책 테스트
    print("\n[1단계] CORS 정책 테스트")
    print("-" * 80)

    # 개발 환경 CORS
    print("\n개발 환경 CORS 정책:")
    dev_cors = CORSPolicies.development()
    headers = dev_cors.get_response_headers("http://localhost:3000")
    print(f"✓ 오리진 확인: {dev_cors.is_origin_allowed('http://localhost:3000')}")
    for key, value in headers.items():
        print(f"  • {key}: {value}")

    # 프로덕션 환경 CORS
    print("\n프로덕션 환경 CORS 정책:")
    prod_cors = CORSPolicies.production()
    allowed = prod_cors.is_origin_allowed("https://app.example.com")
    print(f"✓ app.example.com 허용: {allowed}")
    allowed = prod_cors.is_origin_allowed("https://malicious.com")
    print(f"✓ malicious.com 허용: {allowed}")

    # 공개 API CORS
    print("\n공개 API CORS 정책:")
    public_cors = CORSPolicies.public_api()
    headers = public_cors.get_response_headers("https://any-origin.com")
    print(f"✓ 허용 메서드: {headers.get('Access-Control-Allow-Methods')}")
    print(f"✓ 자격 증명: {headers.get('Access-Control-Allow-Credentials', 'false')}")

    # 고정 시간 창 레이트 제한
    print("\n[2단계] 고정 시간 창 레이트 제한")
    print("-" * 80)

    limiter = AdvancedRateLimiter(
        strategy=RateLimitStrategy.FIXED_WINDOW,
        default_limit=5,
        window_seconds=60
    )

    print("✓ 제한: 5개/60초")
    for i in range(7):
        allowed, info = limiter.check_rate_limit("user_001")
        status = "✓ 허용" if allowed else "✗ 거부"
        print(f"  요청 {i+1}: {status} | 사용: {info['used']}/{info['limit']} | 남은 시간: {info['reset_in_seconds']}초")

    # 슬라이딩 시간 창 레이트 제한
    print("\n[3단계] 슬라이딩 시간 창 레이트 제한")
    print("-" * 80)

    limiter = AdvancedRateLimiter(
        strategy=RateLimitStrategy.SLIDING_WINDOW,
        default_limit=5,
        window_seconds=60
    )

    print("✓ 제한: 5개/60초 (슬라이딩)")
    for i in range(7):
        allowed, info = limiter.check_rate_limit("user_002")
        status = "✓ 허용" if allowed else "✗ 거부"
        print(f"  요청 {i+1}: {status} | 사용: {info['used']}/{info['limit']} | 남은 시간: {info['reset_in_seconds']}초")

    # 토큰 버킷 레이트 제한
    print("\n[4단계] 토큰 버킷 레이트 제한")
    print("-" * 80)

    limiter = AdvancedRateLimiter(
        strategy=RateLimitStrategy.TOKEN_BUCKET,
        default_limit=5,
        window_seconds=60
    )

    print("✓ 제한: 5개/60초 (토큰 버킷)")
    for i in range(7):
        allowed, info = limiter.check_rate_limit("user_003")
        status = "✓ 허용" if allowed else "✗ 거부"
        print(f"  요청 {i+1}: {status} | 사용: {info['used']}/{info['limit']} | 남은: {info['remaining']}")

    # 다중 사용자 제한
    print("\n[5단계] 다중 사용자 제한")
    print("-" * 80)

    limiter = AdvancedRateLimiter(
        strategy=RateLimitStrategy.FIXED_WINDOW,
        default_limit=3,
        window_seconds=60
    )

    print("✓ 사용자별 제한 (3개/60초):")
    for user_id in ["user_A", "user_B", "user_C"]:
        for j in range(4):
            allowed, info = limiter.check_rate_limit(user_id)
            if j < 3:
                status = "✓" if allowed else "✗"
                print(f"  {user_id} 요청 {j+1}: {status} (남은: {info['remaining']})")
            else:
                status = "✓" if allowed else "✗"
                print(f"  {user_id} 요청 {j+1}: {status} (초과)")

    # 사용자 정의 CORS 정책
    print("\n[6단계] 사용자 정의 CORS 정책")
    print("-" * 80)

    custom_cors = CORSPolicy(
        allowed_origins=["https://trusted.com", "https://partner.com"],
        allowed_methods=["GET", "POST"],
        allowed_headers=["Content-Type", "Authorization"],
        max_age=7200
    )

    print("✓ 신뢰할 수 있는 오리진:")
    for origin in ["https://trusted.com", "https://untrusted.com"]:
        allowed = custom_cors.is_origin_allowed(origin)
        status = "✓ 허용" if allowed else "✗ 거부"
        print(f"  {origin}: {status}")

    print("\n" + "=" * 80)
    print("CORS 및 레이트 제한 시스템 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_cors_and_ratelimit()
