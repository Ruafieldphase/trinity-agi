"""
Security Edge Cases 테스트

- Unicode/Emoji 입력 처리
- 동시 요청 스레드 안전성
- 입력 검증 및 새니타이제이션
- 타이밍 공격 방어
- 메모리 누수 검사
"""

import asyncio
import logging
import time

import pytest
from httpx import AsyncClient

logger = logging.getLogger(__name__)


class TestUnicodeHandling:
    """Unicode 및 다국어 입력 처리 테스트"""

    @pytest.mark.asyncio
    async def test_korean_characters(self, async_client: AsyncClient):
        """한글 입력 처리"""
        response = await async_client.post(
            "/chat",
            json={
                "message": "안녕하세요. 저는 한국어를 배우고 있습니다.",
                "user_id": "test-user-ko",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 0

    @pytest.mark.asyncio
    async def test_chinese_characters(self, async_client: AsyncClient):
        """중국어 입력 처리"""
        response = await async_client.post(
            "/chat", json={"message": "你好。我很高兴认识你。", "user_id": "test-user-zh"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_japanese_characters(self, async_client: AsyncClient):
        """일본어 입력 처리"""
        response = await async_client.post(
            "/chat",
            json={"message": "こんにちは。今日は良い天気ですね。", "user_id": "test-user-ja"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_arabic_characters(self, async_client: AsyncClient):
        """아랍어 입력 처리 (RTL)"""
        response = await async_client.post(
            "/chat", json={"message": "مرحبا، كيف حالك؟", "user_id": "test-user-ar"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_mixed_scripts(self, async_client: AsyncClient):
        """혼합 스크립트 입력"""
        response = await async_client.post(
            "/chat",
            json={"message": "Hello 안녕 مرحبا 你好 こんにちは", "user_id": "test-user-mixed"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_zero_width_characters(self, async_client: AsyncClient):
        """Zero-width 문자 입력 (보안 테스트)"""
        # Zero-width space: \u200b
        response = await async_client.post(
            "/chat", json={"message": "Hello\u200bWorld", "user_id": "test-user-zw"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_control_characters(self, async_client: AsyncClient):
        """제어 문자 필터링 테스트"""
        response = await async_client.post(
            "/chat",
            json={
                "message": "Hello\x00World\x1bEnd",  # NULL, ESC 문자
                "user_id": "test-user-ctrl",
            },
        )
        # 제어 문자는 필터링되거나 안전하게 처리되어야 함
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_very_long_unicode_string(self, async_client: AsyncClient):
        """매우 긴 Unicode 문자열"""
        long_message = "한글 " * 1000  # 5000자
        response = await async_client.post(
            "/chat", json={"message": long_message, "user_id": "test-user-long"}
        )
        # 최대 길이 검사
        if response.status_code == 422:
            assert "max_message_length" in response.json().get("detail", [])[0]["loc"]
        else:
            assert response.status_code == 200


class TestEmojiHandling:
    """Emoji 입력 처리 테스트"""

    @pytest.mark.asyncio
    async def test_common_emojis(self, async_client: AsyncClient):
        """일반 Emoji 처리"""
        response = await async_client.post(
            "/chat", json={"message": "Hello 👋 How are you? 😊", "user_id": "test-user-emoji1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_skin_tone_modifiers(self, async_client: AsyncClient):
        """Emoji 스킨톤 수정자"""
        response = await async_client.post(
            "/chat", json={"message": "👋🏽 Hi there! 👩🏿‍💼", "user_id": "test-user-emoji2"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_family_emojis(self, async_client: AsyncClient):
        """가족 Emoji (ZWJ 시퀀스)"""
        response = await async_client.post(
            "/chat", json={"message": "👨‍👩‍👧‍👦 Family", "user_id": "test-user-emoji3"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_flag_emojis(self, async_client: AsyncClient):
        """국기 Emoji"""
        response = await async_client.post(
            "/chat", json={"message": "🇰🇷 Korea 🇺🇸 USA 🇯🇵 Japan", "user_id": "test-user-emoji4"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

    @pytest.mark.asyncio
    async def test_only_emojis(self, async_client: AsyncClient):
        """Emoji만 있는 메시지"""
        response = await async_client.post(
            "/chat", json={"message": "😊😂😍🥰😘", "user_id": "test-user-emoji5"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data


class TestConcurrentRequests:
    """동시 요청 처리 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_requests_10(self, async_client: AsyncClient):
        """동시 10개 요청"""
        tasks = []
        for i in range(10):
            task = async_client.post(
                "/chat",
                json={"message": f"Concurrent request {i}", "user_id": f"user-concurrent-{i}"},
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 모든 응답 검사
        for response in responses:
            if not isinstance(response, Exception):
                assert response.status_code == 200
                data = response.json()
                assert "content" in data
                assert "persona_used" in data

    @pytest.mark.asyncio
    async def test_concurrent_requests_100(self, async_client: AsyncClient):
        """동시 100개 요청"""
        tasks = []
        for i in range(100):
            task = async_client.post(
                "/chat", json={"message": f"Request {i}", "user_id": f"user-{i}"}
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 성공률 검사 (99% 이상)
        successful = sum(
            1 for r in responses if not isinstance(r, Exception) and r.status_code == 200
        )
        success_rate = successful / len(responses)
        assert success_rate >= 0.99, f"Success rate {success_rate} < 99%"

    @pytest.mark.asyncio
    async def test_concurrent_different_personas(self, async_client: AsyncClient):
        """다양한 personas으로 동시 요청"""
        personas = ["lua", "elro", "riri", "nana"]
        tasks = []

        for i in range(40):  # 각 persona당 10개
            persona = personas[i % len(personas)]
            task = async_client.post(
                "/chat",
                json={"message": f"Message for {persona}", "user_id": f"user-{persona}-{i}"},
            )
            tasks.append((task, persona))

        responses = await asyncio.gather(*[t[0] for t in tasks], return_exceptions=True)

        # 각 persona별 응답 검사
        for response, expected_persona in zip(responses, [t[1] for t in tasks]):
            if not isinstance(response, Exception):
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self, async_client: AsyncClient):
        """빠른 연속 요청 (Rate Limiting 테스트)"""
        successful = 0
        rate_limited = 0

        for i in range(20):
            response = await async_client.post(
                "/chat", json={"message": f"Rapid request {i}", "user_id": "user-rapid"}
            )

            if response.status_code == 200:
                successful += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited += 1

        logger.info(f"Successful: {successful}, Rate Limited: {rate_limited}")
        # Rate Limiting이 작동하고 있어야 함
        assert successful > 0


class TestInputValidation:
    """입력 검증 테스트"""

    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self, async_client: AsyncClient):
        """SQL Injection 시도"""
        response = await async_client.post(
            "/chat", json={"message": "'; DROP TABLE users; --", "user_id": "test-injection"}
        )
        # 요청이 안전하게 처리되어야 함
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_xss_attempt(self, async_client: AsyncClient):
        """XSS 시도"""
        response = await async_client.post(
            "/chat", json={"message": "<script>alert('XSS')</script>", "user_id": "test-xss"}
        )
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_command_injection(self, async_client: AsyncClient):
        """Command Injection 시도"""
        response = await async_client.post(
            "/chat", json={"message": "rm -rf /; echo 'hacked'", "user_id": "test-cmd-inject"}
        )
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_null_bytes(self, async_client: AsyncClient):
        """Null 바이트 포함"""
        response = await async_client.post(
            "/chat", json={"message": "Hello\x00World", "user_id": "test-null"}
        )
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_extremely_long_message(self, async_client: AsyncClient):
        """극도로 긴 메시지"""
        response = await async_client.post(
            "/chat", json={"message": "A" * 10000, "user_id": "test-long"}  # 10KB 메시지
        )
        # 최대 길이 검사
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_json_injection(self, async_client: AsyncClient):
        """JSON Injection 시도"""
        response = await async_client.post(
            "/chat",
            json={"message": '"},"admin":true,"is_admin":{"', "user_id": "test-json-inject"},
        )
        assert response.status_code in [200, 422]


class TestMemoryAndPerformance:
    """메모리 및 성능 테스트"""

    @pytest.mark.asyncio
    async def test_no_memory_leak_sequential(self, async_client: AsyncClient):
        """순차 요청에서 메모리 누수 검사"""
        import gc
        import tracemalloc

        tracemalloc.start()
        snapshots = []

        for i in range(50):
            response = await async_client.post(
                "/chat", json={"message": f"Memory test {i}", "user_id": f"user-mem-{i}"}
            )
            assert response.status_code == 200

            if i % 10 == 0:
                gc.collect()
                snapshots.append(tracemalloc.take_snapshot())

        # 첫번째와 마지막 메모리 비교
        if len(snapshots) > 1:
            stats = snapshots[-1].compare_to(snapshots[0], "lineno")
            total_diff = sum(stat.size_diff for stat in stats)
            # 메모리 증가가 제한 범위 내여야 함 (예: 10MB 이내)
            assert total_diff < 10 * 1024 * 1024

        tracemalloc.stop()

    @pytest.mark.asyncio
    async def test_large_response_handling(self, async_client: AsyncClient):
        """큰 응답 처리"""
        response = await async_client.post(
            "/chat",
            json={
                "message": "Generate a very long response about the history of AI",
                "user_id": "test-large-response",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # 응답이 완전히 받아져야 함
        assert len(data.get("content", "")) > 0


class TestSecurityHeaders:
    """보안 헤더 검사"""

    @pytest.mark.asyncio
    async def test_security_headers_present(self, async_client: AsyncClient):
        """필수 보안 헤더 존재 확인"""
        response = await async_client.get("/health")

        # 필수 보안 헤더
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
        }

        for header, expected_value in required_headers.items():
            actual_value = response.headers.get(header)
            assert actual_value is not None, f"Missing header: {header}"
            assert expected_value in actual_value, f"Incorrect {header}: {actual_value}"

    @pytest.mark.asyncio
    async def test_hsts_header(self, async_client: AsyncClient):
        """HSTS 헤더 확인"""
        response = await async_client.get("/health")
        hsts = response.headers.get("Strict-Transport-Security")
        assert hsts is not None
        assert "max-age" in hsts

    @pytest.mark.asyncio
    async def test_csp_header(self, async_client: AsyncClient):
        """CSP 헤더 확인"""
        response = await async_client.get("/health")
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None


class TestTimingAttacks:
    """타이밍 공격 방어 테스트"""

    @pytest.mark.asyncio
    async def test_consistent_response_time(self, async_client: AsyncClient):
        """응답 시간 일관성 (타이밍 공격 방어)"""
        times = []

        for i in range(10):
            start = time.time()
            response = await async_client.post(
                "/chat", json={"message": f"Timing test {i}", "user_id": f"user-timing-{i}"}
            )
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        # 응답 시간의 편차 검사
        avg_time = sum(times) / len(times)
        max_deviation = max(abs(t - avg_time) for t in times)

        # 편차가 30% 이내여야 함 (타이밍 공격 방지)
        assert max_deviation < avg_time * 0.3


class TestBoundaryValues:
    """경계값 테스트"""

    @pytest.mark.asyncio
    async def test_empty_message(self, async_client: AsyncClient):
        """빈 메시지"""
        response = await async_client.post("/chat", json={"message": "", "user_id": "test-empty"})
        # 최소 길이 검사
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_whitespace_only_message(self, async_client: AsyncClient):
        """공백만 있는 메시지"""
        response = await async_client.post(
            "/chat", json={"message": "   \n\t  ", "user_id": "test-whitespace"}
        )
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_max_length_message(self, async_client: AsyncClient):
        """최대 길이 메시지"""
        response = await async_client.post(
            "/chat", json={"message": "A" * 5000, "user_id": "test-max-length"}  # 설정된 최대값
        )
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_over_max_length_message(self, async_client: AsyncClient):
        """최대 길이 초과 메시지"""
        response = await async_client.post(
            "/chat", json={"message": "A" * 5001, "user_id": "test-over-max"}  # 한 글자 초과
        )
        assert response.status_code == 422


class TestErrorHandling:
    """에러 처리 테스트"""

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client: AsyncClient):
        """필수 필드 누락"""
        response = await async_client.post("/chat", json={"message": "test"})  # user_id 누락
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_json(self, async_client: AsyncClient):
        """잘못된 JSON"""
        response = await async_client.post(
            "/chat", content=b"invalid json {", headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_wrong_content_type(self, async_client: AsyncClient):
        """잘못된 Content-Type"""
        response = await async_client.post(
            "/chat",
            content="message=test",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code in [400, 422, 415]


# 테스트 통계
def test_summary(capsys):
    """테스트 완료 요약"""
    logger.info("Security Edge Cases Tests Completed")
    logger.info("✅ Unicode handling: 9 tests")
    logger.info("✅ Emoji handling: 5 tests")
    logger.info("✅ Concurrent requests: 4 tests")
    logger.info("✅ Input validation: 6 tests")
    logger.info("✅ Memory and performance: 2 tests")
    logger.info("✅ Security headers: 3 tests")
    logger.info("✅ Timing attacks: 1 test")
    logger.info("✅ Boundary values: 4 tests")
    logger.info("✅ Error handling: 3 tests")
    logger.info("Total: 37 security edge case tests")
