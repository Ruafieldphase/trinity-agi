#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 키 관리 시스템 - 프로덕션 레벨 키 관리

이 모듈은 API 키의 생성, 관리, 검증을 제공합니다.
"""

import sys
import io
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from enum import Enum

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# API 키 열거형
# ============================================================================

class APIKeyStatus(Enum):
    """API 키 상태"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class APIKeyType(Enum):
    """API 키 타입"""
    SECRET = "secret"      # 비밀 키
    PUBLIC = "public"      # 공개 키


# ============================================================================
# API 키 데이터 모델
# ============================================================================

class APIKey:
    """API 키"""

    def __init__(
        self,
        key_id: str,
        user_id: str,
        key_type: APIKeyType,
        key_hash: str,
        name: str = "",
        scopes: List[str] = None,
        rate_limit: int = 1000,
        last_used: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None
    ):
        """초기화"""
        self.key_id = key_id
        self.user_id = user_id
        self.key_type = key_type
        self.key_hash = key_hash
        self.name = name or f"API Key {key_id[:8]}"
        self.scopes = scopes or ["default"]
        self.rate_limit = rate_limit
        self.last_used = last_used
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at
        self.status = APIKeyStatus.ACTIVE
        self.usage_count = 0
        self.failed_attempts = 0

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def is_active(self) -> bool:
        """활성 여부 확인"""
        if self.is_expired():
            self.status = APIKeyStatus.EXPIRED
            return False
        return self.status == APIKeyStatus.ACTIVE

    def has_scope(self, scope: str) -> bool:
        """특정 스코프 보유 여부"""
        return scope in self.scopes or "default" in self.scopes

    def record_usage(self):
        """사용 기록"""
        self.last_used = datetime.utcnow()
        self.usage_count += 1
        self.failed_attempts = 0  # 성공하면 실패 횟수 초기화

    def record_failure(self):
        """실패 기록"""
        self.failed_attempts += 1

    def __repr__(self):
        return f"<APIKey {self.key_id} - {self.status.value}>"


# ============================================================================
# API 키 관리자
# ============================================================================

class APIKeyManager:
    """API 키 관리"""

    def __init__(self, key_expiration_days: int = 365):
        """
        초기화

        Args:
            key_expiration_days: 키 만료 기본값 (일 단위)
        """
        self.keys: Dict[str, APIKey] = {}
        self.key_expiration_days = key_expiration_days
        self.key_prefix = "sk_"  # 비밀 키 접두사
        self.public_key_prefix = "pk_"  # 공개 키 접두사

    def generate_key(self) -> str:
        """보안 키 생성"""
        return secrets.token_urlsafe(32)

    def hash_key(self, key: str) -> str:
        """키 해싱 (저장용)"""
        return hashlib.sha256(key.encode()).hexdigest()

    def create_key(
        self,
        user_id: str,
        name: str = "",
        scopes: List[str] = None,
        rate_limit: int = 1000,
        expiration_days: int = None,
        key_type: APIKeyType = APIKeyType.SECRET
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        API 키 생성

        Args:
            user_id: 사용자 ID
            name: 키 이름
            scopes: 허용 스코프 목록
            rate_limit: 분당 요청 제한
            expiration_days: 만료 일수
            key_type: 키 타입

        Returns:
            (생성 성공 여부, 키 문자열 또는 None, 에러 메시지 또는 None)
        """
        try:
            # 키 생성
            raw_key = self.generate_key()

            # 키 ID 생성
            key_id = f"{self.key_prefix if key_type == APIKeyType.SECRET else self.public_key_prefix}{secrets.token_hex(8)}"

            # 키 해싱
            key_hash = self.hash_key(raw_key)

            # 만료 시간 계산
            expiration_days = expiration_days or self.key_expiration_days
            expires_at = datetime.utcnow() + timedelta(days=expiration_days)

            # API 키 객체 생성
            api_key = APIKey(
                key_id=key_id,
                user_id=user_id,
                key_type=key_type,
                key_hash=key_hash,
                name=name,
                scopes=scopes,
                rate_limit=rate_limit,
                expires_at=expires_at
            )

            # 저장
            self.keys[key_id] = api_key

            # 실제 키만 반환 (저장되지 않음)
            full_key = f"{key_id}.{raw_key}"

            return True, full_key, None

        except Exception as e:
            return False, None, f"키 생성 오류: {str(e)}"

    def verify_key(self, full_key: str) -> Tuple[bool, Optional[APIKey], Optional[str]]:
        """
        API 키 검증

        Args:
            full_key: 완전한 키 (key_id.raw_key 형식)

        Returns:
            (검증 성공 여부, APIKey 객체 또는 None, 에러 메시지 또는 None)
        """
        try:
            # 키 파싱
            parts = full_key.split(".")
            if len(parts) != 2:
                return False, None, "유효하지 않은 키 형식입니다."

            key_id, raw_key = parts

            # 키 ID로 조회
            api_key = self.keys.get(key_id)
            if not api_key:
                return False, None, "키를 찾을 수 없습니다."

            # 만료 확인
            if api_key.is_expired():
                api_key.status = APIKeyStatus.EXPIRED
                return False, None, "키가 만료되었습니다."

            # 활성 상태 확인
            if not api_key.is_active():
                return False, None, f"키가 {api_key.status.value} 상태입니다."

            # 키 해시 검증
            key_hash = self.hash_key(raw_key)
            if key_hash != api_key.key_hash:
                api_key.record_failure()
                return False, None, "유효하지 않은 키입니다."

            # 사용 기록
            api_key.record_usage()

            return True, api_key, None

        except Exception as e:
            return False, None, f"키 검증 오류: {str(e)}"

    def get_key(self, key_id: str) -> Optional[APIKey]:
        """키 조회"""
        return self.keys.get(key_id)

    def list_keys_for_user(self, user_id: str) -> List[APIKey]:
        """사용자의 모든 키 조회"""
        return [key for key in self.keys.values() if key.user_id == user_id]

    def revoke_key(self, key_id: str) -> Tuple[bool, str]:
        """
        키 취소

        Args:
            key_id: 키 ID

        Returns:
            (취소 성공 여부, 메시지)
        """
        api_key = self.keys.get(key_id)

        if not api_key:
            return False, "키를 찾을 수 없습니다."

        api_key.status = APIKeyStatus.REVOKED
        return True, f"키 {key_id}이 취소되었습니다."

    def suspend_key(self, key_id: str) -> Tuple[bool, str]:
        """
        키 중지

        Args:
            key_id: 키 ID

        Returns:
            (중지 성공 여부, 메시지)
        """
        api_key = self.keys.get(key_id)

        if not api_key:
            return False, "키를 찾을 수 없습니다."

        api_key.status = APIKeyStatus.SUSPENDED
        return True, f"키 {key_id}이 중지되었습니다."

    def reactivate_key(self, key_id: str) -> Tuple[bool, str]:
        """
        키 재활성화

        Args:
            key_id: 키 ID

        Returns:
            (재활성화 성공 여부, 메시지)
        """
        api_key = self.keys.get(key_id)

        if not api_key:
            return False, "키를 찾을 수 없습니다."

        api_key.status = APIKeyStatus.ACTIVE
        return True, f"키 {key_id}이 재활성화되었습니다."

    def get_key_statistics(self, key_id: str) -> Optional[Dict]:
        """키 통계 조회"""
        api_key = self.keys.get(key_id)

        if not api_key:
            return None

        return {
            "key_id": key_id,
            "name": api_key.name,
            "status": api_key.status.value,
            "type": api_key.key_type.value,
            "created_at": api_key.created_at.isoformat(),
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
            "usage_count": api_key.usage_count,
            "failed_attempts": api_key.failed_attempts,
            "rate_limit": api_key.rate_limit,
            "scopes": api_key.scopes,
            "is_expired": api_key.is_expired(),
            "days_until_expiration": (api_key.expires_at - datetime.utcnow()).days if api_key.expires_at else None
        }


# ============================================================================
# 레이트 제한
# ============================================================================

class RateLimiter:
    """API 요청 레이트 제한"""

    def __init__(self):
        """초기화"""
        self.request_history: Dict[str, List[datetime]] = {}

    def check_rate_limit(self, api_key_id: str, limit: int, window_seconds: int = 60) -> Tuple[bool, int]:
        """
        레이트 제한 확인

        Args:
            api_key_id: API 키 ID
            limit: 제한 요청 수
            window_seconds: 시간 창 (초)

        Returns:
            (제한 내 여부, 남은 요청 수)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        if api_key_id not in self.request_history:
            self.request_history[api_key_id] = []

        # 시간 창 벗어난 요청 제거
        self.request_history[api_key_id] = [
            req_time for req_time in self.request_history[api_key_id]
            if req_time > window_start
        ]

        # 현재 요청 기록
        current_count = len(self.request_history[api_key_id])

        if current_count >= limit:
            return False, 0

        self.request_history[api_key_id].append(now)
        remaining = limit - current_count - 1

        return True, remaining

    def reset_key_history(self, api_key_id: str):
        """특정 키의 히스토리 초기화"""
        if api_key_id in self.request_history:
            del self.request_history[api_key_id]


# ============================================================================
# 데모: API 키 관리
# ============================================================================

def demo_api_key_management():
    """API 키 관리 데모"""
    print("=" * 80)
    print("API 키 관리 시스템 데모")
    print("=" * 80)

    # API 키 관리자 초기화
    print("\n[1단계] API 키 관리자 초기화")
    print("-" * 80)

    key_manager = APIKeyManager(key_expiration_days=365)
    print("✓ API 키 관리자 초기화 완료")

    # API 키 생성
    print("\n[2단계] API 키 생성")
    print("-" * 80)

    success, secret_key, error = key_manager.create_key(
        user_id="user_001",
        name="Production API Key",
        scopes=["workflow:read", "workflow:create"],
        rate_limit=1000,
        key_type=APIKeyType.SECRET
    )

    if success:
        print(f"✓ 비밀 키 생성 완료")
        print(f"✓ 키: {secret_key[:50]}...")
    else:
        print(f"✗ 오류: {error}")

    success, public_key, error = key_manager.create_key(
        user_id="user_001",
        name="Public API Key",
        scopes=["workflow:read"],
        rate_limit=100,
        key_type=APIKeyType.PUBLIC
    )

    if success:
        print(f"✓ 공개 키 생성 완료")
        print(f"✓ 키: {public_key[:50]}...")
    else:
        print(f"✗ 오류: {error}")

    # API 키 검증
    print("\n[3단계] API 키 검증")
    print("-" * 80)

    success, api_key, error = key_manager.verify_key(secret_key)
    print(f"{'✓' if success else '✗'} 검증 결과: {success}")
    if success:
        print(f"  • 키 ID: {api_key.key_id}")
        print(f"  • 키 이름: {api_key.name}")
        print(f"  • 상태: {api_key.status.value}")
        print(f"  • 스코프: {', '.join(api_key.scopes)}")
        print(f"  • 사용 횟수: {api_key.usage_count}")
    else:
        print(f"  • 오류: {error}")

    # 잘못된 키 검증
    print("\n[4단계] 잘못된 키 검증")
    print("-" * 80)

    success, api_key, error = key_manager.verify_key("invalid.key")
    print(f"{'✓' if success else '✗'} 검증 결과: {success}")
    print(f"  • 오류: {error}")

    # 사용자별 키 조회
    print("\n[5단계] 사용자별 키 조회")
    print("-" * 80)

    user_keys = key_manager.list_keys_for_user("user_001")
    print(f"✓ User 001의 키 ({len(user_keys)}개):")
    for key in user_keys:
        print(f"  • {key.key_id}: {key.name} ({key.status.value})")

    # 키 통계
    print("\n[6단계] 키 통계")
    print("-" * 80)

    stats = key_manager.get_key_statistics(user_keys[0].key_id)
    if stats:
        print(f"✓ {stats['name']} 통계:")
        print(f"  • 상태: {stats['status']}")
        print(f"  • 생성일: {stats['created_at']}")
        print(f"  • 만료일: {stats['expires_at']}")
        print(f"  • 마지막 사용: {stats['last_used']}")
        print(f"  • 사용 횟수: {stats['usage_count']}")
        print(f"  • 실패 횟수: {stats['failed_attempts']}")
        print(f"  • 만료 여부: {stats['is_expired']}")

    # 키 관리 작업
    print("\n[7단계] 키 관리 작업")
    print("-" * 80)

    # 키 중지
    key_id = user_keys[0].key_id
    success, msg = key_manager.suspend_key(key_id)
    print(f"{'✓' if success else '✗'} {msg}")

    # 중지된 키로 검증 시도
    success, api_key, error = key_manager.verify_key(secret_key)
    print(f"{'✓' if success else '✗'} 중지된 키 검증: {not success}")
    if error:
        print(f"  • 오류: {error}")

    # 키 재활성화
    success, msg = key_manager.reactivate_key(key_id)
    print(f"{'✓' if success else '✗'} {msg}")

    # 레이트 제한 테스트
    print("\n[8단계] 레이트 제한 테스트")
    print("-" * 80)

    rate_limiter = RateLimiter()
    key_id = "test_key"
    limit = 5

    print(f"✓ 요청 제한: {limit}개/60초")
    for i in range(7):
        allowed, remaining = rate_limiter.check_rate_limit(key_id, limit)
        status = "✓ 허용" if allowed else "✗ 거부"
        print(f"  요청 {i+1}: {status} (남은 요청: {remaining})")

    print("\n" + "=" * 80)
    print("API 키 관리 시스템 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_api_key_management()
