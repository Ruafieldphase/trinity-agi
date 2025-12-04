#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Program Learning Agent 테스트 스크립트
빠른 검증을 위한 통합 테스트
"""

import sys
import os

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fdo_agi_repo'))

from program_learning_agent import ProgramLearningAgent
import json

def test_metadata_extraction():
    """메타데이터 추출 테스트"""
    print("\n=== 메타데이터 추출 테스트 ===")
    
    agent = ProgramLearningAgent()
    metadata = agent.extract_metadata("notepad.exe")
    
    print(f"프로그램: {metadata['program']}")
    print(f"창 제목: {metadata['window_title']}")
    print(f"창 크기: {metadata['window_size']}")
    print(f"상태: {metadata['state']}")
    print(f"타임스탬프: {metadata['timestamp']}")
    
    return metadata.get('state') == 'active'

def test_pattern_learning():
    """패턴 학습 테스트"""
    print("\n=== 패턴 학습 테스트 ===")
    
    agent = ProgramLearningAgent()
    
    # 샘플 인터랙션
    sample_interactions = [
        {
            "program": "notepad.exe",
            "action": "open",
            "timestamp": "2025-11-10T10:00:00"
        },
        {
            "program": "notepad.exe", 
            "action": "type",
            "content": "Hello",
            "timestamp": "2025-11-10T10:00:05"
        },
        {
            "program": "notepad.exe",
            "action": "save",
            "timestamp": "2025-11-10T10:00:10"
        }
    ]
    
    for interaction in sample_interactions:
        agent.learn_pattern(interaction)
    
    patterns = agent.analyze_patterns("notepad.exe")
    print(f"\n학습된 패턴 수: {len(patterns)}")
    print(f"패턴 세부사항:")
    print(json.dumps(patterns, indent=2, ensure_ascii=False))
    
    return len(patterns) > 0

def test_cache_integration():
    """Sena 캐시 통합 테스트"""
    print("\n=== Sena 캐시 통합 테스트 ===")
    
    agent = ProgramLearningAgent()
    
    test_data = {
        "program": "vscode.exe",
        "learned_patterns": ["open_file", "edit", "save"],
        "success_rate": 0.85
    }
    
    # 캐시 저장
    cache_key = agent.save_to_cache(test_data)
    print(f"캐시 키: {cache_key}")
    
    # 캐시 조회
    cached = agent.load_from_cache(cache_key)
    
    if cached:
        print(f"캐시 조회 성공:")
        print(json.dumps(cached, indent=2, ensure_ascii=False))
        return True
    else:
        print("⚠️ 캐시 조회 실패")
        return False

def run_all_tests():
    """모든 테스트 실행"""
    print("🧪 Program Learning Agent 통합 테스트 시작\n")
    
    results = {
        "metadata_extraction": False,
        "pattern_learning": False,
        "cache_integration": False
    }
    
    try:
        results["metadata_extraction"] = test_metadata_extraction()
    except Exception as e:
        print(f"❌ 메타데이터 추출 실패: {e}")
    
    try:
        results["pattern_learning"] = test_pattern_learning()
    except Exception as e:
        print(f"❌ 패턴 학습 실패: {e}")
    
    try:
        results["cache_integration"] = test_cache_integration()
    except Exception as e:
        print(f"❌ 캐시 통합 실패: {e}")
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n통과율: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️ {total - passed}개 테스트 실패")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
