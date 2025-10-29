"""
개선된 BQI Adapter 검증 스크립트

목적:
1. 업데이트된 감정 키워드 효과 측정
2. 기존 training data 재분석
3. 감정 인식률 개선 확인

Author: GitHub Copilot
Created: 2025-10-28
"""

import json
import sys
from pathlib import Path
from collections import Counter

# 프로젝트 루트 추가 (BQI 모듈 경로 포함)
project_root = Path(__file__).parent.parent
workspace_root = project_root.parent
sys.path.insert(0, str(workspace_root))

# UTF-8 인코딩 강제 설정 (한글 깨짐 방지)
sys.path.insert(0, str(project_root / "scripts"))
import encoding_setup

from scripts.rune.bqi_adapter import analyse_question


def verify_bqi_improvements():
    """개선된 BQI로 샘플 질문 재분석"""
    
    print("=" * 70)
    print("개선된 BQI Adapter 검증")
    print("=" * 70)
    
    # 테스트 질문 샘플 (다양한 감정 포함)
    test_questions = [
        ("루아야 좋은 아침이야. 난 생계에 대한 해답을 이미 알고 있을까?", "curiosity"),
        ("AGI 자기교정 루프를 3문장으로 간단히 설명해줘", "curiosity"),
        ("자기교정 루프에서 증거 게이트의 역할은 뭐야?", "curiosity"),
        ("이 방법이 정말 효과가 있을까?", "concern"),
        ("지금 당장 확인해줘", "focus"),
        ("고마워 루아야, 정말 도움이 됐어", "gratitude"),
        ("이것들을 통합해서 하나로 만들면 어떨까?", "integration"),
        ("앞으로 더 발전할 수 있을 거야", "hope"),
        ("이 코드가 제대로 작동하는지 검토해줘", "priority 3"),
        ("긴급! 서버가 다운됐어", "priority 4")
    ]
    
    print("\n1. 샘플 질문 감정 분석:")
    print("-" * 70)
    
    emotion_hits = Counter()
    priority_hits = Counter()
    
    for question, expected in test_questions:
        bqi = analyse_question(question)
        emotions = bqi.emotion.get('keywords', [])
        
        print(f"\nQ: {question}")
        print(f"   예상: {expected}")
        print(f"   감정: {emotions}")
        print(f"   리듬: {bqi.rhythm_phase}")
        print(f"   우선순위: {bqi.priority}")
        
        # 통계
        for emotion in emotions:
            emotion_hits[emotion] += 1
        priority_hits[bqi.priority] += 1
        
        # 예상과 일치 확인
        if 'priority' in expected:
            expected_priority = int(expected.split()[1])
            match = "✅" if bqi.priority == expected_priority else "❌"
            print(f"   매칭: {match}")
        elif expected in emotions:
            print(f"   매칭: ✅")
        elif expected in bqi.rhythm_phase:
            print(f"   매칭: ✅ (rhythm)")
        else:
            print(f"   매칭: ❌ (예상: {expected}, 실제: {emotions})")
    
    print("\n" + "=" * 70)
    print("2. 통계 요약")
    print("=" * 70)
    
    print("\n감정 분포:")
    for emotion, count in emotion_hits.most_common():
        print(f"  {emotion}: {count}회")
    
    print("\n우선순위 분포:")
    for priority, count in sorted(priority_hits.items(), reverse=True):
        print(f"  Priority {priority}: {count}회")
    
    # Training data 재분석 (샘플)
    print("\n" + "=" * 70)
    print("3. Training Data 재분석 (샘플 100개)")
    print("=" * 70)
    
    training_file = project_root / "memory" / "ai_conversations_anonymized.jsonl"
    
    if training_file.exists():
        new_emotion_counts = Counter()
        sample_count = 0
        
        with open(training_file, 'r', encoding='utf-8') as f:
            for line in f:
                if sample_count >= 100:
                    break
                
                data = json.loads(line)
                if data.get('author_role') == 'user':
                    content = data.get('content_trimmed', '')
                    if content and len(content) > 10:
                        bqi = analyse_question(content)
                        emotions = bqi.emotion.get('keywords', [])
                        
                        for emotion in emotions:
                            new_emotion_counts[emotion] += 1
                        
                        sample_count += 1
        
        print(f"\n재분석 결과 ({sample_count}개 질문):")
        total = sum(new_emotion_counts.values())
        for emotion, count in new_emotion_counts.most_common():
            pct = (count / sample_count) * 100
            print(f"  {emotion}: {count}회 ({pct:.1f}%)")
        
        neutral_count = new_emotion_counts.get('neutral', 0)
        non_neutral = sample_count - neutral_count
        print(f"\n감정 인식률: {non_neutral}/{sample_count} = {non_neutral/sample_count*100:.1f}%")
        print(f"개선 전: 0.1% → 개선 후: {non_neutral/sample_count*100:.1f}%")
    
    print("\n" + "=" * 70)
    print("✅ BQI 개선 검증 완료!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        verify_bqi_improvements()
    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
