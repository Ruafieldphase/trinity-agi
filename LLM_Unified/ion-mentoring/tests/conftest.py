"""
Pytest 공유 설정 및 Fixtures

이 파일은 모든 테스트에서 공유할 수 있는 fixtures와 설정을 정의합니다.
테스트 실행 시 자동으로 로드됩니다.
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

# ion-mentoring 디렉토리 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 테스트 환경 설정
os.environ["ENVIRONMENT"] = "test"
os.environ["CONFIG_PATH"] = "config/test.yaml"
os.environ["DEBUG"] = "false"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["PHASE4_ENABLED"] = "false"
os.environ.setdefault("ION_USE_IN_MEMORY_REDIS", "true")
os.environ.setdefault("ION_ALLOW_IN_MEMORY_REDIS_FALLBACK", "1")

# ============================================================================
# FastAPI 테스트 클라이언트
# ============================================================================


@pytest.fixture(scope="session")
def app():
    """FastAPI 애플리케이션 인스턴스"""
    from app.main import app

    return app


class AutoUserIdTestClient(TestClient):
    """Test client that injects a default user_id for /chat requests when missing."""

    def post(self, url: str, *args, **kwargs):
        json_payload = kwargs.get("json")
        if isinstance(json_payload, dict) and "user_id" not in json_payload and url.startswith("/chat"):
            payload_copy = dict(json_payload)
            payload_copy["user_id"] = "test-user"
            kwargs["json"] = payload_copy
        return super().post(url, *args, **kwargs)


@pytest.fixture
def client(app):
    """FastAPI TestClient"""
    return AutoUserIdTestClient(app)


@pytest.fixture
async def async_client(app):
    """비동기 HTTP 클라이언트 (AsyncClient)"""
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================================
# Mock 객체 및 응답
# ============================================================================


@pytest.fixture
def mock_pipeline_response():
    """Mock PersonaResponse - 표준 응답"""
    from persona_pipeline import PersonaResponse

    return PersonaResponse(
        content="🌊 테스트 응답입니다!",
        persona_used="Lua",
        resonance_key="curious-flowing-inquiry",
        confidence=0.85,
        metadata={
            "rhythm": {"pace": "flowing", "avg_length": 4.2, "punctuation_density": 0.08},
            "tone": {"primary": "curious", "confidence": 0.8, "secondary": None},
            "routing": {"secondary_persona": "Elro", "reasoning": "호기심 기반 질문"},
        },
    )


@pytest.fixture
def mock_elro_response():
    """Mock PersonaResponse - Elro (논리적)"""
    from persona_pipeline import PersonaResponse

    return PersonaResponse(
        content="📐 논리적으로 분석해볼게요.",
        persona_used="Elro",
        resonance_key="analytical-flowing-statement",
        confidence=0.9,
        metadata={
            "rhythm": {"pace": "measured", "avg_length": 5.1, "punctuation_density": 0.05},
            "tone": {"primary": "analytical", "confidence": 0.9, "secondary": None},
            "routing": {"secondary_persona": "Riri", "reasoning": "데이터 기반 분석"},
        },
    )


@pytest.fixture
def mock_riri_response():
    """Mock PersonaResponse - Riri (분석적)"""
    from persona_pipeline import PersonaResponse

    return PersonaResponse(
        content="📊 균형잡힌 관점에서 봐보겠습니다.",
        persona_used="Riri",
        resonance_key="balanced-steady-analysis",
        confidence=0.88,
        metadata={
            "rhythm": {"pace": "steady", "avg_length": 4.8, "punctuation_density": 0.06},
            "tone": {"primary": "balanced", "confidence": 0.88, "secondary": "analytical"},
            "routing": {"secondary_persona": "Nana", "reasoning": "조율적 접근"},
        },
    )


@pytest.fixture
def mock_nana_response():
    """Mock PersonaResponse - Nana (조율적)"""
    from persona_pipeline import PersonaResponse

    return PersonaResponse(
        content="🎵 종합적으로 조율해드리겠습니다.",
        persona_used="Nana",
        resonance_key="orchestrative-flowing-synthesis",
        confidence=0.82,
        metadata={
            "rhythm": {"pace": "flowing", "avg_length": 4.5, "punctuation_density": 0.1},
            "tone": {"primary": "orchestrative", "confidence": 0.82, "secondary": None},
            "routing": {"secondary_persona": "Lua", "reasoning": "공감적 조율"},
        },
    )


@pytest.fixture
def mock_fallback_response():
    """Mock PersonaResponse - Fallback 응답 (에러 시)"""
    from persona_pipeline import PersonaResponse

    return PersonaResponse(
        content="죄송합니다. 일시적인 문제가 발생했습니다.",
        persona_used="Nana",
        resonance_key="urgent-burst-expressive",
        confidence=0.0,
        metadata={
            "error": "Backend failure",
            "fallback": True,
            "original_message": "Unknown error occurred",
        },
    )


# ============================================================================
# Mock 백엔드 클라이언트
# ============================================================================


@pytest.fixture
def mock_vertex_client():
    """Mock VertexAIConnector"""
    mock = MagicMock()
    mock.send_prompt = MagicMock(return_value="Mock AI response")
    mock.is_available = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_pipeline(mock_pipeline_response):
    """Mock PersonaPipeline"""
    mock = MagicMock()
    mock.process = MagicMock(return_value=mock_pipeline_response)
    mock.vertex_client = MagicMock()
    return mock


# ============================================================================
# 테스트 데이터
# ============================================================================


@pytest.fixture
def test_messages():
    """테스트 메시지 컬렉션"""
    return {
        "normal": "안녕하세요! 이것이 정상 메시지입니다.",
        "emotional": "정말 답답해요! 이게 왜 안 되는 거죠?",
        "analytical": "이 데이터를 분석해주실 수 있나요?",
        "long": "테스트 메시지 " * 50,  # ~700자
        "empty": "",
        "whitespace": "   ",
        "special_chars": "!@#$%^&*()_+-=[]{}|;':,./<>?`~",
        "emoji": "🌊 이 이모지는 어떻게 처리되나요?",
        "mixed_lang": "Hello 안녕 こんにちは Привет",
    }


@pytest.fixture
def test_chat_requests():
    """테스트 채팅 요청 컬렉션"""
    return {
        "valid": {"message": "안녕하세요!"},
        "empty": {"message": ""},
        "whitespace": {"message": "   "},
        "long": {"message": "테스트 메시지 " * 50},
        "missing_field": {"text": "잘못된 필드"},
        "invalid_type": {"message": 12345},
        "null_message": {"message": None},
        "special_chars": {"message": "!@#$%^&*()_+-=[]{}|;':,./<>?`~"},
    }


# ============================================================================
# 테스트 설정
# ============================================================================


@pytest.fixture(autouse=True)
def reset_environment():
    """각 테스트 전 환경 초기화"""
    # 테스트 환경 설정
    os.environ["ENVIRONMENT"] = "test"
    yield
    # 테스트 후 정리 (필요시)
    pass


@pytest.fixture
def mock_config():
    """Mock 설정 객체"""
    config = MagicMock()
    config.environment = "test"
    config.app_name = "테스트 앱"
    config.app_version = "0.1.0"
    config.debug = False
    config.log_level = "WARNING"
    config.rate_limit_enabled = False
    config.cors_origins = ["http://localhost:3000"]
    return config


# ============================================================================
# 유틸리티 Fixtures
# ============================================================================


@pytest.fixture
def mock_sleep(monkeypatch):
    """asyncio.sleep을 즉시 반환하도록 Mock"""

    async def instant_sleep(seconds):
        pass

    monkeypatch.setattr(asyncio, "sleep", instant_sleep)


@pytest.fixture
def capture_logs(caplog):
    """로그 캡처"""
    import logging

    caplog.set_level(logging.DEBUG)
    return caplog


# ============================================================================
# Pytest 마커 정의
# ============================================================================


def pytest_configure(config):
    """Pytest 마커 등록"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "asyncio: Async tests")


# ============================================================================
# 테스트 레포트 Hooks
# ============================================================================


def pytest_collection_modifyitems(config, items):
    """테스트 마커 자동 적용"""
    for item in items:
        # 파일 이름 기반으로 자동 마커 추가
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        else:
            item.add_marker(pytest.mark.unit)

        # async 테스트 감지
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# ============================================================================
# E2E 테스트용 추가 Fixtures
# ============================================================================


@pytest.fixture
def e2e_persona_messages():
    """E2E 테스트용 페르소나별 메시지 모음"""
    return {
        "lua": {
            "emotional": "정말 답답해요!",
            "frustrated": "이게 정말 싫어요!",
            "anxious": "불안해서 어떻게 할 줄 모르겠어요",
        },
        "elro": {
            "technical": "이 함수의 시간 복잡도는?",
            "curious": "이게 어떻게 작동하나요?",
            "analytical": "기술적으로 분석해주세요",
        },
        "riri": {
            "data": "데이터를 분석해주세요",
            "metrics": "이 메트릭을 비교해주세요",
            "balanced": "균형 잡힌 관점에서 봐주세요",
        },
        "nana": {
            "urgent": "급히 조율해야 해요!",
            "coordination": "프로젝트 일정을 조율해주세요",
            "synthesis": "여러 의견을 종합해주세요",
        },
    }


@pytest.fixture
def e2e_test_scenarios():
    """E2E 테스트 시나리오 모음"""
    return [
        {
            "name": "Happy Path - Emotional Support",
            "input": "정말 답답해요! 이 문제를 어떻게 해결하죠?",
            "expected_persona": "Lua",
            "category": "happy_path",
        },
        {
            "name": "Happy Path - Technical Query",
            "input": "이 함수의 시간 복잡도를 어떻게 분석하나요?",
            "expected_personas": ["Elro", "Riri"],
            "category": "happy_path",
        },
        {
            "name": "Validation - Empty Message",
            "input": "",
            "expected_status": 400,
            "category": "validation",
        },
        {
            "name": "Validation - Too Long",
            "input": "A" * 1001,
            "expected_status": 400,
            "category": "validation",
        },
        {
            "name": "Edge Case - Single Character",
            "input": "A",
            "expected_status": 200,
            "category": "edge_case",
        },
    ]


@pytest.fixture
def e2e_performance_config():
    """E2E 성능 테스트 설정"""
    return {
        "response_time_p95": 2.0,  # 초 (P95 < 2초)
        "response_time_p99": 5.0,  # 초 (P99 < 5초)
        "health_check_max": 0.5,  # 초
        "concurrent_users": 10,  # 동시 사용자
        "requests_per_minute": 10,  # 분당 요청 수
        "error_rate_threshold": 0.01,  # 1% 이상
    }


@pytest.fixture
def rate_limit_tester():
    """속도 제한 테스트 유틸리티"""

    class RateLimitTester:
        def __init__(self):
            self.request_times = []
            self.success_count = 0
            self.rate_limited_count = 0

        def record_success(self, timestamp):
            self.success_count += 1
            self.request_times.append(timestamp)

        def record_rate_limit(self, timestamp):
            self.rate_limited_count += 1

        def get_stats(self):
            return {
                "success": self.success_count,
                "rate_limited": self.rate_limited_count,
                "total": self.success_count + self.rate_limited_count,
            }

    return RateLimitTester()


# ============================================================================
# 테스트 재시도 설정 (실패한 테스트 자동 재시도)
# ============================================================================


@pytest.fixture(scope="session", autouse=True)
def setup_test_session():
    """테스트 세션 시작 시 실행"""
    print("\n" + "=" * 70)
    print("ION Mentoring 테스트 세션 시작")
    print("=" * 70 + "\n")
    yield
    print("\n" + "=" * 70)
    print("ION Mentoring 테스트 세션 종료")
    print("=" * 70 + "\n")
