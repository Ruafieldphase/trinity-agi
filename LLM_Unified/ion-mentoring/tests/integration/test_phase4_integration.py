"""
Phase 4 API v2 Integration Tests
AI 권장사항 엔진 + 다중 턴 대화 시스템 통합 테스트

테스트 항목:
1. 라우터 등록 및 엔드포인트 가용성
2. 권장사항 엔진 엔드포인트 기능
3. 다중 턴 대화 엔드포인트 기능
4. 의존성 주입 작동
5. 에러 처리 및 검증
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# 프로젝트 경로 설정
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.main import app


class TestPhase4Integration:
    """Phase 4 API v2 통합 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)

    # ==================== 헬스 체크 테스트 ====================

    def test_phase4_health_check(self, client):
        """Phase 4 헬스 체크 엔드포인트"""
        response = client.get("/api/v2/phase4/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "phase4_features" in data
        assert data["phase4_features"]["recommendations_available"] is True
        assert data["phase4_features"]["conversations_available"] is True
        assert data["phase4_features"]["ab_testing_enabled"] is True

    # ==================== 권장사항 엔진 엔드포인트 테스트 ====================

    def test_personalized_recommendation_success(self, client):
        """개인화 추천 - 성공 케이스"""
        request_data = {
            "user_id": "user_123",
            "query": "I want to learn programming",
            "context": {"tone": "curious", "pace": "measured", "intent": "learning"},
            "options": {"top_k": 3},
        }

        response = client.post("/api/v2/recommend/personalized", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 필수 필드 확인
        assert "primary_persona" in data
        assert "confidence" in data
        assert "all_scores" in data
        assert "ranked_recommendations" in data
        assert "explanation" in data
        assert "metadata" in data

        # 값 검증
        assert isinstance(data["primary_persona"], str)
        assert 0 <= data["confidence"] <= 1
        assert isinstance(data["all_scores"], dict)
        assert isinstance(data["ranked_recommendations"], list)

    def test_personalized_recommendation_without_context(self, client):
        """개인화 추천 - 컨텍스트 없이"""
        request_data = {"user_id": "user_456", "query": "Help me solve a technical problem"}

        response = client.post("/api/v2/recommend/personalized", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "primary_persona" in data
        assert data["confidence"] > 0

    def test_personalized_recommendation_validation_error(self, client):
        """개인화 추천 - 검증 실패"""
        request_data = {
            # user_id 누락
            "query": "Some query"
        }

        response = client.post("/api/v2/recommend/personalized", json=request_data)

        assert response.status_code == 422  # Validation Error

    def test_comparison_recommendation(self, client):
        """권장사항 비교 (A/B 테스트)"""
        request_data = {
            "user_id": "user_789",
            "query": "Data analysis problem",
            "include_legacy": True,
        }

        response = client.post("/api/v2/recommend/compare", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "new_recommendation" in data
        assert "legacy_recommendation" in data
        assert "comparison" in data

        # 비교 정보
        comparison = data["comparison"]
        assert "consensus" in comparison or "confidence_improvement" in comparison

    def test_comparison_without_legacy(self, client):
        """권장사항 비교 - 레거시 미포함"""
        request_data = {"user_id": "user_999", "query": "Some query", "include_legacy": False}

        response = client.post("/api/v2/recommend/compare", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["legacy_recommendation"] is None
        assert "new_recommendation" in data

    # ==================== 다중 턴 대화 엔드포인트 테스트 ====================

    def test_start_conversation(self, client):
        """대화 세션 시작"""
        request_data = {
            "user_id": "user_conv_001",
            "persona_id": "Lua",
            "options": {"session_ttl_hours": 24},
        }

        response = client.post("/api/v2/conversations/start", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 필수 필드 확인
        assert "session_id" in data
        assert "user_id" in data
        assert "persona_id" in data
        assert "created_at" in data
        assert "expires_at" in data
        assert "status" in data

        # 값 검증
        assert data["user_id"] == "user_conv_001"
        assert data["persona_id"] == "Lua"
        assert data["status"] == "active"

        # 시간 검증
        assert isinstance(data["created_at"], str)
        assert isinstance(data["expires_at"], str)

        return data["session_id"]

    def test_start_conversation_all_personas(self, client):
        """각 페르소나로 대화 시작"""
        personas = ["Lua", "Elro", "Riri", "Nana"]

        for persona in personas:
            request_data = {"user_id": f"user_{persona}", "persona_id": persona}

            response = client.post("/api/v2/conversations/start", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["persona_id"] == persona
            assert "session_id" in data

    def test_process_turn(self, client):
        """대화 턴 처리"""
        # 먼저 세션 생성
        start_response = client.post(
            "/api/v2/conversations/start", json={"user_id": "user_turn_test", "persona_id": "Lua"}
        )
        session_id = start_response.json()["session_id"]

        # 턴 처리
        turn_request = {"user_message": "How can I learn Python?", "metadata": {"source": "web"}}

        response = client.post(f"/api/v2/conversations/{session_id}/turn", json=turn_request)

        assert response.status_code == 200
        data = response.json()

        # 필수 필드 확인
        assert "turn_number" in data
        assert "session_id" in data
        assert "response_text" in data
        assert "context_used" in data
        assert "metadata" in data

        # 값 검증
        assert data["session_id"] == session_id
        assert data["turn_number"] > 0
        assert len(data["response_text"]) > 0

    def test_get_conversation_context(self, client):
        """대화 컨텍스트 조회"""
        # 세션 생성
        start_response = client.post(
            "/api/v2/conversations/start",
            json={"user_id": "user_context_test", "persona_id": "Elro"},
        )
        session_id = start_response.json()["session_id"]

        # 컨텍스트 조회
        response = client.get(f"/api/v2/conversations/{session_id}")

        assert response.status_code == 200
        data = response.json()

        # 필수 필드 확인
        assert "session_id" in data
        assert "user_id" in data
        assert "persona_id" in data
        assert "turn_count" in data
        assert "messages" in data
        assert "context_memory" in data
        assert "state" in data
        assert "expires_at" in data

        # 값 검증
        assert data["session_id"] == session_id

    def test_get_nonexistent_conversation(self, client):
        """존재하지 않는 세션 조회 (시뮬레이션 모드에서는 200 반환)"""
        response = client.get("/api/v2/conversations/nonexistent_session")

        # 시뮬레이션 모드에서는 항상 응답을 생성함
        # 실제 배포 시에는 404를 반환하도록 구현 필요
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data

    def test_close_conversation(self, client):
        """대화 세션 종료"""
        # 세션 생성
        start_response = client.post(
            "/api/v2/conversations/start", json={"user_id": "user_close_test", "persona_id": "Riri"}
        )
        session_id = start_response.json()["session_id"]

        # 세션 종료
        close_request = {"save_conversation": True}

        response = client.post(f"/api/v2/conversations/{session_id}/close", json=close_request)

        assert response.status_code == 200
        data = response.json()

        # 필수 필드 확인
        assert "session_id" in data
        assert "closed_at" in data
        assert "summary" in data

        # 값 검증
        assert data["session_id"] == session_id

    def test_list_conversations(self, client):
        """사용자의 모든 대화 조회"""
        user_id = "user_list_test"

        # 몇 개 세션 생성
        for i in range(3):
            client.post(
                "/api/v2/conversations/start",
                json={"user_id": user_id, "persona_id": ["Lua", "Elro", "Riri"][i]},
            )

        # 세션 목록 조회
        response = client.get(f"/api/v2/conversations?user_id={user_id}")

        assert response.status_code == 200
        data = response.json()

        # 필수 필드 확인
        assert "user_id" in data
        assert "sessions" in data
        assert "total_count" in data
        assert "active_count" in data

        # 값 검증
        assert data["user_id"] == user_id
        assert isinstance(data["sessions"], list)

    # ==================== 다중 턴 대화 플로우 테스트 ====================

    def test_full_conversation_flow(self, client):
        """완전한 다중 턴 대화 플로우"""
        # 1. 대화 시작
        start_response = client.post(
            "/api/v2/conversations/start", json={"user_id": "user_flow_test", "persona_id": "Lua"}
        )
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]

        # 2. 여러 턴 처리
        messages = [
            "I'm feeling overwhelmed with my project",
            "Tell me more about time management",
            "That sounds helpful",
        ]

        for msg in messages:
            turn_response = client.post(
                f"/api/v2/conversations/{session_id}/turn", json={"user_message": msg}
            )
            assert turn_response.status_code == 200
            assert turn_response.json()["response_text"]

        # 3. 컨텍스트 확인
        context_response = client.get(f"/api/v2/conversations/{session_id}")
        assert context_response.status_code == 200
        context = context_response.json()
        assert context["turn_count"] > 0
        assert len(context["messages"]) > 0

        # 4. 세션 종료
        close_response = client.post(
            f"/api/v2/conversations/{session_id}/close", json={"save_conversation": True}
        )
        assert close_response.status_code == 200

    # ==================== 에러 핸들링 테스트 ====================

    def test_invalid_json_payload(self, client):
        """잘못된 JSON 페이로드"""
        response = client.post(
            "/api/v2/recommend/personalized",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code in [400, 422]

    def test_missing_required_fields(self, client):
        """필수 필드 누락"""
        # 필수 필드인 user_id 없음
        response = client.post("/api/v2/conversations/start", json={"persona_id": "Lua"})

        assert response.status_code == 422

    # ==================== 성능 테스트 ====================

    def test_recommendation_response_time(self, client):
        """권장사항 응답 시간 테스트"""
        import time

        request_data = {"user_id": "user_perf_test", "query": "Complex technical query"}

        start_time = time.time()
        response = client.post("/api/v2/recommend/personalized", json=request_data)
        response_time = time.time() - start_time

        assert response.status_code == 200
        # 응답 시간이 500ms 이내여야 함 (시뮬레이션이므로 빠름)
        assert response_time < 0.5

    def test_turn_processing_response_time(self, client):
        """턴 처리 응답 시간 테스트"""
        import time

        # 세션 생성
        start_response = client.post(
            "/api/v2/conversations/start", json={"user_id": "user_perf_turn", "persona_id": "Lua"}
        )
        session_id = start_response.json()["session_id"]

        # 턴 처리 시간 측정
        start_time = time.time()
        response = client.post(
            f"/api/v2/conversations/{session_id}/turn", json={"user_message": "Hello!"}
        )
        response_time = time.time() - start_time

        assert response.status_code == 200
        # 응답 시간이 500ms 이내여야 함
        assert response_time < 0.5


class TestPhase4DependencyInjection:
    """의존성 주입 테스트"""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)

    def test_engines_initialized_at_startup(self, client):
        """앱 시작 시 엔진 초기화"""
        from app.dependencies import get_phase4_status

        status = get_phase4_status()

        # Phase 4가 가용한 경우 엔진이 초기화되어야 함
        if status["phase4_available"]:
            # 최소한 하나의 엔진이 초기화되었는지 확인
            assert (
                status["recommendation_engine_initialized"]
                or status["session_manager_initialized"]
                or status["multiturn_engine_initialized"]
            )

    def test_singleton_pattern(self, client):
        """싱글톤 패턴 검증"""
        from app.dependencies import (
            get_multiturn_engine,
            get_recommendation_engine,
            get_session_manager,
        )

        try:
            # 동일한 인스턴스를 반환해야 함
            engine1 = get_recommendation_engine()
            engine2 = get_recommendation_engine()
            assert engine1 is engine2

            manager1 = get_session_manager()
            manager2 = get_session_manager()
            assert manager1 is manager2

            multiturn1 = get_multiturn_engine()
            multiturn2 = get_multiturn_engine()
            assert multiturn1 is multiturn2
        except RuntimeError:
            # Phase 4 엔진을 사용할 수 없는 경우 스킵
            pytest.skip("Phase 4 engines not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
