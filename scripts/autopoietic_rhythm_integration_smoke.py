"""
Autopoietic Rhythm Integration Smoke Test

실제 공명(resonance) 분석 구현과 연동하여 리듬 패턴 감지를 검증합니다.
- ResonanceConverter(LLM_Unified/ion-mentoring) import
- Rhythm 분석 PASS/FAIL
- 종료 코드 전파 (0=PASS, 1=FAIL)
"""
import sys
from pathlib import Path

# Import resonance converter from ion-mentoring
repo_root = Path(__file__).resolve().parents[1]
ion_mentoring = repo_root / "LLM_Unified" / "ion-mentoring"
sys.path.insert(0, str(ion_mentoring))

try:
    from resonance_converter import ResonanceConverter
except ImportError as e:
    print(f"FAIL: Cannot import ResonanceConverter: {e}")
    sys.exit(1)


def main():
    print("=" * 70)
    print("Autopoietic Rhythm Integration Smoke Test")
    print("=" * 70)
    
    # Initialize converter (offline mode)
    converter = ResonanceConverter(vertex_client=None)
    
    # Test 1: Fast-paced urgent rhythm
    print("\nTest 1: Fast-paced urgent rhythm detection")
    urgent_text = "뭐야! 안 돼! 왜?!"
    rhythm = converter.analyze_rhythm(urgent_text)
    
    assert rhythm.pace == 'fast', f"Expected fast pace, got: {rhythm.pace}"
    assert rhythm.exclamation_ratio > 0, "Expected exclamation_ratio > 0"
    print(f"  ✓ Fast rhythm detected: pace={rhythm.pace}, exclaim={rhythm.exclamation_ratio:.2f}")
    
    # Test 2: Slow contemplative rhythm
    print("\nTest 2: Slow contemplative rhythm detection")
    slow_text = "이 시스템의 아키텍처를 천천히 살펴보면, 여러 흥미로운 패턴들을 발견할 수 있습니다."
    rhythm = converter.analyze_rhythm(slow_text)
    
    assert rhythm.pace == 'slow', f"Expected slow pace, got: {rhythm.pace}"
    assert rhythm.avg_sentence_length > 10, "Expected avg_sentence_length > 10"
    print(f"  ✓ Slow rhythm detected: pace={rhythm.pace}, avg_len={rhythm.avg_sentence_length:.1f}")
    
    # Test 3: Question pattern rhythm
    print("\nTest 3: Question pattern rhythm detection")
    question_text = "이게 맞나요? 혹시 다른 방법은 없을까요?"
    rhythm = converter.analyze_rhythm(question_text)
    
    assert rhythm.question_ratio > 0, "Expected question_ratio > 0"
    print(f"  ✓ Question rhythm detected: questions={rhythm.question_ratio:.2f}")
    
    # Test 4: Full conversion (rhythm + emotion + key)
    print("\nTest 4: Full resonance conversion")
    result = converter.convert("이게 정말 동작하나요?")
    
    assert 'rhythm' in result, "Missing rhythm in conversion result"
    assert 'emotion' in result, "Missing emotion in conversion result"
    assert 'resonance_key' in result, "Missing resonance_key in conversion result"
    print(f"  ✓ Full conversion: key={result['resonance_key']}, emotion={result['emotion'].primary}")
    
    print("\n" + "=" * 70)
    print("PASS: All autopoietic rhythm integration tests passed.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except AssertionError as e:
        print(f"\nFAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
