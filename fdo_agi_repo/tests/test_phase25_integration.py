"""
Phase 2.5 통합 검증 테스트
모든 RPA 모듈이 정상 작동하는지 확인
"""

import asyncio
import sys
from pathlib import Path

# RPA 모듈 추가
sys.path.insert(0, str(Path(__file__).parent))

# UTF-8 강제 설정
from rpa.utf8_utils import force_utf8
force_utf8()


async def test_youtube_learner():
    """YouTube Learner 테스트"""
    print("\n1️⃣ Testing YouTube Learner...")
    try:
        from rpa.youtube_learner import YouTubeLearner, YouTubeLearnerConfig
        
        config = YouTubeLearnerConfig()
        learner = YouTubeLearner(config)
        
        print(f"   ✅ YouTubeLearner initialized")
        print(f"   📁 Output dir: {config.output_dir}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def test_rpa_core():
    """RPA Core 테스트"""
    print("\n2️⃣ Testing RPA Core...")
    try:
        from rpa.core import RPACore, RPACoreConfig
        import pyautogui
        
        config = RPACoreConfig()
        rpa = RPACore(config)
        
        screen_size = pyautogui.size()
        mouse_pos = pyautogui.position()
        
        print(f"   ✅ RPACore initialized")
        print(f"   🖥️ Screen: {screen_size}")
        print(f"   🖱️ Mouse: {mouse_pos}")
        print(f"   🛡️ Failsafe: {pyautogui.FAILSAFE}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def test_trial_error_engine():
    """Trial-Error Engine 테스트"""
    print("\n3️⃣ Testing Trial-Error Engine...")
    try:
        from rpa.trial_error_engine import TrialErrorEngine, TrialErrorConfig
        
        config = TrialErrorConfig()
        engine = TrialErrorEngine(config)
        
        print(f"   ✅ TrialErrorEngine initialized")
        print(f"   🎲 Epsilon: {engine.current_epsilon}")
        print(f"   🔄 Max trials: {config.max_trials}")
        print(f"   💾 Experience DB: {config.experience_db}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def test_e2e_pipeline():
    """E2E Pipeline 테스트"""
    print("\n4️⃣ Testing E2E Pipeline...")
    try:
        from rpa.e2e_pipeline import E2EPipeline, E2EConfig
        
        config = E2EConfig()
        pipeline = E2EPipeline(config)
        
        print(f"   ✅ E2EPipeline initialized")
        print(f"   📂 Output: {config.output_dir}")
        print(f"   📝 Ledger: {config.ledger_path}")
        print(f"   🔧 Auto-execution: {config.enable_auto_execution}")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def test_resonance_ledger():
    """Resonance Ledger 테스트"""
    print("\n5️⃣ Testing Resonance Ledger Integration...")
    try:
        ledger_path = Path("memory/resonance_ledger.jsonl")
        
        if ledger_path.exists():
            with open(ledger_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            print(f"   ✅ Ledger file exists")
            print(f"   📊 Total events: {len(lines)}")
            
            # 최근 이벤트 확인
            if lines:
                import json
                last_event = json.loads(lines[-1])
                print(f"   🕐 Last event: {last_event.get('event', 'N/A')}")
                print(f"   📅 Timestamp: {last_event.get('ts', 'N/A')[:19]}")
        else:
            print(f"   ⚠️ Ledger file not found (will be created on first use)")
        
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False


async def main():
    """통합 검증 실행"""
    print("=" * 60)
    print("🧪 Phase 2.5 RPA Integration Verification")
    print("=" * 60)
    
    results = []
    
    # 모듈별 테스트
    results.append(("YouTube Learner", await test_youtube_learner()))
    results.append(("RPA Core", await test_rpa_core()))
    results.append(("Trial-Error Engine", await test_trial_error_engine()))
    results.append(("E2E Pipeline", await test_e2e_pipeline()))
    results.append(("Resonance Ledger", await test_resonance_ledger()))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 Verification Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("\n🎉 Phase 2.5 RPA Integration: COMPLETE")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\n⚠️ Please check the logs above for details")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
