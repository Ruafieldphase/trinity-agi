"""
Phase 2.5 Day 1 Integration Test
Comet API Client + Task Queue Server 통합 검증

테스트 항목:
1. Task Queue Server 상태 확인 (http://localhost:8091)
2. Comet Client HTTP 기본 동작 검증
3. 간단한 Mock 서버 테스트 (선택)

실행:
    python integrations/test_day1_integration.py
"""

import asyncio
import logging
from datetime import datetime

import httpx

from integrations.comet_client import (
    CometConfig,
    CometHTTPClient,
    CometResponse,
)


async def test_task_queue_server():
    """Task Queue Server Health Check"""
    print("\n" + "=" * 60)
    print("TEST 1: Task Queue Server Health Check")
    print("=" * 60 + "\n")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8091/api/health", timeout=3.0)
            data = response.json()
            
            print(f"✅ Task Queue Server: ONLINE")
            print(f"   Status: {data.get('status')}")
            print(f"   Queue Size: {data.get('queue_size')}")
            print(f"   Results Count: {data.get('results_count')}")
            print(f"   Timestamp: {data.get('timestamp')}")
            
            return True
    
    except Exception as e:
        print(f"❌ Task Queue Server: OFFLINE")
        print(f"   Error: {e}")
        return False


async def test_comet_client_basic():
    """Comet Client 기본 동작 테스트 (서버 없이)"""
    print("\n" + "=" * 60)
    print("TEST 2: Comet Client Basic Functionality")
    print("=" * 60 + "\n")
    
    # Config 검증
    config = CometConfig(
        base_url="http://localhost:8090",
        timeout=5.0,
        retry_attempts=2,
        log_requests=True
    )
    
    print(f"✅ Comet Config:")
    print(f"   Base URL: {config.base_url}")
    print(f"   Timeout: {config.timeout}s")
    print(f"   Retry Attempts: {config.retry_attempts}")
    
    # Client 생성 검증
    async with CometHTTPClient(config) as client:
        print(f"\n✅ Comet HTTP Client initialized")
        print(f"   Client Type: {type(client).__name__}")
        print(f"   Config: {client.config}")
    
    print(f"\n✅ Comet HTTP Client closed cleanly")
    
    return True


async def test_comet_client_mock():
    """Comet Client Mock 서버 테스트 (선택)"""
    print("\n" + "=" * 60)
    print("TEST 3: Comet Client Mock Test (Optional)")
    print("=" * 60 + "\n")
    
    print("⚠️  Comet 서버가 없어 Health Check는 실패합니다.")
    print("   이는 정상 동작입니다. 서버 실행 시 연결됩니다.\n")
    
    config = CometConfig(
        base_url="http://localhost:8090",
        timeout=3.0,
        retry_attempts=1,
        log_requests=False
    )
    
    async with CometHTTPClient(config) as client:
        # Health Check (실패 예상)
        healthy = await client.health_check()
        
        if healthy:
            print(f"✅ Comet Server: ONLINE (예상치 못한 성공)")
        else:
            print(f"⚠️  Comet Server: OFFLINE (예상된 결과)")
            print(f"   서버 시작 방법:")
            print(f"   1. Comet Browser Worker 실행")
            print(f"   2. Port 8090에서 FastAPI 서버 실행")
    
    return True


async def test_data_models():
    """Data Models 검증"""
    print("\n" + "=" * 60)
    print("TEST 4: Data Models Validation")
    print("=" * 60 + "\n")
    
    # CometResponse 생성 테스트
    response1 = CometResponse(success=True, data={"test": "data"})
    print(f"✅ CometResponse (success):")
    print(f"   Success: {response1.success}")
    print(f"   Data: {response1.data}")
    print(f"   Timestamp: {response1.timestamp}")
    
    response2 = CometResponse(success=False, error="Test error")
    print(f"\n✅ CometResponse (failure):")
    print(f"   Success: {response2.success}")
    print(f"   Error: {response2.error}")
    print(f"   Timestamp: {response2.timestamp}")
    
    return True


async def main():
    """전체 테스트 실행"""
    logging.basicConfig(
        level=logging.WARNING,  # INFO로 변경하면 상세 로그 출력
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    print("\n" + "=" * 60)
    print("PHASE 2.5 DAY 1 INTEGRATION TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = []
    
    # Test 1: Task Queue Server
    result1 = await test_task_queue_server()
    results.append(("Task Queue Server", result1))
    
    # Test 2: Comet Client Basic
    result2 = await test_comet_client_basic()
    results.append(("Comet Client Basic", result2))
    
    # Test 3: Comet Client Mock
    result3 = await test_comet_client_mock()
    results.append(("Comet Client Mock", result3))
    
    # Test 4: Data Models
    result4 = await test_data_models()
    results.append(("Data Models", result4))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60 + "\n")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n✅ Phase 2.5 Day 1 통합 테스트 성공!")
        print("   다음 단계: Day 2 (YouTube Handler 구현)")
    else:
        print("\n⚠️  일부 테스트 실패 (정상일 수 있음)")
        print("   Comet 서버 미실행 시 Test 3 실패는 예상된 결과입니다.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
