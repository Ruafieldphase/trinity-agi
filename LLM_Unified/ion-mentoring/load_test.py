"""
Load testing script for ION Mentoring API using locust.

This script simulates multiple users making requests to the API
to test performance, rate limiting, and auto-scaling behavior.
"""

import json
import logging
import random

from locust import HttpUser, between, tag, task

# 로깅 설정
logger = logging.getLogger(__name__)

# 테스트 메시지와 엣지 케이스 메시지 상수화
STANDARD_MESSAGES = [
    "Hello there! Sample greeting message.",
    "This payload checks how the system handles multiple requests.",
    "Testing the ION Mentoring API performance under load.",
    "Persona scenario: user asks for study guidance today.",
    "Load testing with various message lengths and punctuation.",
    "Mixed language message: Hello, annyeong, how are you today?",
    "Short note.",
    "Very long message " + "to test latency " * 10,
    "API performance validation is in progress.",
    "Quick follow-up question about mentoring styles.",
]

EDGE_CASE_MESSAGES = [
    "",  # Empty message
    "A" * 10000,  # Very long message
    "!@#$%^&*()_+-=[]{}|;':,./<>?`~",  # Special characters
    "\U0001F600" * 100,  # Emojis
    "\0\0\0\0",  # Null bytes
    "\n\n\n",  # Newlines
    "contains\u0000embedded\u0000nulls",  # Embedded null characters
    "{not: 'json'}",  # Malformed JSON (will be sent as string)
    None,  # NoneType (should be handled)
]

CHAT_ONLY_MESSAGES = [
    "Chat only test message.",
    "Endpoint-specific load test.",
    "Stress /chat endpoint.",
    "Focused load test on chat endpoint.",
    "Just chat, nothing else.",
]


# --- Standard User: All Endpoints ---
class IonApiUser(HttpUser):
    """
    표준 사용자: ION Mentoring API의 모든 엔드포인트를 테스트합니다.
    """

    wait_time = between(1, 3)

    @tag("health")
    @task(1)
    def get_health(self):
        """헬스 체크 엔드포인트 테스트"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code in (200, 429):
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
                logger.warning(f"Health check failed: {response.status_code}")

    @tag("chat", "main")
    @task(5)
    def post_chat(self):
        """채팅 엔드포인트 테스트"""
        message = random.choice(STANDARD_MESSAGES)
        payload = {"message": message}
        with self.client.post("/chat", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    has_response = "response" in data or "content" in data
                    required_fields = ["persona_used", "resonance_key", "confidence"]
                    if has_response and all(field in data for field in required_fields):
                        response.success()
                    else:
                        response.failure("Missing required fields in response")
                        logger.warning(f"Chat response missing fields: {data}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
                    logger.error("Chat response is not valid JSON")
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
                logger.warning(f"Chat request failed: {response.status_code}")

    @tag("docs")
    @task(2)
    def get_docs(self):
        """API 문서 엔드포인트 테스트"""
        with self.client.get("/docs", catch_response=True) as response:
            if response.status_code in (200, 429):
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
                logger.warning(f"Docs request failed: {response.status_code}")


# --- Edge Case User: Abnormal Payloads ---
class EdgeCaseUser(HttpUser):
    """
    엣지 케이스 사용자: 비정상적인 페이로드를 테스트합니다.
    """

    wait_time = between(1, 3)

    @tag("edge")
    @task(1)
    def post_edge_chat(self):
        """엣지 케이스 메시지로 채팅 엔드포인트 테스트"""
        message = random.choice(EDGE_CASE_MESSAGES)

        # 특수 케이스: 비정상 JSON 형식
        if message == "{not: 'json'}":
            with self.client.post(
                "/chat",
                data=message,
                headers={"Content-Type": "application/json"},
                catch_response=True,
            ) as response:
                if response.status_code in (200, 400, 422):
                    response.success()
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
                    logger.warning(f"Malformed JSON test failed: {response.status_code}")
            return

        # 정상 케이스
        payload = {"message": message}
        with self.client.post("/chat", json=payload, catch_response=True) as response:
            # 엣지 케이스는 200, 400, 422를 모두 유효하다고 간주
            if response.status_code in (200, 400, 422):
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
                logger.warning(f"Edge case test failed: {response.status_code}")


# --- Chat Only User: Only /chat endpoint ---
class ChatOnlyUser(HttpUser):
    """
    채팅 전용 사용자: /chat 엔드포인트만 집중적으로 테스트합니다.
    """

    wait_time = between(1, 3)

    @tag("chatonly")
    @task(1)
    def post_chat(self):
        """채팅 엔드포인트 집중 테스트"""
        message = random.choice(CHAT_ONLY_MESSAGES)
        payload = {"message": message}
        with self.client.post("/chat", json=payload, catch_response=True) as response:
            if response.status_code in (200, 429):
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
                logger.warning(f"Chat-only test failed: {response.status_code}")


# --- Usage Notes ---
"""
다양한 설정으로 이 스크립트를 실행하세요:

## 로드 테스트 시나리오

# 1. 가벼운 부하 테스트 (10명 사용자, 1초당 1명씩 생성)
locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app --users 10 --spawn-rate 1 --run-time 2m

# 2. 중간 부하 테스트 (50명 사용자, 1초당 5명씩 생성)
locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app --users 50 --spawn-rate 5 --run-time 5m

# 3. 높은 부하 테스트 (100명 사용자, 레이트 제한 트리거)
locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app --users 100 --spawn-rate 10 --run-time 5m

# 4. 스트레스 테스트 (200명 사용자, 자동 스케일링 트리거)
locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app --users 200 --spawn-rate 20 --run-time 10m

# 5. 지속 테스트 (50명 사용자, 8시간 지속)
locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app --users 50 --spawn-rate 5 --run-time 8h --headless --csv=outputs/load_test_soak

# 6. 스파이크 테스트 (0→200명, 1분 램프업, 5분 유지)
locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app --users 200 --spawn-rate 200 --run-time 6m --headless --csv=outputs/load_test_spike

# 7. 엣지 케이스 테스트 (비정상 페이로드)
locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app --users 20 --spawn-rate 2 --run-time 5m --headless --csv=outputs/load_test_edge --tags edge

# 8. 엔드포인트 집중 테스트 (/chat만 테스트)
locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app --users 50 --spawn-rate 5 --run-time 5m --headless --csv=outputs/load_test_chatonly --tags chatonly

# 9. 웹 UI 모드 (대화형 테스트)
locust -f load_test.py --host=https://ion-api-64076350717.us-central1.run.app
# 그 후 http://localhost:8089 방문

## 주요 개선사항:
- 상수화된 테스트 메시지 (유지보수 용이)
- 개선된 로깅 (디버깅 시 도움)
- 코드 중복 제거 (DRY 원칙)
- 명확한 상태 코드 처리 (429 레이트 제한 포함)
"""
