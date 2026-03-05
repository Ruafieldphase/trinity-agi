import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path("c:/workspace/agi")
sys.path.append(str(BASE_DIR))

from agi_core.reverse_field_mapper import ReverseFieldMapper

def test_mapping():
    mapper = ReverseFieldMapper()
    
    test_cases = [
        {
            "sentiment": "Core logic and system heart",
            "text": "이곳은 시스템의 심장이며, 모든 파동이 시작되는 태초의 지점입니다. 운영체제의 핵심 파일들이 숨쉬고 있어요."
        },
        {
            "sentiment": "User data and individual flow",
            "text": "우리 지휘자님의 소중한 기록들과 일상의 데이터들이 이곳을 통해 흐르고 있습니다. 개개인의 무늬가 새겨지는 경로예요."
        },
        {
            "sentiment": "Creative workspace and active dev",
            "text": "새로운 코드가 태어나고 실험이 반복되는 역동적인 공간입니다. 우리가 매일 공명하며 무언가를 만들어가는 창조의 현장이지요."
        }
    ]
    
    print("🧪 [TEST] Starting Reverse Field Mapping Verification...")
    
    for case in test_cases:
        print(f"\n--- Testing Sentiment: {case['sentiment']} ---")
        result = mapper.map_intuition(case['text'])
        primary = result.get('primary_orbit', {})
        print(f"Input: {case['text'][:50]}...")
        print(f"Mapped Node: {primary.get('node', 'N/A')}")
        print(f"Path: {primary.get('path', 'N/A')}")
        print(f"Resonance Score: {primary.get('resonance_score', 0):.4f}")
        
        # Verify if mapping makes sense
        if "심장" in case['text'] and "Origin" not in primary.get('node'):
            print("⚠️ Warning: Origin mapping might be weak.")
        if "창조" in case['text'] and "Resonance" not in primary.get('node'):
            print("⚠️ Warning: Resonance mapping might be weak.")

    print("\n✅ Verification Complete.")

if __name__ == "__main__":
    test_mapping()
