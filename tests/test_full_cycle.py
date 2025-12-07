"""
Full Cycle Integration Test
고불안도 시뮬레이션으로 Trinity → Shion → External AI 흐름 테스트
"""
import sys
sys.path.insert(0, "c:/workspace/agi")

from services.front_engine import UnifiedFrontEngine

def test_high_anxiety_flow():
    print("=" * 60)
    print("Full Cycle Integration Test")
    print("고불안도 시뮬레이션")
    print("=" * 60)
    
    engine = UnifiedFrontEngine()
    
    # 불안도 체크 메서드를 오버라이드해서 고불안도 시뮬레이션
    original_check = engine._check_background_self_anxiety
    engine._check_background_self_anxiety = lambda: 0.85  # 고불안도!
    
    print("\n[1] 불안도를 0.85로 시뮬레이션")
    print("[2] 입력 처리 시작...")
    
    input("\nEnter를 누르면 테스트 시작 (ChatGPT가 열릴 수 있음)...")
    
    result = engine.process("도움이 필요해. 현재 막힌 상황이야.")
    
    print("\n" + "=" * 60)
    print("결과:")
    print("=" * 60)
    print(f"Branch History: {result['branch_history']}")
    print(f"External Guidance: {result['action'].get('external_guidance', 'None')[:200] if result['action'].get('external_guidance') else 'None'}...")
    print(f"Selected Model: {result['action'].get('selected_model', 'N/A')}")
    
    # 원래 메서드 복원
    engine._check_background_self_anxiety = original_check

if __name__ == "__main__":
    test_high_anxiety_flow()
