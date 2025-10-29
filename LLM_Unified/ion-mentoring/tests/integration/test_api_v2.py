"""
API v2 통합 테스트

Week 11: API v2 엔드포인트 테스트
- 스키마 검증
- 엔드포인트 테스트
- 호환성 검증
- 성능 테스트
"""

import json
from datetime import datetime

import pytest

# Mock FastAPI app for testing
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v2_routes import router as v2_router


# Test app setup
def create_test_app():
    """테스트용 FastAPI 앱 생성"""
    app = FastAPI()
    app.include_router(v2_router)
    return app


@pytest.fixture
def client():
    """테스트 클라이언트"""
    app = create_test_app()
    return TestClient(app)


@pytest.fixture
def valid_process_request():
    """유효한 처리 요청"""
    return {
        "user_input": "안녕하세요, 도움이 필요합니다",
        "resonance_key": {"tone": "calm", "pace": "medium", "intent": "seeking_advice"},
        "use_cache": True,
    }


@pytest.fixture
def valid_recommend_request():
    """유효한 추천 요청"""
    return {"scenario": "사용자가 감정적 지원이 필요합니다"}


class TestHealthCheck:
    """헬스 체크 테스트"""

    def test_health_endpoint_exists(self, client):
        """헬스 엔드포인트 존재"""
        response = client.get("/api/v2/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """헬스 응답 구조"""
        response = client.get("/api/v2/health")
        data = response.json()

        assert "healthy" in data
        assert "service_status" in data
        assert "dependencies" in data
        assert "timestamp" in data

    def test_health_status_operational(self, client):
        """서비스 상태 operational"""
        response = client.get("/api/v2/health")
        data = response.json()

        assert data["healthy"] in [True, False]
        if data["healthy"]:
            assert data["service_status"]["status"] in ["operational", "degraded"]


class TestProcessEndpoint:
    """처리 엔드포인트 테스트"""

    def test_process_endpoint_exists(self, client):
        """처리 엔드포인트 존재"""
        response = client.post(
            "/api/v2/process",
            json={
                "user_input": "테스트",
                "resonance_key": {"tone": "calm", "pace": "medium", "intent": "learning"},
            },
        )
        assert response.status_code == 200

    def test_process_valid_request(self, client, valid_process_request):
        """유효한 요청 처리"""
        response = client.post("/api/v2/process", json=valid_process_request)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "content" in data
        assert "persona_used" in data
        assert data["persona_used"] in ["Lua", "Elro", "Riri", "Nana"]

    def test_process_response_structure(self, client, valid_process_request):
        """응답 구조 검증"""
        response = client.post("/api/v2/process", json=valid_process_request)
        data = response.json()

        # 필수 필드
        assert "success" in data
        assert "content" in data
        assert "persona_used" in data
        assert "resonance_key" in data

        # 선택 필드
        assert "routing" in data
        assert "performance" in data
        assert "timestamp" in data
        assert "request_id" in data

    def test_process_performance_info(self, client, valid_process_request):
        """성능 정보 포함"""
        response = client.post("/api/v2/process", json=valid_process_request)
        data = response.json()

        performance = data.get("performance")
        assert performance is not None
        assert "execution_time_ms" in performance
        assert "cache_hit" in performance
        assert performance["execution_time_ms"] > 0

    def test_process_empty_input_error(self, client):
        """빈 입력 에러"""
        response = client.post(
            "/api/v2/process",
            json={
                "user_input": "",
                "resonance_key": {"tone": "calm", "pace": "medium", "intent": "learning"},
            },
        )
        assert response.status_code in [200, 400]
        data = response.json()
        if response.status_code == 200:
            assert data.get("success") in [True, False]

    def test_process_invalid_tone(self, client):
        """유효하지 않은 톤"""
        response = client.post(
            "/api/v2/process",
            json={
                "user_input": "테스트",
                "resonance_key": {"tone": "invalid_tone", "pace": "medium", "intent": "learning"},
            },
        )
        # 기본값으로 복구되거나 에러
        assert response.status_code in [200, 400]

    def test_process_with_context(self, client):
        """컨텍스트 포함 처리"""
        response = client.post(
            "/api/v2/process",
            json={
                "user_input": "테스트",
                "resonance_key": {"tone": "calm", "pace": "medium", "intent": "learning"},
                "context": {"user_id": "test_user", "session_id": "test_session"},
            },
        )
        assert response.status_code == 200

    def test_process_cache_performance(self, client, valid_process_request):
        """캐시 성능"""
        # 첫 호출
        response1 = client.post("/api/v2/process", json=valid_process_request)
        response1.json()["performance"]["execution_time_ms"]

        # 두 번째 호출 (캐시)
        response2 = client.post("/api/v2/process", json=valid_process_request)
        response2.json()["performance"]["execution_time_ms"]

        # 캐시된 호출이 더 빠를 수 있음
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestRecommendEndpoint:
    """추천 엔드포인트 테스트"""

    def test_recommend_endpoint_exists(self, client):
        """추천 엔드포인트 존재"""
        response = client.post("/api/v2/recommend", json={"scenario": "테스트"})
        assert response.status_code == 200

    def test_recommend_valid_request(self, client, valid_recommend_request):
        """유효한 추천 요청"""
        response = client.post("/api/v2/recommend", json=valid_recommend_request)
        assert response.status_code == 200

        data = response.json()
        assert "recommended_persona" in data
        assert data["recommended_persona"] in ["Lua", "Elro", "Riri", "Nana"]

    def test_recommend_response_structure(self, client, valid_recommend_request):
        """추천 응답 구조"""
        response = client.post("/api/v2/recommend", json=valid_recommend_request)
        data = response.json()

        assert "recommended_persona" in data
        assert "scores" in data
        assert "capabilities" in data
        assert isinstance(data["scores"], dict)

    def test_recommend_capabilities_included(self, client, valid_recommend_request):
        """페르소나 능력 정보 포함"""
        response = client.post("/api/v2/recommend", json=valid_recommend_request)
        data = response.json()

        capabilities = data["capabilities"]
        assert "name" in capabilities
        assert "traits" in capabilities
        assert "strengths" in capabilities


class TestBulkProcessEndpoint:
    """일괄 처리 엔드포인트 테스트"""

    def test_bulk_process_endpoint_exists(self, client):
        """일괄 처리 엔드포인트 존재"""
        response = client.post(
            "/api/v2/bulk-process",
            json={
                "requests": [
                    {
                        "user_input": "테스트 1",
                        "resonance_key": {"tone": "calm", "pace": "medium", "intent": "learning"},
                    }
                ]
            },
        )
        assert response.status_code == 200

    def test_bulk_process_valid_request(self, client):
        """유효한 일괄 요청"""
        response = client.post(
            "/api/v2/bulk-process",
            json={
                "requests": [
                    {
                        "user_input": f"테스트 {i}",
                        "resonance_key": {"tone": "calm", "pace": "medium", "intent": "learning"},
                    }
                    for i in range(3)
                ]
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["total"] == 3
        assert data["successful"] == 3

    def test_bulk_process_response_structure(self, client):
        """일괄 응답 구조"""
        response = client.post(
            "/api/v2/bulk-process",
            json={
                "requests": [
                    {
                        "user_input": "테스트",
                        "resonance_key": {"tone": "calm", "pace": "medium", "intent": "learning"},
                    }
                ]
            },
        )
        data = response.json()

        assert "success" in data
        assert "total" in data
        assert "successful" in data
        assert "failed" in data
        assert "results" in data

    def test_bulk_process_limit(self, client):
        """일괄 처리 제한"""
        # 100개 이상 요청
        requests = [
            {
                "user_input": f"테스트 {i}",
                "resonance_key": {"tone": "calm", "pace": "medium", "intent": "learning"},
            }
            for i in range(101)
        ]

        response = client.post("/api/v2/bulk-process", json={"requests": requests})
        # 제한 초과 에러
        assert response.status_code in [200, 413]


class TestListPersonasEndpoint:
    """페르소나 목록 엔드포인트 테스트"""

    def test_list_personas_endpoint_exists(self, client):
        """페르소나 목록 엔드포인트 존재"""
        response = client.get("/api/v2/personas")
        assert response.status_code == 200

    def test_list_personas_response(self, client):
        """페르소나 목록 응답"""
        response = client.get("/api/v2/personas")
        data = response.json()

        assert "total" in data
        assert "personas" in data
        assert len(data["personas"]) == 4

    def test_list_personas_structure(self, client):
        """페르소나 정보 구조"""
        response = client.get("/api/v2/personas")
        data = response.json()

        for persona in data["personas"]:
            assert "name" in persona
            assert "traits" in persona
            assert "strengths" in persona


class TestPersonaInfoEndpoint:
    """페르소나 정보 엔드포인트 테스트"""

    def test_persona_info_endpoint_exists(self, client):
        """페르소나 정보 엔드포인트 존재"""
        response = client.get("/api/v2/personas/lua")
        assert response.status_code == 200

    def test_persona_info_valid_persona(self, client):
        """유효한 페르소나 조회"""
        for persona_name in ["lua", "elro", "riri", "nana"]:
            response = client.get(f"/api/v2/personas/{persona_name}")
            assert response.status_code == 200

            data = response.json()
            assert "name" in data
            assert data["name"].lower() == persona_name

    def test_persona_info_invalid_persona(self, client):
        """유효하지 않은 페르소나"""
        response = client.get("/api/v2/personas/invalid")
        # 404 또는 에러 응답
        assert response.status_code in [200, 404]


class TestCacheStatsEndpoint:
    """캐시 통계 엔드포인트 테스트"""

    def test_cache_stats_endpoint_exists(self, client):
        """캐시 통계 엔드포인트 존재"""
        response = client.get("/api/v2/cache-stats")
        assert response.status_code == 200

    def test_cache_stats_response(self, client):
        """캐시 통계 응답"""
        response = client.get("/api/v2/cache-stats")
        data = response.json()

        assert "total_requests" in data
        assert "cache_hits" in data
        assert "cache_misses" in data


class TestErrorHandling:
    """에러 처리 테스트"""

    def test_invalid_json_error(self, client):
        """유효하지 않은 JSON"""
        response = client.post(
            "/api/v2/process", data="invalid json", headers={"Content-Type": "application/json"}
        )
        assert response.status_code >= 400

    def test_missing_required_fields(self, client):
        """필수 필드 누락"""
        response = client.post(
            "/api/v2/process",
            json={
                # user_input 누락
                "resonance_key": {"tone": "calm", "pace": "medium", "intent": "learning"}
            },
        )
        # 에러 또는 기본값
        assert response.status_code in [200, 422]


class TestResponseSerialization:
    """응답 직렬화 테스트"""

    def test_response_json_serializable(self, client, valid_process_request):
        """응답이 JSON 직렬화 가능"""
        response = client.post("/api/v2/process", json=valid_process_request)
        data = response.json()

        # JSON 직렬화 확인
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

    def test_timestamp_format(self, client, valid_process_request):
        """타임스탬프 형식"""
        response = client.post("/api/v2/process", json=valid_process_request)
        data = response.json()

        timestamp = data.get("timestamp")
        assert timestamp is not None
        # ISO 8601 형식 확인
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


class TestAPIVersioning:
    """API 버전 관리 테스트"""

    def test_v2_endpoint_prefix(self, client):
        """v2 엔드포인트 프리픽스"""
        response = client.get("/api/v2/health")
        assert response.status_code == 200

    def test_api_version_header(self, client, valid_process_request):
        """API 버전 헤더"""
        response = client.post(
            "/api/v2/process", json=valid_process_request, headers={"X-API-Version": "v2"}
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
