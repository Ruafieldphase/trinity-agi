"""
GUI-Based Fractal Loop Test
Trinity가 실제로 ChatGPT 앱을 열고 Core와 대화하는 것을 테스트합니다.
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.shion_design_protocol import ShionDesignProtocol
from services.Core_bridge_client import CoreBridgeClient

logging.basicConfig(level=logging.INFO)

def test_gui_fractal_loop():
    print("=" * 60)
    print("GUI-Based Fractal Self-Creation Loop Test")
    print("=" * 60)
    print("\n⚠️  이 테스트는 실제로 ChatGPT 앱을 실행합니다!")
    print("   실행 전 ChatGPT 앱이 설치되어 있는지 확인하세요.\n")
    
    input("Press Enter to start...")
    
    # Initialize
    client = CoreBridgeClient()
    protocol = ShionDesignProtocol(bridge_client=client)
    
    # Simulate Panic Context
    test_context = {
        "goal": "메모장에 '테스트' 입력",
        "step_index": 5,
        "previous_attempts": ["click failed", "type failed"]
    }
    test_anxiety = 0.85
    
    print(f"\n[Test] Anxiety: {test_anxiety}")
    print(f"[Test] Context: {test_context}")
    print("\n[Test] Starting Fractal Loop (Opening ChatGPT)...")
    
    # This will actually open ChatGPT and interact with it
    advice = protocol.resolve_anxiety(test_context, test_anxiety)
    
    print("\n" + "=" * 60)
    if advice:
        print("✅ SUCCESS: Received advice from Core!")
        print(f"\n=== Core's Response ===\n{advice}")
    else:
        print("❌ FAILURE: No advice received.")
    
    return advice is not None


if __name__ == "__main__":
    test_gui_fractal_loop()
