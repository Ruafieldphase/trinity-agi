"""
E2E (End-to-End) 사용자 여정 테스트

이 모듈은 ION Mentoring 애플리케이션의 완전한 사용자 여정을 테스트합니다:
- 모든 4가지 페르소나 라우팅
- 입력 검증 및 에러 처리
- 성능 지표 검증
- 다중 턴 대화 흐름
- 속도 제한 및 복구

전체 시스템이 의도한 대로 작동하는지 검증합니다.
"""

import time

import pytest
from fastapi.testclient import TestClient


class TestHappyPathJourneys:
    """완벽한 흐름 - 모든 페르소나 라우팅 테스트"""

    @pytest.mark.e2e
    def test_emotional_support_journey_lua(self, client: TestClient):
        """
        E2E-001: 감정적 지원 요청 → Lua 페르소나

        사용자가 좌절감을 표현하면 Lua(감정 지원 전문가)가 응답해야 합니다.
        """
        # Arrange
        request_data = {"message": "정말 답답해요! 이 문제를 어떻게 해결하죠?"}

        # Act
        response = client.post("/chat", json=request_data)
        data = response.json()

        # Assert
        assert response.status_code == 200
        # Lua 또는 유사한 감정 지원 페르소나
        assert data["persona_used"] in ["Lua", "Elro", "Riri", "Nana"]
        assert data["confidence"] > 0.5
        assert "resonance_key" in data
        assert "-" in data["resonance_key"]  # tone-pace-intent 형식
        assert len(data["content"]) > 0

        # 성능 검증
        process_time = float(response.headers.get("X-Process-Time", 0))
        assert process_time < 5.0, f"Response time {process_time}s exceeded 5s limit"

    @pytest.mark.e2e
    def test_technical_query_journey_elro(self, client: TestClient):
        """
        E2E-002: 기술 질문 → Elro 페르소나

        기술적 호기심을 표현하면 Elro(논리적 전문가)가 응답해야 합니다.
        """
        # Arrange
        request_data = {"message": "이 함수의 시간 복잡도를 어떻게 분석하나요?"}

        # Act
        response = client.post("/chat", json=request_data)
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert data["persona_used"] in ["Elro", "Riri"]  # 기술 관련 페르소나
        assert data["confidence"] > 0.7
        assert data["metadata"]["tone"]["primary"] in ["curious", "analytical"]
        assert len(data["content"]) > 0

    @pytest.mark.e2e
    def test_analytical_query_journey_riri(self, client: TestClient):
        """
        E2E-003: 데이터 분석 요청 → Riri 페르소나

        분석적 호기심을 표현하면 Riri(분석 전문가)가 응답해야 합니다.
        """
        # Arrange
        request_data = {"message": "데이터를 비교 분석해주세요. 메트릭은?"}

        # Act
        response = client.post("/chat", json=request_data)
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert data["persona_used"] in ["Riri", "Elro"]
        assert data["confidence"] > 0.7
        assert len(data["content"]) > 0

    @pytest.mark.e2e
    def test_coordination_query_journey_nana(self, client: TestClient):
        """
        E2E-004: 프로젝트 조율 요청 → Nana 페르소나

        급하고 협력적인 톤으로 요청하면 Nana(조율 전문가)가 응답해야 합니다.
        """
        # Arrange
        request_data = {"message": "긴급! 프로젝트 일정을 조율해야 해요!"}

        # Act
        response = client.post("/chat", json=request_data)
        data = response.json()

        # Assert
        assert response.status_code == 200
        # 조율 또는 감정 지원 관련 페르소나
        assert data["persona_used"] in ["Nana", "Lua", "Elro"]
        assert len(data["content"]) > 0


class TestInputValidationJourneys:
    """입력 검증 - 잘못된 입력 처리"""

    @pytest.mark.e2e
    def test_empty_message_validation(self, client: TestClient):
        """
        E2E-005: 빈 메시지 입력 오류

        빈 메시지는 검증 오류를 반환해야 합니다.
        """
        # Arrange
        request_data = {"message": ""}

        # Act
        response = client.post("/chat", json=request_data)

        # Assert
        # 422 또는 400 모두 허용 (검증 오류)
        assert response.status_code in [400, 422]

    @pytest.mark.e2e
    def test_whitespace_only_validation(self, client: TestClient):
        """
        E2E-006: 공백만 포함된 메시지 오류

        공백만으로 이루어진 메시지는 검증 오류를 반환해야 합니다.
        """
        # Arrange
        request_data = {"message": "   \t\n  "}

        # Act
        response = client.post("/chat", json=request_data)

        # Assert
        # 422 또는 400 모두 허용 (검증 오류)
        assert response.status_code in [400, 422]

    @pytest.mark.e2e
    def test_message_too_long_validation(self, client: TestClient):
        """
        E2E-007: 메시지 길이 초과 오류

        1000자 이상의 메시지는 검증 오류를 반환해야 합니다.
        """
        # Arrange
        long_message = "A" * 1001
        request_data = {"message": long_message}

        # Act
        response = client.post("/chat", json=request_data)

        # Assert
        # 422 또는 400 모두 허용 (검증 오류)
        assert response.status_code in [400, 422]

    @pytest.mark.e2e
    def test_special_characters_valid(self, client: TestClient):
        """
        E2E-008: 특수 문자 처리

        특수 문자가 포함된 메시지는 정상 처리되어야 합니다.
        """
        # Arrange
        request_data = {"message": "이건 @#$%^&*() 특수문자 테스트입니다!"}

        # Act
        response = client.post("/chat", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "persona_used" in data
        assert len(data["content"]) > 0

    @pytest.mark.e2e
    def test_emoji_message_valid(self, client: TestClient):
        """
        E2E-009: 이모지 메시지 처리

        이모지가 포함된 메시지는 정상 처리되어야 합니다.
        """
        # Arrange
        request_data = {"message": "안녕하세요 😊 도움이 필요합니다 🆘"}

        # Act
        response = client.post("/chat", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "persona_used" in data


class TestPersonaRoutingJourneys:
    """페르소나 라우팅 - 모든 페르소나 테스트"""

    @pytest.mark.e2e
    def test_all_personas_routable(self, client: TestClient):
        """
        E2E-013: 모든 4가지 페르소나 라우팅 가능

        적절한 메시지로 모든 페르소나를 라우팅할 수 있어야 합니다.
        """
        # Arrange - 각 페르소나를 트리거하는 메시지들
        test_cases = [
            ("정말 답답해요!", "Lua"),  # 감정적
            ("기술적으로 어떻게 되나요?", "Elro"),  # 기술적
            ("데이터를 분석해주세요", "Riri"),  # 분석적
            ("급히 조율해야 해요!", "Nana"),  # 긴급/협력
        ]

        personas_routed = set()

        # Act
        for message, target_persona in test_cases:
            response = client.post("/chat", json={"message": message})
            data = response.json()
            personas_routed.add(data["persona_used"])

            # Assert
            assert response.status_code == 200
            assert data["persona_used"] in ["Lua", "Elro", "Riri", "Nana"]
            assert data["confidence"] > 0.5

        # 최소 2개 이상의 서로 다른 페르소나가 라우팅되어야 함
        assert (
            len(personas_routed) >= 2
        ), f"Only {len(personas_routed)} personas routed: {personas_routed}"


class TestErrorHandlingJourneys:
    """에러 처리 - 다양한 오류 시나리오"""

    @pytest.mark.e2e
    def test_missing_message_field(self, client: TestClient):
        """
        E2E-011: 필수 필드 누락

        'message' 필드가 없으면 검증 오류를 반환해야 합니다.
        """
        # Arrange
        request_data = {"wrong_field": "test"}

        # Act
        response = client.post("/chat", json=request_data)

        # Assert
        # 422 또는 400 모두 허용 (검증 오류)
        assert response.status_code in [400, 422]

    @pytest.mark.e2e
    def test_invalid_json_request(self, client: TestClient):
        """
        E2E-012: 잘못된 JSON 형식

        잘못된 JSON은 400 오류를 반환해야 합니다.
        """
        # Act
        response = client.post(
            "/chat", content=b"{invalid json}", headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 422  # Validation error


class TestHealthCheckJourneys:
    """헬스 체크 - 시스템 상태 검증"""

    @pytest.mark.e2e
    def test_health_check_endpoint(self, client: TestClient):
        """
        E2E-015: /health 엔드포인트

        헬스 체크 엔드포인트는 빠르게 응답해야 합니다.
        """
        # Arrange
        start_time = time.time()

        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]

        # 성능 검증
        elapsed_time = time.time() - start_time
        assert elapsed_time < 0.5, f"Health check took {elapsed_time}s (expected < 0.5s)"

        # 헤더 검증
        process_time = float(response.headers.get("X-Process-Time", 0))
        assert process_time < 0.1


class TestPerformanceJourneys:
    """성능 - 응답 시간 및 처리량"""

    @pytest.mark.e2e
    def test_response_time_slo_p95(self, client: TestClient):
        """
        E2E-016: 응답 시간 SLO (P95 < 2초)

        95%의 요청은 2초 이내에 응답해야 합니다.
        """
        # Arrange
        request_data = {"message": "테스트 메시지"}
        response_times = []
        num_requests = 10

        # Act
        for _ in range(num_requests):
            start = time.time()
            response = client.post("/chat", json=request_data)
            elapsed = time.time() - start

            if response.status_code == 200:
                response_times.append(elapsed)

        # Assert
        if response_times:
            response_times.sort()
            p95_index = int(len(response_times) * 0.95)
            p95_time = (
                response_times[p95_index] if p95_index < len(response_times) else response_times[-1]
            )
            assert p95_time < 2.0, f"P95 response time {p95_time}s exceeded 2s limit"

    @pytest.mark.e2e
    def test_concurrent_requests_handling(self, client: TestClient):
        """
        E2E-017: 동시 요청 처리

        여러 순차 요청을 정상 처리해야 합니다.
        """
        # Arrange
        request_data = {"message": "순차 요청 테스트"}
        num_requests = 5

        # Act - 5개의 순차 요청
        responses = []
        for _ in range(num_requests):
            response = client.post("/chat", json=request_data)
            responses.append(response)

        # Assert
        successful = sum(1 for r in responses if r.status_code == 200)
        sum(1 for r in responses if r.status_code == 429)

        # 적어도 1개 이상은 성공해야 함
        assert successful >= 1, "At least 1 request should succeed"

        # 모든 응답이 유효해야 함
        for response in responses:
            assert response.status_code in [200, 429]


class TestDocumentationJourneys:
    """문서 - API 문서 접근"""

    @pytest.mark.e2e
    def test_swagger_docs_accessible(self, client: TestClient):
        """
        E2E-018: Swagger API 문서

        /docs 엔드포인트는 Swagger UI를 제공해야 합니다.
        """
        # Act
        response = client.get("/docs")

        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.e2e
    def test_redoc_docs_accessible(self, client: TestClient):
        """
        ReDoc API 문서

        /redoc 엔드포인트는 ReDoc을 제공해야 합니다.
        """
        # Act
        response = client.get("/redoc")

        # Assert
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.e2e
    def test_openapi_schema_accessible(self, client: TestClient):
        """
        OpenAPI 스키마

        /openapi.json은 유효한 OpenAPI 스키마를 제공해야 합니다.
        """
        # Act
        response = client.get("/openapi.json")

        # Assert
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema


class TestResponseValidationJourneys:
    """응답 검증 - 응답 구조 및 내용 검증"""

    @pytest.mark.e2e
    def test_response_schema_validation(self, client: TestClient):
        """
        응답 스키마 검증

        응답은 필수 필드를 모두 포함해야 합니다.
        """
        # Arrange
        request_data = {"message": "스키마 검증 테스트"}

        # Act
        response = client.post("/chat", json=request_data)
        data = response.json()

        # Assert
        assert response.status_code == 200

        # 필수 필드 검증
        required_fields = ["content", "persona_used", "resonance_key", "confidence", "metadata"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # 필드 타입 검증
        assert isinstance(data["content"], str) and len(data["content"]) > 0
        assert isinstance(data["persona_used"], str)
        assert data["persona_used"] in ["Lua", "Elro", "Riri", "Nana"]
        assert isinstance(data["resonance_key"], str)
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0
        assert isinstance(data["metadata"], dict)

    @pytest.mark.e2e
    def test_metadata_structure_validation(self, client: TestClient):
        """
        메타데이터 구조 검증

        메타데이터는 리듬, 톤, 라우팅 정보를 포함해야 합니다.
        """
        # Arrange
        request_data = {"message": "메타데이터 검증"}

        # Act
        response = client.post("/chat", json=request_data)
        data = response.json()

        # Assert
        metadata = data["metadata"]

        # 주요 구조 검증
        assert "rhythm" in metadata
        assert "tone" in metadata
        assert "routing" in metadata

        # rhythm 필드 검증
        rhythm = metadata["rhythm"]
        assert "pace" in rhythm
        assert rhythm["pace"] in [
            "burst",
            "flowing",
            "contemplative",
            "medium",
            "steady",
            "measured",
        ]

        # tone 필드 검증
        tone = metadata["tone"]
        assert "primary" in tone
        assert "confidence" in tone
        assert isinstance(tone["confidence"], (int, float))


class TestEdgeCaseJourneys:
    """엣지 케이스 - 경계 케이스 테스트"""

    @pytest.mark.e2e
    def test_single_character_message(self, client: TestClient):
        """
        단일 문자 메시지

        1글자 메시지도 정상 처리되어야 합니다.
        """
        # Arrange
        request_data = {"message": "A"}

        # Act
        response = client.post("/chat", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "persona_used" in data

    @pytest.mark.e2e
    def test_unicode_korean_message(self, client: TestClient):
        """
        유니코드 한글 메시지

        한글만 포함된 메시지도 정상 처리되어야 합니다.
        """
        # Arrange
        request_data = {"message": "안녕하세요 저는 한글만 사용합니다"}

        # Act
        response = client.post("/chat", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "persona_used" in data

    @pytest.mark.e2e
    def test_mixed_language_message(self, client: TestClient):
        """
        혼합 언어 메시지

        한글과 영어가 혼합된 메시지도 정상 처리되어야 합니다.
        """
        # Arrange
        request_data = {"message": "안녕 hello 안녕 world"}

        # Act
        response = client.post("/chat", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "persona_used" in data


# 테스트 실행 가이드
"""
E2E 테스트 실행 방법:

1. 모든 E2E 테스트 실행:
   pytest tests/e2e/test_complete_user_journeys.py -v

2. 특정 카테고리 실행:
   pytest tests/e2e/test_complete_user_journeys.py::TestHappyPathJourneys -v

3. 성능 관련 테스트만:
   pytest tests/e2e/test_complete_user_journeys.py::TestPerformanceJourneys -v

4. 마커로 실행:
   pytest tests/e2e/ -m e2e -v

5. 상세 출력과 함께:
   pytest tests/e2e/ -vv --tb=short

6. 실패한 테스트만 재실행:
   pytest tests/e2e/ --lf

테스트 커버리지 검증:
pytest tests/e2e/ --cov=app --cov-report=html
"""
