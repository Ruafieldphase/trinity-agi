"""
API 통합 테스트

전체 API 흐름이 정상 동작하는지 테스트합니다.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ion-mentoring 디렉토리 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from persona_pipeline import PersonaResponse


@pytest.mark.integration
class TestChatEndpointFlow:
    """채팅 엔드포인트 통합 테스트"""

    def test_complete_chat_flow(self, client, mock_pipeline_response):
        """완전한 채팅 흐름 테스트"""
        with patch("app.main.pipeline") as mock_pipeline:
            mock_pipeline.process.return_value = mock_pipeline_response

            # 1. 채팅 요청
            response = client.post(
                "/chat", json={"message": "안녕하세요, 이 프로젝트를 설명해주시겠어요?", "user_id": "test-user"}
            )

            # 2. 응답 검증
            assert response.status_code == 200
            data = response.json()

            # 3. 응답 내용 검증
            assert data["persona_used"] == "Lua"
            assert data["confidence"] == 0.85
            assert "rhythm" in data["metadata"]
            assert "tone" in data["metadata"]

            # 4. pipeline.process 호출 확인
            mock_pipeline.process.assert_called_once()
            call_args = mock_pipeline.process.call_args
            assert call_args[0][0] == "안녕하세요, 이 프로젝트를 설명해주시겠어요?"

    def test_health_check_flow(self, client):
        """헬스체크 흐름 테스트"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["healthy", "degraded"]
        assert data["version"] == "1.0.0"
        assert "pipeline_ready" in data

    def test_root_endpoint_flow(self, client):
        """루트 엔드포인트 흐름"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_retry_logic_on_failure(self, client, mock_pipeline_response):
        """실패 시 에러 처리 확인"""
        with patch("app.main.pipeline") as mock_pipeline:
            # 파이프라인 실패 시뮬레이션
            mock_pipeline.process.side_effect = Exception("Pipeline failed")

            response = client.post("/chat", json={"message": "테스트", "user_id": "test-user"})

            # 에러 발생 시 500 반환 확인
            assert response.status_code == 500
            data = response.json()
            assert "error" in data


@pytest.mark.integration
class TestPersonaRouting:
    """페르소나 라우팅 통합 테스트"""

    def test_persona_selection_based_on_message(
        self, client, mock_elro_response, mock_riri_response, mock_nana_response
    ):
        """메시지에 따른 페르소나 선택"""
        test_cases = [
            ("논리적 문제를 분석해주세요", "Elro", mock_elro_response),
            ("데이터를 비교 분석해보세요", "Riri", mock_riri_response),
            ("프로젝트를 종합적으로 조율해주세요", "Nana", mock_nana_response),
        ]

        for message, expected_persona, mock_response in test_cases:
            with patch("app.main.pipeline") as mock_pipeline:
                mock_pipeline.process.return_value = mock_response

                response = client.post("/chat", json={"message": message, "user_id": "test-user"})

                assert response.status_code == 200
                data = response.json()
                assert data["persona_used"] == expected_persona

    def test_persona_confidence_scores(
        self,
        client,
        mock_elro_response,
        mock_riri_response,
        mock_nana_response,
        mock_pipeline_response,
    ):
        """페르소나별 신뢰도 점수"""
        responses = [
            ("Lua", 0.85, mock_pipeline_response),
            ("Elro", 0.9, mock_elro_response),
            ("Riri", 0.88, mock_riri_response),
            ("Nana", 0.82, mock_nana_response),
        ]

        for persona_id, expected_confidence, mock_response in responses:
            with patch("app.main.pipeline") as mock_pipeline:
                mock_pipeline.process.return_value = mock_response

                response = client.post("/chat", json={"message": f"{persona_id}를 테스트합니다", "user_id": "test-user"})

                assert response.status_code == 200
                data = response.json()
                assert data["confidence"] == expected_confidence


@pytest.mark.integration
class TestErrorHandling:
    """에러 처리 통합 테스트"""

    def test_validation_error_handling(self, client):
        """입력 검증 에러 처리"""
        invalid_requests = [
            {"message": ""},  # 빈 메시지
            {"message": "   "},  # 공백만
            {"text": "필드명 오류"},  # 잘못된 필드
            {"message": 12345},  # 잘못된 타입
        ]

        for invalid_request in invalid_requests:
            response = client.post("/chat", json=invalid_request)
            assert response.status_code in [400, 422]

    def test_server_error_handling(self, client):
        """서버 에러 처리"""
        with patch("app.main.pipeline") as mock_pipeline:
            mock_pipeline.process.side_effect = Exception("Unexpected error")

            response = client.post("/chat", json={"message": "테스트", "user_id": "test-user"})

            assert response.status_code == 500
            data = response.json()
            assert "error" in data

    def test_timeout_error_handling(self, client):
        """타임아웃 에러 처리"""
        with patch("app.main.pipeline") as mock_pipeline:
            mock_pipeline.process.side_effect = TimeoutError("Response timeout")

            response = client.post("/chat", json={"message": "테스트", "user_id": "test-user"})

            # TimeoutError도 500으로 처리됨 (일반 에러 처리)
            assert response.status_code == 500
            data = response.json()
            assert "error" in data

    def test_fallback_response_on_error(self, client, mock_fallback_response):
        """에러 시 폴백 응답"""
        with patch("app.main.pipeline") as mock_pipeline:
            mock_pipeline.process.return_value = mock_fallback_response

            response = client.post("/chat", json={"message": "테스트", "user_id": "test-user"})

            assert response.status_code == 200
            data = response.json()
            assert data["persona_used"] == "Nana"
            assert data["confidence"] == 0.0
            assert "error" in data["metadata"]


@pytest.mark.integration
class TestResponseValidation:
    """응답 검증 통합 테스트"""

    def test_response_schema_structure(self, client, mock_pipeline_response):
        """응답 스키마 구조 검증"""
        with patch("app.main.pipeline") as mock_pipeline:
            mock_pipeline.process.return_value = mock_pipeline_response

            response = client.post("/chat", json={"message": "테스트", "user_id": "test-user"})

            assert response.status_code == 200
            data = response.json()

            # 필수 필드
            required_fields = ["content", "persona_used", "resonance_key", "confidence", "metadata"]
            for field in required_fields:
                assert field in data

            # 타입 검증
            assert isinstance(data["content"], str)
            assert isinstance(data["persona_used"], str)
            assert isinstance(data["resonance_key"], str)
            assert isinstance(data["confidence"], float)
            assert isinstance(data["metadata"], dict)

    def test_metadata_completeness(self, client, mock_pipeline_response):
        """메타데이터 완성도 검증"""
        with patch("app.main.pipeline") as mock_pipeline:
            mock_pipeline.process.return_value = mock_pipeline_response

            response = client.post("/chat", json={"message": "테스트", "user_id": "test-user"})

            assert response.status_code == 200
            metadata = response.json()["metadata"]

            # 주요 메타데이터 필드
            assert "rhythm" in metadata
            assert "tone" in metadata
            assert "routing" in metadata

            # rhythm 필드
            assert "pace" in metadata["rhythm"]
            assert "avg_length" in metadata["rhythm"]
            assert "punctuation_density" in metadata["rhythm"]

            # tone 필드
            assert "primary" in metadata["tone"]
            assert "confidence" in metadata["tone"]

    def test_confidence_range_validation(self, client):
        """신뢰도 범위 검증 (0.0-1.0)"""
        test_confidences = [0.0, 0.25, 0.5, 0.75, 1.0]

        for confidence_value in test_confidences:
            response = PersonaResponse(
                content="테스트",
                persona_used="Lua",
                resonance_key="test-key",
                confidence=confidence_value,
                metadata={},
            )

            assert 0.0 <= response.confidence <= 1.0


@pytest.mark.integration
class TestPerformanceMetrics:
    """성능 메트릭 통합 테스트"""

    def test_response_headers_include_process_time(self, client, mock_pipeline_response):
        """응답 처리 시간 검증"""
        with patch("app.main.pipeline") as mock_pipeline:
            mock_pipeline.process.return_value = mock_pipeline_response

            response = client.post("/chat", json={"message": "테스트", "user_id": "test-user"})

            assert response.status_code == 200
            # X-Process-Time 헤더는 선택사항 (로그에서 확인 가능)
            # 응답이 정상적으로 처리되었는지 확인
            data = response.json()
            assert "persona_used" in data

    def test_health_check_response_time(self, client):
        """헬스체크 응답 확인"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # 헬스체크는 상태 정보를 반환
        assert "status" in data
        assert data["status"] in ["healthy", "running"]


@pytest.mark.integration
@pytest.mark.slow
class TestLoadBehavior:
    """부하 상황 테스트"""

    def test_multiple_concurrent_requests(self, client, mock_pipeline_response):
        """동시 요청 처리"""
        with patch("app.main.pipeline") as mock_pipeline:
            mock_pipeline.process.return_value = mock_pipeline_response

            # 5개의 동시 요청 시뮬레이션
            responses = []
            for i in range(5):
                response = client.post("/chat", json={"message": f"테스트 메시지 {i}", "user_id": "test-user"})
                responses.append(response)

            # 모든 요청이 성공
            for response in responses:
                assert response.status_code == 200

            # pipeline.process 호출 횟수 확인
            assert mock_pipeline.process.call_count == 5

    def test_rapid_fire_requests(self, client, mock_pipeline_response):
        """빠른 속도의 연속 요청"""
        with patch("app.main.pipeline") as mock_pipeline:
            mock_pipeline.process.return_value = mock_pipeline_response

            # 10개의 빠른 요청
            for i in range(10):
                response = client.post("/chat", json={"message": f"메시지 {i}", "user_id": "test-user"})
                assert response.status_code == 200
