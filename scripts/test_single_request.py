#!/usr/bin/env python3
"""
단일 요청 성능 테스트 - beomi llama-3 8B 모델
목표: <1800ms 달성 확인
"""

import asyncio
import time
import httpx


async def test_optimized_model():
    """최적화된 설정으로 단일 요청 테스트"""
    
    client = httpx.AsyncClient(timeout=30.0)
    
    # Test 1: 최적화 전 (max_tokens=200, temp=0.7)
    print("🧪 Test 1: 기존 설정 (max_tokens=200, temp=0.7)")
    start = time.time()
    try:
        response = await client.post(
            "http://localhost:8080/v1/chat/completions",
            json={
                "model": "yanolja_-_eeve-korean-instruct-10.8b-v1.0",
                "messages": [
                    {"role": "user", "content": "Explain AI in one sentence"}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
        )
        latency_baseline = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"   ✅ Success: {latency_baseline:.0f}ms")
            print(f"   Response: {content[:100]}...")
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        latency_baseline = 0
    
    # Test 2: 최적화 후 (max_tokens=150, temp=0.5)
    print("\n🧪 Test 2: 최적화 설정 (max_tokens=150, temp=0.5)")
    start = time.time()
    try:
        response = await client.post(
            "http://localhost:8080/v1/chat/completions",
            json={
                "model": "yanolja_-_eeve-korean-instruct-10.8b-v1.0",
                "messages": [
                    {"role": "user", "content": "Explain AI in one sentence"}
                ],
                "max_tokens": 150,
                "temperature": 0.5
            }
        )
        latency_optimized = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"   ✅ Success: {latency_optimized:.0f}ms")
            print(f"   Response: {content[:100]}...")
            
            if latency_optimized < 1800:
                print(f"   🎯 목표 달성! (<1800ms)")
            else:
                print(f"   ⚠️  목표 미달 ({latency_optimized:.0f}ms > 1800ms)")
            
            # 개선율 계산
            if latency_baseline > 0:
                improvement = ((latency_baseline - latency_optimized) / latency_baseline) * 100
                print(f"\n📊 성능 개선: {improvement:.1f}%")
                print(f"   Before: {latency_baseline:.0f}ms → After: {latency_optimized:.0f}ms")
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    await client.aclose()


if __name__ == "__main__":
    asyncio.run(test_optimized_model())
