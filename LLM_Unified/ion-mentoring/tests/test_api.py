"""
FastAPI 엔드포인트 테스트

Week 3 Day 1: REST API 테스트
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# ion-mentoring 디렉토리 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
from persona_pipeline import PersonaResponse

# === Fixtures ===


@pytest.fixture
def client():
    """TestClient 생성"""
    return TestClient(app)


@pytest.fixture
def mock_pipeline_response():
    """Mock PersonaResponse"""
    return PersonaResponse(
        content="🌊 테스트 응답입니다!",
        persona_used="Lua",
        resonance_key="curious-flowing-inquiry",
        confidence=0.85,
        metadata={
            "rhythm": {"pace": "flowing", "avg_length": 4.2, "punctuation_density": 0.08},
            "tone": {"primary": "curious", "confidence": 0.8, "secondary": None},
            "routing": {
                "secondary_persona": "Elro",
                "reasoning": "tone=curious pace=flowing intent=inquiry → Lua 선택",
            },
            "phase": {
                "phase_index": 0,
                "phase_label": "Attune",
                "guidance": "Acknowledge the user's curiosity and provide a clear overview.",
                "bqi": {"beauty": 0.71, "quality": 0.82, "impact": 0.64},
                "timestamp": 1697539100.0,
            },
            "rune": {
                "overall_quality": 0.81,
                "regenerate": False,
                "feedback": "- 응답이 사용자의 질문 의도를 충실히 반영하고 있습니다.",
                "transparency": {
                    "impact": 0.81,
                    "confidence": 0.5,
                    "risks": [],
                    "source": "heuristic",
                },
            },
        },
    )


# === Phase 1: 기본 엔드포인트 테스트 (3개) ===


def test_root_endpoint(client):
    """
    Test 1: 루트 경로 접근

    GET / 엔드포인트가 정상적으로 응답하는지 확인
    """
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "내다AI Ion API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "running"
    assert "/docs" in data["docs"]


def test_health_check_endpoint(client):
    """
    Test 2: 헬스체크 엔드포인트

    GET /health가 정상적으로 응답하고 pipeline_ready를 확인
    """
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["version"] == "1.0.0"
    assert "pipeline_ready" in data
    assert isinstance(data["pipeline_ready"], bool)


def test_docs_endpoint_accessible(client):
    """
    Test 3: Swagger UI 접근

    GET /docs가 접근 가능한지 확인 (HTML 반환)
    """
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


# === Phase 2: 채팅 엔드포인트 테스트 (5개) ===


@patch("app.main.pipeline")
def test_chat_endpoint_success(mock_pipeline, client, mock_pipeline_response):
    """
    Test 4: 정상 채팅 요청

    POST /chat에 정상 메시지를 보내면 PersonaResponse가 반환됨
    """
    # Mock 설정
    mock_pipeline.process.return_value = mock_pipeline_response

    # 요청
    response = client.post("/chat", json={"message": "이거 어떻게 하는 거예요?", "user_id": "test-user"})

    assert response.status_code == 200

    data = response.json()
    assert data["content"] == "🌊 테스트 응답입니다!"
    assert data["persona_used"] == "Lua"
    assert data["resonance_key"] == "curious-flowing-inquiry"
    assert data["confidence"] == 0.85
    assert "metadata" in data
    assert "rhythm" in data["metadata"]
    assert "tone" in data["metadata"]

    # pipeline.process가 호출되었는지 확인
    mock_pipeline.process.assert_called_once()


@patch("app.main.pipeline")
def test_chat_endpoint_different_personas(mock_pipeline, client):
    """
    Test 5: 다양한 페르소나 라우팅

    다른 입력에 대해 다른 페르소나가 반환되는지 확인
    """
    # Elro 응답 Mock
    elro_response = PersonaResponse(
        content="📐 논리적으로 분석해볼게요.",
        persona_used="Elro",
        resonance_key="analytical-flowing-statement",
        confidence=0.9,
        metadata={},
    )
    mock_pipeline.process.return_value = elro_response

    response = client.post("/chat", json={"message": "이 문제를 분석해주세요", "user_id": "test-user"})

    assert response.status_code == 200
    data = response.json()
    assert data["persona_used"] == "Elro"
    assert data["confidence"] == 0.9


def test_chat_endpoint_empty_message(client):
    """
    Test 6: 빈 메시지 에러

    빈 문자열 또는 공백만 있는 메시지는 400 에러
    """
    # 빈 문자열
    response = client.post("/chat", json={"message": "", "user_id": "test-user"})
    assert response.status_code == 422  # Pydantic validation error

    # 공백만
    response = client.post("/chat", json={"message": "   ", "user_id": "test-user"})
    assert response.status_code == 422


def test_chat_endpoint_long_message(client):
    """
    Test 7: 긴 메시지 처리

    1000자 이내의 긴 메시지도 정상 처리
    """
    long_message = "테스트 메시지 " * 50  # ~700자

    with patch("app.main.pipeline") as mock_pipeline:
        mock_pipeline.process.return_value = PersonaResponse(
            content="응답입니다",
            persona_used="Nana",
            resonance_key="calm-flowing-statement",
            confidence=0.7,
            metadata={},
        )

        response = client.post("/chat", json={"message": long_message, "user_id": "test-user"})

        assert response.status_code == 200


@patch("app.main.pipeline")
def test_chat_endpoint_vertex_failure_fallback(mock_pipeline, client):
    """
    Test 8: Vertex AI 장애 시 폴백

    Vertex AI 에러 시 Nana 폴백 응답 (confidence=0.0)
    """
    # Nana 폴백 응답 (에러 메타데이터 포함)
    fallback_response = PersonaResponse(
        content="죄송합니다. 일시적인 문제가 발생했습니다.",
        persona_used="Nana",
        resonance_key="urgent-burst-expressive",
        confidence=0.0,
        metadata={"error": "Vertex AI connection failed", "fallback": True},
    )
    mock_pipeline.process.return_value = fallback_response

    response = client.post("/chat", json={"message": "안녕하세요", "user_id": "test-user"})

    assert response.status_code == 200
    data = response.json()
    assert data["persona_used"] == "Nana"
    assert data["confidence"] == 0.0
    assert "error" in data["metadata"]


# === Phase 3: 에러 핸들링 테스트 (2개) ===


def test_invalid_request_format(client):
    """
    Test 9: 잘못된 요청 형식

    message 필드가 없거나 타입이 잘못된 경우 422 에러
    """
    # message 필드 누락
    response = client.post("/chat", json={"text": "잘못된 필드", "user_id": "test-user"})
    assert response.status_code == 422

    # message가 문자열이 아님
    response = client.post("/chat", json={"message": 12345, "user_id": "test-user"})
    assert response.status_code == 422


@patch("app.main.pipeline")
def test_internal_server_error(mock_pipeline, client):
    """
    Test 10: 내부 서버 에러

    예상치 못한 에러 발생 시 500 에러 반환
    """
    # pipeline.process에서 예외 발생
    mock_pipeline.process.side_effect = Exception("Unexpected error")

    response = client.post("/chat", json={"message": "테스트", "user_id": "test-user"})

    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["status_code"] == 500


# === Phase 4: Response 스키마 검증 (2개) ===


@patch("app.main.pipeline")
def test_response_schema_completeness(mock_pipeline, client, mock_pipeline_response):
    """
    Test 11: 응답 스키마 완전성

    모든 필수 필드가 포함되어 있는지 확인
    """
    mock_pipeline.process.return_value = mock_pipeline_response

    response = client.post("/chat", json={"message": "테스트", "user_id": "test-user"})

    assert response.status_code == 200
    data = response.json()

    # 필수 필드 확인
    required_fields = ["content", "persona_used", "resonance_key", "confidence", "metadata"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # 타입 확인
    assert isinstance(data["content"], str)
    assert isinstance(data["persona_used"], str)
    assert isinstance(data["resonance_key"], str)
    assert isinstance(data["confidence"], float)
    assert isinstance(data["metadata"], dict)

    # confidence 범위 확인
    assert 0.0 <= data["confidence"] <= 1.0


@patch("app.main.pipeline")
def test_metadata_structure(mock_pipeline, client, mock_pipeline_response):
    """
    Test 12: 메타데이터 구조 검증

    metadata에 rhythm, tone, routing, phase, rune 정보가 포함되는지 확인
    """
    mock_pipeline.process.return_value = mock_pipeline_response

    response = client.post("/chat", json={"message": "테스트", "user_id": "test-user"})

    assert response.status_code == 200
    data = response.json()

    metadata = data["metadata"]

    # rhythm 정보
    assert "rhythm" in metadata
    assert "pace" in metadata["rhythm"]
    assert "avg_length" in metadata["rhythm"]

    # tone 정보
    assert "tone" in metadata
    assert "primary" in metadata["tone"]
    assert "confidence" in metadata["tone"]

    # routing 정보
    assert "routing" in metadata
    assert "secondary_persona" in metadata["routing"]

    # phase 정보
    assert "phase" in metadata
    assert "phase_label" in metadata["phase"]
    assert "bqi" in metadata["phase"]
    assert "quality" in metadata["phase"]["bqi"]

    # rune 정보
    assert "rune" in metadata
    assert "overall_quality" in metadata["rune"]
    assert "regenerate" in metadata["rune"]


@patch("app.main.generate_summary_background", new_callable=AsyncMock)
def test_chat_end_triggers_background(mock_generate_summary, client):
    from app import main as app_main

    app_main.summaries_cache.clear()

    response = client.post("/chat/end", params={"session_id": "session-123"})

    assert response.status_code == 200
    mock_generate_summary.assert_awaited_once_with("session-123")
    assert app_main.summaries_cache["session-123"]["status"] == "generating"


def test_chat_end_skip_summary(client):
    from app import main as app_main

    app_main.summaries_cache.clear()

    response = client.post(
        "/chat/end", params={"session_id": "session-skip", "skip_summary": "true"}
    )

    assert response.status_code == 200
    assert response.json()["summary"] is None
    assert "session-skip" not in app_main.summaries_cache


def test_get_summary_states(client):
    from app import main as app_main

    session_id = "session-state"
    app_main.summaries_cache[session_id] = {"status": "generating"}

    generating = client.get(f"/summaries/{session_id}")
    assert generating.status_code == 200
    assert generating.json()["status"] == "generating"

    app_main.summaries_cache[session_id] = {"status": "failed", "error": "timeout"}
    failed = client.get(f"/summaries/{session_id}")
    assert failed.json()["status"] == "failed"
    assert failed.json()["error"] == "timeout"

    app_main.summaries_cache[session_id] = {
        "status": "completed",
        "summary": "요약 완료",
        "generated_at": "2025-01-01T00:00:00",
    }
    completed = client.get(f"/summaries/{session_id}")
    assert completed.json()["status"] == "completed"
    assert completed.json()["summary"] == "요약 완료"
    assert completed.json()["generated_at"] == "2025-01-01T00:00:00"


if __name__ == "__main__":
    # 개별 실행 테스트
    pytest.main([__file__, "-v", "--tb=short"])
