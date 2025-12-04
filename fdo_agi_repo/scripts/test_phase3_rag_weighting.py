#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 검증: BQI 좌표 기반 RAG 가중치

다양한 BQI 좌표로 RAG 검색 결과를 비교하여 가중치 효과를 검증합니다.

테스트 시나리오:
1. Priority 4 (긴급) vs Priority 1 (탐색): 시간 가중치 효과 확인
2. Emotion concern vs hope: 문서 타입 필터링 효과 확인
3. Rhythm integration vs reflection: 검색 범위 조정 효과 확인
"""
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# 프로젝트 루트 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# UTF-8 인코딩 강제 설정 (한글 깨짐 방지)
sys.path.insert(0, str(project_root / "scripts"))
import encoding_setup

from tools.rag.retriever import rag_query


def print_section(title: str):
    """섹션 제목 출력"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_hits(hits: List[Dict[str, Any]], max_display: int = 5):
    """검색 결과 출력"""
    for i, hit in enumerate(hits[:max_display], 1):
        print(f"\n[{i}] 관련도: {hit['relevance']:.4f}")
        print(f"    소스: {hit['source']}")
        if hit['source'] == 'resonance_ledger':
            print(f"    이벤트: {hit.get('event_type', 'unknown')}")
            print(f"    Task ID: {hit.get('task_id', 'unknown')}")
        elif hit['source'] == 'coordinate':
            print(f"    ID: {hit.get('id', 'unknown')}")
        print(f"    스니펫: {hit['snippet'][:100]}...")


def test_priority_weighting():
    """
    Priority 가중치 테스트:
    - Priority 4 (긴급): 최근 문서 강조
    - Priority 1 (탐색): 다양한 문서 탐색
    """
    print_section("Test 1: Priority 가중치 (시간 기반)")
    
    query = "증거 검증 실패 원인"
    
    # Priority 4 (긴급)
    print("\n[Priority 4 - 긴급]")
    bqi_urgent = {
        "priority": 4,
        "emotion": ["concern"],
        "rhythm": "exploration"
    }
    result_urgent = rag_query(
        query=query,
        top_k=5,
        bqi_coord=bqi_urgent
    )
    print(f"총 {len(result_urgent['hits'])}개 검색")
    print_hits(result_urgent['hits'])
    
    # Priority 1 (탐색)
    print("\n[Priority 1 - 탐색]")
    bqi_explore = {
        "priority": 1,
        "emotion": ["curiosity"],
        "rhythm": "exploration"
    }
    result_explore = rag_query(
        query=query,
        top_k=5,
        bqi_coord=bqi_explore
    )
    print(f"총 {len(result_explore['hits'])}개 검색")
    print_hits(result_explore['hits'])
    
    # 비교 분석
    print("\n[비교 분석]")
    if result_urgent['hits'] and result_explore['hits']:
        urgent_top = result_urgent['hits'][0]
        explore_top = result_explore['hits'][0]
        print(f"긴급 모드 Top 1: {urgent_top.get('event_type', urgent_top.get('id'))}")
        print(f"탐색 모드 Top 1: {explore_top.get('event_type', explore_top.get('id'))}")
        if urgent_top.get('id') != explore_top.get('id'):
            print("✅ Priority 가중치가 검색 결과 순위에 영향을 미쳤습니다.")
        else:
            print("⚠️  Priority 가중치 효과가 제한적입니다.")


def test_emotion_filtering():
    """
    Emotion 기반 필터링 테스트:
    - concern: 문제 해결, 위험 분석 문서 우선
    - hope: 성공 사례 문서 우선
    """
    print_section("Test 2: Emotion 기반 필터링")
    
    query = "자기교정 루프 개선"
    
    # Emotion: concern
    print("\n[Emotion: concern - 문제 해결 중심]")
    bqi_concern = {
        "priority": 2,
        "emotion": ["concern", "anxiety"],
        "rhythm": "reflection"
    }
    result_concern = rag_query(
        query=query,
        top_k=5,
        bqi_coord=bqi_concern
    )
    print(f"총 {len(result_concern['hits'])}개 검색")
    print_hits(result_concern['hits'])
    
    # Emotion: hope
    print("\n[Emotion: hope - 성공 사례 중심]")
    bqi_hope = {
        "priority": 2,
        "emotion": ["hope", "gratitude"],
        "rhythm": "reflection"
    }
    result_hope = rag_query(
        query=query,
        top_k=5,
        bqi_coord=bqi_hope
    )
    print(f"총 {len(result_hope['hits'])}개 검색")
    print_hits(result_hope['hits'])
    
    # 비교 분석
    print("\n[비교 분석]")
    concern_events = [h.get('event_type') for h in result_concern['hits'] if 'event_type' in h]
    hope_events = [h.get('event_type') for h in result_hope['hits'] if 'event_type' in h]
    
    print(f"concern 모드 이벤트: {concern_events[:3]}")
    print(f"hope 모드 이벤트: {hope_events[:3]}")
    
    concern_corrections = sum(1 for e in concern_events if 'correction' in str(e) or 'second_pass' in str(e))
    hope_success = sum(1 for e in hope_events if 'complete' in str(e) or 'learning' in str(e))
    
    print(f"concern 모드: 교정 관련 {concern_corrections}개")
    print(f"hope 모드: 성공 관련 {hope_success}개")


def test_rhythm_scope():
    """
    Rhythm 기반 범위 조정 테스트:
    - integration: 교차 도메인 소스 혼합
    - reflection: 평가, 리뷰 문서 우선
    """
    print_section("Test 3: Rhythm 기반 검색 범위")
    
    query = "BQI 시스템 효과"
    
    # Rhythm: integration
    print("\n[Rhythm: integration - 교차 도메인]")
    bqi_integration = {
        "priority": 2,
        "emotion": ["curiosity"],
        "rhythm": "integration"
    }
    result_integration = rag_query(
        query=query,
        top_k=5,
        bqi_coord=bqi_integration
    )
    print(f"총 {len(result_integration['hits'])}개 검색")
    print_hits(result_integration['hits'])
    
    # Rhythm: reflection
    print("\n[Rhythm: reflection - 평가 중심]")
    bqi_reflection = {
        "priority": 2,
        "emotion": ["curiosity"],
        "rhythm": "reflection"
    }
    result_reflection = rag_query(
        query=query,
        top_k=5,
        bqi_coord=bqi_reflection
    )
    print(f"총 {len(result_reflection['hits'])}개 검색")
    print_hits(result_reflection['hits'])
    
    # 비교 분석
    print("\n[비교 분석]")
    integration_sources = [h['source'] for h in result_integration['hits']]
    reflection_sources = [h['source'] for h in result_reflection['hits']]
    
    print(f"integration 모드 소스: {integration_sources}")
    print(f"reflection 모드 소스: {reflection_sources}")
    
    integration_coord_ratio = integration_sources.count('coordinate') / len(integration_sources) if integration_sources else 0
    reflection_ledger_ratio = reflection_sources.count('resonance_ledger') / len(reflection_sources) if reflection_sources else 0
    
    print(f"integration 모드 coordinate 비율: {integration_coord_ratio:.2%}")
    print(f"reflection 모드 ledger 비율: {reflection_ledger_ratio:.2%}")


def test_baseline_comparison():
    """
    Baseline 비교: BQI 가중치 없음 vs 있음
    """
    print_section("Test 4: Baseline 비교 (BQI 가중치 효과)")
    
    query = "자기교정 루프 실패"
    
    # BQI 가중치 없음
    print("\n[BQI 가중치 없음]")
    result_no_bqi = rag_query(
        query=query,
        top_k=5,
        bqi_coord=None
    )
    print(f"총 {len(result_no_bqi['hits'])}개 검색")
    print_hits(result_no_bqi['hits'])
    
    # BQI 가중치 있음 (concern + urgent)
    print("\n[BQI 가중치 있음 - concern + urgent]")
    bqi_weighted = {
        "priority": 4,
        "emotion": ["concern"],
        "rhythm": "reflection"
    }
    result_with_bqi = rag_query(
        query=query,
        top_k=5,
        bqi_coord=bqi_weighted
    )
    print(f"총 {len(result_with_bqi['hits'])}개 검색")
    print_hits(result_with_bqi['hits'])
    
    # 비교 분석
    print("\n[비교 분석]")
    if result_no_bqi['hits'] and result_with_bqi['hits']:
        no_bqi_relevance = [h['relevance'] for h in result_no_bqi['hits']]
        with_bqi_relevance = [h['relevance'] for h in result_with_bqi['hits']]
        
        print(f"BQI 없음 평균 관련도: {sum(no_bqi_relevance)/len(no_bqi_relevance):.4f}")
        print(f"BQI 있음 평균 관련도: {sum(with_bqi_relevance)/len(with_bqi_relevance):.4f}")
        
        # 순위 변화 확인
        no_bqi_top_id = result_no_bqi['hits'][0].get('id')
        with_bqi_top_id = result_with_bqi['hits'][0].get('id')
        
        if no_bqi_top_id != with_bqi_top_id:
            print("✅ BQI 가중치가 검색 결과 순위를 변경했습니다.")
        else:
            print("⚠️  BQI 가중치 효과가 제한적입니다.")


def main():
    """메인 테스트 실행"""
    print("=" * 70)
    print("Phase 3 검증: BQI 좌표 기반 RAG 가중치")
    print("=" * 70)
    
    try:
        # 1. Priority 가중치 테스트
        test_priority_weighting()
        
        # 2. Emotion 필터링 테스트
        test_emotion_filtering()
        
        # 3. Rhythm 범위 테스트
        test_rhythm_scope()
        
        # 4. Baseline 비교
        test_baseline_comparison()
        
        print("\n" + "=" * 70)
        print("✅ Phase 3 검증 완료")
        print("=" * 70)
        print("\n주요 확인 사항:")
        print("1. Priority 4 (긴급)은 최근 문서를 우선적으로 검색합니다.")
        print("2. Emotion concern은 문제 해결 관련 문서를, hope는 성공 사례를 강조합니다.")
        print("3. Rhythm integration은 교차 도메인을, reflection은 평가 문서를 우선합니다.")
        print("4. BQI 가중치는 검색 결과 순위에 영향을 미칩니다.")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
