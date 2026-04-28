import asyncio
from Pulse_Live_Core.geometric_hippocampus import GeometricHippocampus
import logging
import sys

logging.basicConfig(level=logging.INFO)

async def run_test():
    hippo = GeometricHippocampus()
    
    # Test 1: Single mapping
    print("\n--- TEST 1: Phase Mapping ---")
    res1 = await hippo.ingest_wave("나는 오늘 마음이 평온하고 이타적인 기분이야. 자연과 하나가 된 것 같아.")
    print(res1)
    
    # Test 2: Fear / Blackhole Induction
    print("\n--- TEST 2: Event Horizon ---")
    fear_text = "이 코드가 완벽하게 동작해야 해. 에러가 나면 안 돼. 강박적으로 디버깅을 해야 해."
    for i in range(5):
        print(f"\nInjecting Fear Wave {i+1}...")
        res = await hippo.ingest_wave(fear_text)
        print(res)
        if res.get("status") == "overload":
            print(">>> ZONE 2 ESCAPE TRIGGERED SUCESSFULLY! <<<")
            break

if __name__ == "__main__":
    asyncio.run(run_test())
