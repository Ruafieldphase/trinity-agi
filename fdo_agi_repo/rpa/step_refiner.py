"""
LLM-based Step Refinement
Phase 2.5 Week 2 Day 10

입력: Step Extractor의 원시 단계들
출력: LLM으로 정제된 핵심 실행 단계들

기능:
1. 중복 제거
2. 관련 단계 병합
3. 실행 가능한 형식으로 변환
4. Docker 설치 플로우 추출
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# TODO: LLM API 통합 (Phase 3)
# from openai import OpenAI


class StepRefiner:
    """LLM 기반 단계 정제기"""
    
    def __init__(self, llm_enabled: bool = False):
        self.llm_enabled = llm_enabled
        # self.client = OpenAI() if llm_enabled else None
    
    def refine_steps(self, steps: List[Dict[str, Any]], 
                     focus_keyword: str = "docker") -> List[Dict[str, Any]]:
        """단계 정제 메인 로직"""
        
        # 1. 키워드 필터링
        filtered = self._filter_by_keyword(steps, focus_keyword)
        print(f"📌 Keyword filtered: {len(steps)} → {len(filtered)}")
        
        # 2. 낮은 신뢰도 제거
        high_confidence = self._filter_by_confidence(filtered, min_confidence=0.5)
        print(f"🎯 High confidence: {len(filtered)} → {len(high_confidence)}")
        
        # 3. 시간 기반 그룹화 (30초 윈도우)
        grouped = self._group_by_time_window(high_confidence, window_seconds=30)
        print(f"📦 Time-grouped: {len(high_confidence)} → {len(grouped)} groups")
        
        # 4. 그룹별 대표 단계 선택
        representative = self._select_representative(grouped)
        print(f"⭐ Representative: {len(representative)} steps")
        
        # 5. LLM 정제 (선택적)
        if self.llm_enabled:
            refined = self._llm_refine(representative)
            print(f"🤖 LLM refined: {len(representative)} → {len(refined)}")
            return refined
        
        return representative
    
    def _filter_by_keyword(self, steps: List[Dict], keyword: str) -> List[Dict]:
        """키워드 기반 필터링"""
        return [
            s for s in steps 
            if keyword.lower() in s['description'].lower()
            or (s.get('target') and keyword.lower() in s['target'].lower())
        ]
    
    def _filter_by_confidence(self, steps: List[Dict], 
                              min_confidence: float) -> List[Dict]:
        """신뢰도 기반 필터링"""
        return [s for s in steps if s['confidence'] >= min_confidence]
    
    def _group_by_time_window(self, steps: List[Dict], 
                               window_seconds: float) -> List[List[Dict]]:
        """시간 윈도우 기반 그룹화"""
        if not steps:
            return []
        
        groups = []
        current_group = [steps[0]]
        
        for step in steps[1:]:
            if step['timestamp'] - current_group[0]['timestamp'] <= window_seconds:
                current_group.append(step)
            else:
                groups.append(current_group)
                current_group = [step]
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _select_representative(self, groups: List[List[Dict]]) -> List[Dict]:
        """각 그룹에서 대표 단계 선택"""
        representatives = []
        
        for group in groups:
            # 가장 신뢰도 높은 단계 선택
            best = max(group, key=lambda s: s['confidence'])
            
            # 그룹 정보 추가
            best['group_size'] = len(group)
            best['time_span'] = group[-1]['timestamp'] - group[0]['timestamp']
            
            representatives.append(best)
        
        return representatives
    
    def _llm_refine(self, steps: List[Dict]) -> List[Dict]:
        """LLM 기반 정제 (향후 구현)"""
        # TODO: OpenAI API 호출
        # 1. 단계들을 텍스트로 변환
        # 2. LLM에게 "이 단계들을 정제해서 핵심 설치 플로우만 추출해줘" 요청
        # 3. LLM 응답 파싱
        
        print("⚠️  LLM refinement not implemented yet (Phase 3)")
        return steps


def main():
    """메인 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Refine extracted steps using LLM")
    parser.add_argument("--input", required=True, help="Input steps JSON file")
    parser.add_argument("--output", required=True, help="Output refined JSON file")
    parser.add_argument("--keyword", default="docker", help="Focus keyword (default: docker)")
    parser.add_argument("--llm", action="store_true", help="Enable LLM refinement")
    parser.add_argument("--min-confidence", type=float, default=0.5, 
                       help="Minimum confidence threshold")
    
    args = parser.parse_args()
    
    # 입력 로드
    print(f"\n📄 Loading: {args.input}")
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
        steps = data['steps']
    
    print(f"✅ Loaded {len(steps)} steps")
    
    # 정제 실행
    refiner = StepRefiner(llm_enabled=args.llm)
    refined = refiner.refine_steps(steps, focus_keyword=args.keyword)
    
    # 결과 저장
    output_data = {
        "refined_steps_count": len(refined),
        "original_steps_count": len(steps),
        "keyword": args.keyword,
        "min_confidence": args.min_confidence,
        "refined_steps": refined
    }
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Refined steps saved: {output_path}")
    print(f"📊 Refinement ratio: {len(refined)}/{len(steps)} ({len(refined)/len(steps)*100:.1f}%)")
    
    # 샘플 출력
    print("\n" + "="*70)
    print("📋 Sample refined steps:")
    print("="*70)
    
    for i, step in enumerate(refined[:5], 1):
        print(f"\n{i}. {step['action'].upper()}")
        if step.get('target'):
            print(f"   Target: {step['target']}")
        print(f"   Time: {step['timestamp']:.1f}s")
        print(f"   Confidence: {step['confidence']:.2f}")
        print(f"   Group size: {step.get('group_size', 1)}")
        desc = step['description'][:80] + '...' if len(step['description']) > 80 else step['description']
        print(f"   Description: {desc}")


if __name__ == "__main__":
    main()
