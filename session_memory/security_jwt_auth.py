#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
보안 시스템 - JWT 인증 및 권한 관리

이 모듈은 Agent System의 JWT 기반 인증 시스템을 제공합니다.
"""

import sys
import io
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List, Tuple
from enum import Enum
from functools import wraps

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 보안 관련 열거형
# ============================================================================

class UserRole(Enum):
    """사용자 역할"""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(Enum):
    """권한"""
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    AGENT_READ = "agent:read"
    AGENT_MANAGE = "agent:manage"
    METRICS_READ = "metrics:read"
    HEALTH_READ = "health:read"
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"


# ============================================================================
# 역할별 권한 정의
# ============================================================================

ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.WORKFLOW_CREATE,
        Permission.WORKFLOW_READ,
        Permission.WORKFLOW_UPDATE,
        Permission.WORKFLOW_DELETE,
        Permission.AGENT_READ,
        Permission.AGENT_MANAGE,
        Permission.METRICS_READ,
        Permission.HEALTH_READ,
        Permission.CONFIG_READ,
        Permission.CONFIG_WRITE,
    ],
    UserRole.OPERATOR: [
        Permission.WORKFLOW_CREATE,
        Permission.WORKFLOW_READ,
        Permission.WORKFLOW_UPDATE,
        Permission.AGENT_READ,
        Permission.METRICS_READ,
        Permission.HEALTH_READ,
    ],
    UserRole.VIEWER: [
        Permission.WORKFLOW_READ,
        Permission.AGENT_READ,
        Permission.METRICS_READ,
        Permission.HEALTH_READ,
    ],
    UserRole.GUEST: [
        Permission.METRICS_READ,
    ]
}


# ============================================================================
# JWT 토큰 관리자
# ============================================================================

class JWTManager:
    """JWT 토큰 생성 및 검증"""

    def __init__(self, secret_key: str = None, algorithm: str = "HS256", expiration_hours: int = 24):
        """
        초기화

        Args:
            secret_key: JWT 서명 키
            algorithm: JWT 알고리즘 (기본: HS256)
            expiration_hours: 토큰 만료 시간 (시간 단위)
        """
        self.secret_key = secret_key or self._generate_secret_key()
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours

    @staticmethod
    def _generate_secret_key() -> str:
        """보안 비밀 키 생성"""
        return secrets.token_urlsafe(32)

    def create_token(
        self,
        user_id: str,
        username: str,
        role: UserRole,
        additional_claims: Dict = None,
        expiration_hours: int = None
    ) -> str:
        """
        JWT 토큰 생성

        Args:
            user_id: 사용자 ID
            username: 사용자 이름
            role: 사용자 역할
            additional_claims: 추가 클레임
            expiration_hours: 토큰 만료 시간

        Returns:
            JWT 토큰 문자열
        """
        expiration_hours = expiration_hours or self.expiration_hours

        payload = {
            "user_id": user_id,
            "username": username,
            "role": role.value,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=expiration_hours),
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        JWT 토큰 검증

        Args:
            token: JWT 토큰 문자열

        Returns:
            (검증 성공 여부, 클레임 딕셔너리 또는 None, 에러 메시지 또는 None)
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return True, payload, None
        except jwt.ExpiredSignatureError:
            return False, None, "토큰이 만료되었습니다."
        except jwt.InvalidTokenError as e:
            return False, None, f"유효하지 않은 토큰입니다: {str(e)}"
        except Exception as e:
            return False, None, f"토큰 검증 오류: {str(e)}"

    def refresh_token(self, token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        JWT 토큰 갱신

        Args:
            token: 기존 JWT 토큰

        Returns:
            (갱신 성공 여부, 새 토큰 또는 None, 에러 메시지 또는 None)
        """
        success, payload, error = self.verify_token(token)

        if not success:
            return False, None, error

        # 만료된 토큰도 클레임 추출 시도
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            new_token = self.create_token(
                user_id=payload["user_id"],
                username=payload["username"],
                role=UserRole(payload["role"])
            )
            return True, new_token, None
        except Exception as e:
            return False, None, f"토큰 갱신 오류: {str(e)}"

    def decode_token_unsafe(self, token: str) -> Optional[Dict]:
        """
        검증 없이 토큰 디코드 (개발용)

        Args:
            token: JWT 토큰

        Returns:
            클레임 딕셔너리 또는 None
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None


# ============================================================================
# 사용자 관리자
# ============================================================================

class User:
    """사용자 정보"""

    def __init__(self, user_id: str, username: str, password_hash: str, role: UserRole, active: bool = True):
        """초기화"""
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.active = active
        self.created_at = datetime.utcnow()
        self.last_login = None

    def verify_password(self, password: str) -> bool:
        """비밀번호 검증"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.password_hash

    def get_permissions(self) -> List[Permission]:
        """사용자 권한 조회"""
        return ROLE_PERMISSIONS.get(self.role, [])

    def has_permission(self, permission: Permission) -> bool:
        """특정 권한 보유 여부 확인"""
        return permission in self.get_permissions()

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"


class UserManager:
    """사용자 관리"""

    def __init__(self):
        """초기화"""
        self.users: Dict[str, User] = {}
        self._initialize_default_users()

    def _initialize_default_users(self):
        """기본 사용자 초기화"""
        # 기본 사용자들 생성 (테스트용)
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        self.users["admin"] = User("user_001", "admin", admin_hash, UserRole.ADMIN)

        operator_hash = hashlib.sha256("operator123".encode()).hexdigest()
        self.users["operator"] = User("user_002", "operator", operator_hash, UserRole.OPERATOR)

        viewer_hash = hashlib.sha256("viewer123".encode()).hexdigest()
        self.users["viewer"] = User("user_003", "viewer", viewer_hash, UserRole.VIEWER)

    def create_user(self, user_id: str, username: str, password: str, role: UserRole) -> Tuple[bool, Optional[User], str]:
        """
        사용자 생성

        Args:
            user_id: 사용자 ID
            username: 사용자 이름
            password: 비밀번호
            role: 사용자 역할

        Returns:
            (생성 성공 여부, User 객체 또는 None, 메시지)
        """
        if username in self.users:
            return False, None, "이미 존재하는 사용자입니다."

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = User(user_id, username, password_hash, role)
        self.users[username] = user

        return True, user, f"사용자 {username} 생성 완료"

    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[User], str]:
        """
        사용자 인증

        Args:
            username: 사용자 이름
            password: 비밀번호

        Returns:
            (인증 성공 여부, User 객체 또는 None, 메시지)
        """
        user = self.users.get(username)

        if not user:
            return False, None, "사용자를 찾을 수 없습니다."

        if not user.active:
            return False, None, "비활성화된 사용자입니다."

        if not user.verify_password(password):
            return False, None, "비밀번호가 틀렸습니다."

        user.last_login = datetime.utcnow()
        return True, user, "인증 성공"

    def get_user(self, username: str) -> Optional[User]:
        """사용자 조회"""
        return self.users.get(username)

    def update_user_role(self, username: str, new_role: UserRole) -> Tuple[bool, str]:
        """사용자 역할 변경"""
        user = self.users.get(username)

        if not user:
            return False, "사용자를 찾을 수 없습니다."

        user.role = new_role
        return True, f"사용자 {username}의 역할을 {new_role.value}로 변경했습니다."

    def deactivate_user(self, username: str) -> Tuple[bool, str]:
        """사용자 비활성화"""
        user = self.users.get(username)

        if not user:
            return False, "사용자를 찾을 수 없습니다."

        user.active = False
        return True, f"사용자 {username}을 비활성화했습니다."


# ============================================================================
# 인증 데코레이터
# ============================================================================

def require_auth(jwt_manager: JWTManager):
    """
    인증 필요 데코레이터

    Args:
        jwt_manager: JWTManager 인스턴스

    Returns:
        데코레이터 함수
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, token: str = None, **kwargs):
            if not token:
                return {
                    "success": False,
                    "error": "토큰이 필요합니다."
                }

            success, payload, error = jwt_manager.verify_token(token)

            if not success:
                return {
                    "success": False,
                    "error": error
                }

            # 토큰 정보를 kwargs에 추가
            kwargs["token_payload"] = payload

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(required_permission: Permission):
    """
    권한 필요 데코레이터

    Args:
        required_permission: 필요한 권한

    Returns:
        데코레이터 함수
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, token_payload: Dict = None, **kwargs):
            if not token_payload:
                return {
                    "success": False,
                    "error": "토큰 정보가 없습니다."
                }

            user_role = UserRole(token_payload.get("role"))
            permissions = ROLE_PERMISSIONS.get(user_role, [])

            if required_permission not in permissions:
                return {
                    "success": False,
                    "error": f"권한이 없습니다: {required_permission.value}"
                }

            return func(*args, token_payload=token_payload, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# 보안 유틸리티
# ============================================================================

class SecurityUtils:
    """보안 유틸리티"""

    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호 해싱"""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """비밀번호 검증"""
        return SecurityUtils.hash_password(password) == password_hash

    @staticmethod
    def generate_api_key() -> str:
        """API 키 생성"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def is_password_strong(password: str) -> Tuple[bool, str]:
        """비밀번호 강도 확인"""
        if len(password) < 8:
            return False, "비밀번호는 최소 8자 이상이어야 합니다."

        if not any(c.isupper() for c in password):
            return False, "비밀번호에 대문자가 필요합니다."

        if not any(c.isdigit() for c in password):
            return False, "비밀번호에 숫자가 필요합니다."

        if not any(c in "!@#$%^&*" for c in password):
            return False, "비밀번호에 특수문자(!@#$%^&*)가 필요합니다."

        return True, "비밀번호 강도 양호"


# ============================================================================
# 데모: JWT 인증 시스템
# ============================================================================

def demo_jwt_auth():
    """JWT 인증 시스템 데모"""
    print("=" * 80)
    print("JWT 인증 시스템 데모")
    print("=" * 80)

    # JWT 관리자 초기화
    print("\n[1단계] JWT 관리자 초기화")
    print("-" * 80)

    jwt_manager = JWTManager()
    print(f"✓ JWT 관리자 초기화 완료")
    print(f"✓ 비밀 키: {jwt_manager.secret_key[:20]}...")
    print(f"✓ 알고리즘: {jwt_manager.algorithm}")
    print(f"✓ 토큰 만료: {jwt_manager.expiration_hours}시간")

    # 사용자 관리자 초기화
    print("\n[2단계] 사용자 관리자 초기화")
    print("-" * 80)

    user_manager = UserManager()
    print(f"✓ 기본 사용자 생성:")
    print(f"  • admin (관리자)")
    print(f"  • operator (운영자)")
    print(f"  • viewer (뷰어)")

    # 사용자 인증
    print("\n[3단계] 사용자 인증")
    print("-" * 80)

    success, user, msg = user_manager.authenticate("admin", "admin123")
    print(f"{'✓' if success else '✗'} {msg}")
    if success:
        print(f"  • 사용자: {user.username}")
        print(f"  • 역할: {user.role.value}")
        print(f"  • 마지막 로그인: {user.last_login}")

    # 토큰 생성
    print("\n[4단계] JWT 토큰 생성")
    print("-" * 80)

    token = jwt_manager.create_token(
        user_id=user.user_id,
        username=user.username,
        role=user.role
    )
    print(f"✓ 토큰 생성 완료")
    print(f"✓ 토큰: {token[:50]}...")

    # 토큰 검증
    print("\n[5단계] JWT 토큰 검증")
    print("-" * 80)

    success, payload, error = jwt_manager.verify_token(token)
    print(f"{'✓' if success else '✗'} 검증: {success}")
    if payload:
        print(f"  • 사용자 ID: {payload['user_id']}")
        print(f"  • 사용자 이름: {payload['username']}")
        print(f"  • 역할: {payload['role']}")
        print(f"  • 발급 시간: {payload['iat']}")
        print(f"  • 만료 시간: {payload['exp']}")

    # 권한 확인
    print("\n[6단계] 사용자 권한 확인")
    print("-" * 80)

    permissions = user.get_permissions()
    print(f"✓ Admin 사용자의 권한 ({len(permissions)}개):")
    for perm in permissions:
        print(f"  • {perm.value}")

    # 다른 역할의 권한 확인
    print("\n✓ Viewer 사용자의 권한:")
    viewer_permissions = ROLE_PERMISSIONS[UserRole.VIEWER]
    for perm in viewer_permissions:
        print(f"  • {perm.value}")

    # 토큰 갱신
    print("\n[7단계] JWT 토큰 갱신")
    print("-" * 80)

    success, new_token, error = jwt_manager.refresh_token(token)
    print(f"{'✓' if success else '✗'} 갱신: {success}")
    if new_token:
        print(f"✓ 새 토큰: {new_token[:50]}...")

    # 비밀번호 강도 확인
    print("\n[8단계] 비밀번호 강도 확인")
    print("-" * 80)

    test_passwords = [
        "weak",
        "WeakPassword",
        "Weak123",
        "Strong@123",
        "SuperStrong@456"
    ]

    for pwd in test_passwords:
        strong, msg = SecurityUtils.is_password_strong(pwd)
        status = "✓ 강함" if strong else "✗ 약함"
        print(f"{status}: {pwd:20} - {msg}")

    # API 키 생성
    print("\n[9단계] API 키 생성")
    print("-" * 80)

    api_key = SecurityUtils.generate_api_key()
    print(f"✓ API 키: {api_key[:40]}...")

    # 사용자 관리 작업
    print("\n[10단계] 사용자 관리 작업")
    print("-" * 80)

    # 새 사용자 생성
    success, new_user, msg = user_manager.create_user(
        "user_004",
        "newuser",
        "NewUser@123",
        UserRole.OPERATOR
    )
    print(f"{'✓' if success else '✗'} {msg}")

    # 사용자 역할 변경
    success, msg = user_manager.update_user_role("viewer", UserRole.OPERATOR)
    print(f"{'✓' if success else '✗'} {msg}")

    # 사용자 비활성화
    success, msg = user_manager.deactivate_user("viewer")
    print(f"{'✓' if success else '✗'} {msg}")

    # 비활성화된 사용자 인증 시도
    success, user, msg = user_manager.authenticate("viewer", "viewer123")
    print(f"{'✓' if success else '✗'} 비활성 사용자 인증: {msg}")

    print("\n" + "=" * 80)
    print("JWT 인증 시스템 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_jwt_auth()
