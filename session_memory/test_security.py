#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
보안 시스템 테스트 - JWT, API 키, CORS, 레이트 제한

이 모듈은 전체 보안 시스템을 테스트합니다.
"""

import sys
import io
import unittest

from security_jwt_auth import (
    JWTManager, UserManager, UserRole, Permission,
    ROLE_PERMISSIONS, SecurityUtils, require_auth, require_permission
)
from security_api_keys import (
    APIKeyManager, APIKey, APIKeyStatus, APIKeyType, RateLimiter
)
from security_cors_ratelimit import (
    CORSPolicy, CORSPolicies, AdvancedRateLimiter,
    RateLimitStrategy
)

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# JWT 인증 테스트
# ============================================================================

class TestJWTAuth(unittest.TestCase):
    """JWT 인증 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.jwt_manager = JWTManager(secret_key="test_secret_key_12345678")
        self.user_manager = UserManager()

    def test_user_authentication(self):
        """사용자 인증 테스트"""
        success, user, msg = self.user_manager.authenticate("admin", "admin123")
        self.assertTrue(success)
        self.assertEqual(user.username, "admin")
        self.assertEqual(user.role, UserRole.ADMIN)

    def test_user_authentication_failed(self):
        """사용자 인증 실패 테스트"""
        success, user, msg = self.user_manager.authenticate("admin", "wrong_password")
        self.assertFalse(success)

    def test_token_creation(self):
        """토큰 생성 테스트"""
        token = self.jwt_manager.create_token(
            user_id="user_001",
            username="admin",
            role=UserRole.ADMIN
        )
        self.assertIsNotNone(token)
        self.assertIn(".", token)

    def test_token_verification(self):
        """토큰 검증 테스트"""
        token = self.jwt_manager.create_token(
            user_id="user_001",
            username="admin",
            role=UserRole.ADMIN
        )

        success, payload, error = self.jwt_manager.verify_token(token)
        self.assertTrue(success)
        self.assertEqual(payload["user_id"], "user_001")
        self.assertEqual(payload["username"], "admin")

    def test_token_refresh(self):
        """토큰 갱신 테스트"""
        token = self.jwt_manager.create_token(
            user_id="user_001",
            username="admin",
            role=UserRole.ADMIN
        )

        success, new_token, error = self.jwt_manager.refresh_token(token)
        self.assertTrue(success)
        self.assertIsNotNone(new_token)
        self.assertNotEqual(token, new_token)

    def test_password_strength(self):
        """비밀번호 강도 테스트"""
        weak_pwd = "weak"
        strong_pwd = "Strong@123"

        is_weak, msg = SecurityUtils.is_password_strong(weak_pwd)
        self.assertFalse(is_weak)

        is_strong, msg = SecurityUtils.is_password_strong(strong_pwd)
        self.assertTrue(is_strong)

    def test_user_permissions(self):
        """사용자 권한 테스트"""
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        self.assertIn(Permission.WORKFLOW_CREATE, admin_perms)
        self.assertIn(Permission.CONFIG_WRITE, admin_perms)

        viewer_perms = ROLE_PERMISSIONS[UserRole.VIEWER]
        self.assertIn(Permission.WORKFLOW_READ, viewer_perms)
        self.assertNotIn(Permission.WORKFLOW_DELETE, viewer_perms)

    def test_create_user(self):
        """사용자 생성 테스트"""
        success, user, msg = self.user_manager.create_user(
            "user_100",
            "testuser",
            "TestPassword@123",
            UserRole.OPERATOR
        )

        self.assertTrue(success)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, UserRole.OPERATOR)


# ============================================================================
# API 키 테스트
# ============================================================================

class TestAPIKeys(unittest.TestCase):
    """API 키 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.key_manager = APIKeyManager()

    def test_api_key_creation(self):
        """API 키 생성 테스트"""
        success, key, error = self.key_manager.create_key(
            user_id="user_001",
            name="Test Key",
            scopes=["workflow:read"],
            key_type=APIKeyType.SECRET
        )

        self.assertTrue(success)
        self.assertIsNotNone(key)
        self.assertIn(".", key)

    def test_api_key_verification(self):
        """API 키 검증 테스트"""
        success, key, error = self.key_manager.create_key(
            user_id="user_001",
            name="Test Key"
        )

        success, api_key, error = self.key_manager.verify_key(key)
        self.assertTrue(success)
        self.assertEqual(api_key.name, "Test Key")

    def test_api_key_invalid_verification(self):
        """유효하지 않은 API 키 검증 테스트"""
        success, api_key, error = self.key_manager.verify_key("invalid.key")
        self.assertFalse(success)

    def test_api_key_revoke(self):
        """API 키 취소 테스트"""
        success, key, error = self.key_manager.create_key(
            user_id="user_001",
            name="Test Key"
        )

        key_id = key.split(".")[0]
        success, msg = self.key_manager.revoke_key(key_id)
        self.assertTrue(success)

        success, api_key, error = self.key_manager.verify_key(key)
        self.assertFalse(success)

    def test_api_key_suspend_and_reactivate(self):
        """API 키 중지 및 재활성화 테스트"""
        success, key, error = self.key_manager.create_key(
            user_id="user_001",
            name="Test Key"
        )

        key_id = key.split(".")[0]

        # 중지
        success, msg = self.key_manager.suspend_key(key_id)
        self.assertTrue(success)

        # 검증 실패
        success, api_key, error = self.key_manager.verify_key(key)
        self.assertFalse(success)

        # 재활성화
        success, msg = self.key_manager.reactivate_key(key_id)
        self.assertTrue(success)

        # 검증 성공
        success, api_key, error = self.key_manager.verify_key(key)
        self.assertTrue(success)

    def test_api_key_statistics(self):
        """API 키 통계 테스트"""
        success, key, error = self.key_manager.create_key(
            user_id="user_001",
            name="Stats Test Key"
        )

        # 키 검증하여 사용 기록
        self.key_manager.verify_key(key)

        key_id = key.split(".")[0]
        stats = self.key_manager.get_key_statistics(key_id)

        self.assertIsNotNone(stats)
        self.assertEqual(stats["usage_count"], 1)
        self.assertFalse(stats["is_expired"])


# ============================================================================
# CORS 및 레이트 제한 테스트
# ============================================================================

class TestCORSAndRateLimit(unittest.TestCase):
    """CORS 및 레이트 제한 테스트"""

    def test_cors_policy_development(self):
        """개발 환경 CORS 정책 테스트"""
        cors = CORSPolicies.development()
        self.assertTrue(cors.is_origin_allowed("http://localhost:3000"))
        self.assertTrue(cors.is_origin_allowed("http://any-origin.com"))

    def test_cors_policy_production(self):
        """프로덕션 환경 CORS 정책 테스트"""
        cors = CORSPolicies.production()
        self.assertTrue(cors.is_origin_allowed("https://app.example.com"))
        self.assertFalse(cors.is_origin_allowed("https://malicious.com"))

    def test_cors_policy_public_api(self):
        """공개 API CORS 정책 테스트"""
        cors = CORSPolicies.public_api()
        self.assertTrue(cors.is_origin_allowed("https://any-origin.com"))
        self.assertFalse(cors.allow_credentials)

    def test_cors_headers(self):
        """CORS 헤더 생성 테스트"""
        cors = CORSPolicy(allowed_origins=["https://trusted.com"])
        headers = cors.get_response_headers("https://trusted.com")

        self.assertEqual(headers["Access-Control-Allow-Origin"], "https://trusted.com")
        self.assertIn("GET", headers["Access-Control-Allow-Methods"])

    def test_fixed_window_rate_limit(self):
        """고정 시간 창 레이트 제한 테스트"""
        limiter = AdvancedRateLimiter(
            strategy=RateLimitStrategy.FIXED_WINDOW,
            default_limit=3,
            window_seconds=60
        )

        # 제한 내 요청
        allowed, info = limiter.check_rate_limit("user_001")
        self.assertTrue(allowed)

        # 두 번째 요청
        allowed, info = limiter.check_rate_limit("user_001")
        self.assertTrue(allowed)

        # 세 번째 요청
        allowed, info = limiter.check_rate_limit("user_001")
        self.assertTrue(allowed)

        # 네 번째 요청 - 제한 초과
        allowed, info = limiter.check_rate_limit("user_001")
        self.assertFalse(allowed)

    def test_sliding_window_rate_limit(self):
        """슬라이딩 시간 창 레이트 제한 테스트"""
        limiter = AdvancedRateLimiter(
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            default_limit=2,
            window_seconds=60
        )

        # 첫 두 요청
        allowed1, _ = limiter.check_rate_limit("user_002")
        allowed2, _ = limiter.check_rate_limit("user_002")

        self.assertTrue(allowed1)
        self.assertTrue(allowed2)

        # 세 번째 요청 - 제한 초과
        allowed3, _ = limiter.check_rate_limit("user_002")
        self.assertFalse(allowed3)

    def test_token_bucket_rate_limit(self):
        """토큰 버킷 레이트 제한 테스트"""
        limiter = AdvancedRateLimiter(
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            default_limit=3,
            window_seconds=60
        )

        # 요청
        for i in range(4):
            allowed, info = limiter.check_rate_limit("user_003")
            if i < 3:
                self.assertTrue(allowed)
            else:
                self.assertFalse(allowed)

    def test_multiple_users_rate_limit(self):
        """다중 사용자 레이트 제한 테스트"""
        limiter = AdvancedRateLimiter(
            strategy=RateLimitStrategy.FIXED_WINDOW,
            default_limit=2,
            window_seconds=60
        )

        # 사용자별 독립적 제한
        allowed_user1_1, _ = limiter.check_rate_limit("user_A")
        allowed_user1_2, _ = limiter.check_rate_limit("user_A")
        allowed_user1_3, _ = limiter.check_rate_limit("user_A")

        allowed_user2_1, _ = limiter.check_rate_limit("user_B")
        allowed_user2_2, _ = limiter.check_rate_limit("user_B")

        self.assertTrue(allowed_user1_1)
        self.assertTrue(allowed_user1_2)
        self.assertFalse(allowed_user1_3)  # User A 제한 초과

        self.assertTrue(allowed_user2_1)
        self.assertTrue(allowed_user2_2)  # User B는 독립적 제한


# ============================================================================
# 종합 보안 테스트
# ============================================================================

class TestSecurityIntegration(unittest.TestCase):
    """종합 보안 테스트"""

    def test_complete_authentication_flow(self):
        """완전한 인증 흐름 테스트"""
        # 1. 사용자 인증
        user_manager = UserManager()
        success, user, msg = user_manager.authenticate("admin", "admin123")
        self.assertTrue(success)

        # 2. JWT 토큰 생성
        jwt_manager = JWTManager()
        token = jwt_manager.create_token(
            user_id=user.user_id,
            username=user.username,
            role=user.role
        )
        self.assertIsNotNone(token)

        # 3. 토큰 검증
        success, payload, error = jwt_manager.verify_token(token)
        self.assertTrue(success)

        # 4. 권한 확인
        role = UserRole(payload["role"])
        permissions = ROLE_PERMISSIONS[role]
        self.assertIn(Permission.WORKFLOW_CREATE, permissions)

    def test_api_key_with_cors(self):
        """API 키와 CORS 통합 테스트"""
        # 1. API 키 생성
        key_manager = APIKeyManager()
        success, key, error = key_manager.create_key(
            user_id="user_001",
            name="Integration Test",
            scopes=["workflow:read"]
        )
        self.assertTrue(success)

        # 2. API 키 검증
        success, api_key, error = key_manager.verify_key(key)
        self.assertTrue(success)

        # 3. CORS 정책 확인
        cors = CORSPolicies.production()
        self.assertTrue(cors.is_origin_allowed("https://app.example.com"))

    def test_api_key_with_rate_limit(self):
        """API 키와 레이트 제한 통합 테스트"""
        # 1. API 키 생성
        key_manager = APIKeyManager()
        success, key, error = key_manager.create_key(
            user_id="user_001",
            name="Rate Limited Key",
            rate_limit=100
        )
        self.assertTrue(success)

        # 2. API 키 검증
        success, api_key, error = key_manager.verify_key(key)
        self.assertTrue(success)

        # 3. 레이트 제한 적용
        limiter = AdvancedRateLimiter(default_limit=api_key.rate_limit)
        key_id = key.split(".")[0]

        for i in range(102):
            allowed, info = limiter.check_rate_limit(key_id)
            if i < 100:
                self.assertTrue(allowed)
            else:
                self.assertFalse(allowed)


# ============================================================================
# 테스트 실행
# ============================================================================

def run_tests():
    """테스트 실행"""
    print("=" * 80)
    print("보안 시스템 테스트")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestJWTAuth))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIKeys))
    suite.addTests(loader.loadTestsFromTestCase(TestCORSAndRateLimit))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityIntegration))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 결과 요약
    print("\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)
    print(f"실행: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    print(f"성공률: {(result.testsRun - len(result.failures) - len(result.errors))/result.testsRun*100:.1f}%")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
