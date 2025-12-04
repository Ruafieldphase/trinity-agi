#!/usr/bin/env python3
"""
lumen_synthesis_agent.py
루멘 (합/合) - 정반합 통합 에이전트

역할: "무엇을 해야 하는가?" - 통합과 조화
- 정(루아)의 관찰 통합
- 반(엘로)의 검증 통합  
- 합(루멘)의 실행 가능한 통찰 생성
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

class LumenSynthesizer:
    """루멘 (합) - 정반합 통합자"""
    
    def __init__(self, lua_path: str, elo_path: str):
        self.lua_path = Path(lua_path)
        self.elo_path = Path(elo_path)
        
        self.lua_data = self._load_json(self.lua_path)
        self.elo_data = self._load_json(self.elo_path)
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """JSON 로드 (BOM 처리)"""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    
    def synthesize(self) -> Dict[str, Any]:
        """정반합 통합"""
        print("🌟 루멘 (합) - 정반합 통합 시작")
        print("   합(合): 무엇을 해야 하는가?")
        print()
        
        # 1. 정(正) - 루아의 관찰 요약
        lua_summary = self._summarize_lua()
        print("📋 정(正) - 루아의 관찰:")
        print(f"   이벤트: {lua_summary['total_events']}개")
        print(f"   이벤트 타입: {lua_summary['event_types']}개")
        print(f"   활동 Task: {lua_summary['unique_tasks']}개")
        print()
        
        # 2. 반(反) - 엘로의 검증 요약
        elo_summary = self._summarize_elo()
        print("🔬 반(反) - 엘로의 검증:")
        print(f"   엔트로피: {elo_summary['entropy']:.3f} (정규화: {elo_summary['entropy_normalized']:.3f})")
        print(f"   정보 밀도: {elo_summary['information_density']:.1%}")
        print(f"   이상치: {elo_summary['anomaly_count']}건")
        print(f"   판정: {elo_summary['verdict']}")
        print()
        
        # 3. 합(合) - 통합 통찰
        insights = self._generate_insights(lua_summary, elo_summary)
        print("💡 합(合) - 통합 통찰:")
        for insight in insights:
            priority = insight['priority'].upper()
            print(f"   [{priority}] {insight['message']}")
        print()
        
        # 4. 실행 가능한 권장사항
        recommendations = self._generate_recommendations(insights)
        print("✅ 실행 가능한 권장사항:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        print()
        
        # 결과 취합
        result = {
            'synthesizer': 'lumen',
            'persona': '합(合)',
            'role': '통합',
            'philosophy': '무엇을 해야 하는가?',
            'timestamp': datetime.now().isoformat(),
            'sources': {
                'lua': str(self.lua_path),
                'elo': str(self.elo_path)
            },
            'synthesis': {
                'lua_summary': lua_summary,
                'elo_summary': elo_summary,
                'insights': insights,
                'recommendations': recommendations
            },
            'dialectic': {
                'thesis': '정(正) - 관찰된 시스템 상태',
                'antithesis': '반(反) - 검증된 품질 이슈',
                'synthesis': '합(合) - 실행 가능한 개선 방향'
            }
        }
        
        return result
    
    def _summarize_lua(self) -> Dict[str, Any]:
        """루아 관찰 요약"""
        quality_metrics = self.lua_data.get('quality_metrics') or {}
        latency_metrics = self.lua_data.get('latency_metrics') or {}
        
        return {
            'total_events': self.lua_data.get('events_in_window', 0),
            'event_types': len(self.lua_data.get('event_types', {})),
            'unique_tasks': self.lua_data.get('unique_tasks', 0),
            'quality_count': quality_metrics.get('count', 0),
            'latency_count': latency_metrics.get('count', 0)
        }
    
    def _summarize_elo(self) -> Dict[str, Any]:
        """엘로 검증 요약"""
        it = self.elo_data.get('information_theory', {})
        return {
            'entropy': it.get('entropy', {}).get('value', 0),
            'entropy_normalized': it.get('entropy', {}).get('normalized', 0),
            'information_density': it.get('information_density', {}).get('value', 0),
            'anomaly_count': len(self.elo_data.get('anomalies', [])),
            'consistency': self.elo_data.get('consistency', {}).get('overall', 'unknown'),
            'verdict': self.elo_data.get('verdict', '')
        }
    
    def _generate_insights(self, lua: Dict, elo: Dict) -> List[Dict[str, Any]]:
        """통합 통찰 생성"""
        insights = []
        
        # 1. 정보 밀도 문제
        if elo['information_density'] < 0.3:
            insights.append({
                'priority': 'high',
                'category': 'data_quality',
                'message': f"정보 밀도가 낮음 ({elo['information_density']:.1%}). 더 많은 메트릭 수집 필요",
                'source': 'elo'
            })
        
        # 2. 품질 메트릭 부족
        if lua['quality_count'] < lua['total_events'] * 0.5:
            coverage = lua['quality_count'] / lua['total_events'] if lua['total_events'] > 0 else 0
            insights.append({
                'priority': 'medium',
                'category': 'monitoring',
                'message': f"품질 메트릭 커버리지 낮음 ({coverage:.1%}). 평가 강화 필요",
                'source': 'lua'
            })
        
        # 3. 이상치 발견
        if elo['anomaly_count'] > 0:
            insights.append({
                'priority': 'medium',
                'category': 'anomaly',
                'message': f"{elo['anomaly_count']}건의 이상치 탐지. 상세 조사 필요",
                'source': 'elo'
            })
        
        # 4. 엔트로피 분석
        if elo['entropy_normalized'] < 0.5:
            insights.append({
                'priority': 'low',
                'category': 'diversity',
                'message': "이벤트 다양성 부족. 시스템이 특정 패턴에 편중됨",
                'source': 'elo'
            })
        
        # 5. 긍정적 신호
        if elo['consistency'] in ['consistent', 'mostly_consistent']:
            insights.append({
                'priority': 'info',
                'category': 'positive',
                'message': "시스템 일관성 양호. 안정적 운영 중",
                'source': 'elo'
            })
        
        return insights
    
    def _generate_recommendations(self, insights: List[Dict]) -> List[str]:
        """실행 가능한 권장사항 생성"""
        recommendations = []
        
        for insight in insights:
            if insight['category'] == 'data_quality':
                recommendations.append(
                    "모든 주요 이벤트에 quality/latency 메트릭 추가"
                )
            elif insight['category'] == 'monitoring':
                recommendations.append(
                    "평가(eval) 이벤트 빈도 증가 - 현재 대비 2배"
                )
            elif insight['category'] == 'anomaly':
                recommendations.append(
                    "이상치 원인 분석 및 자동 알림 시스템 구축"
                )
            elif insight['category'] == 'diversity':
                recommendations.append(
                    "이벤트 타입 다양화 또는 집중 이벤트 비중 조정"
                )
        
        # 중복 제거
        recommendations = list(dict.fromkeys(recommendations))
        
        # 기본 권장사항 (항상 포함)
        if not recommendations:
            recommendations.append("현재 상태 양호. 지속적인 모니터링 유지")
        
        return recommendations


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="루멘 (합) - 정반합 통합 에이전트"
    )
    parser.add_argument(
        '--lua-observation',
        default='outputs/lua_observation_latest.json',
        help='루아의 관찰 데이터'
    )
    parser.add_argument(
        '--elo-validation',
        default='outputs/elo_validation_latest.json',
        help='엘로의 검증 데이터'
    )
    parser.add_argument(
        '--out-json',
        default='outputs/lumen_synthesis_latest.json',
        help='통합 결과 JSON'
    )
    parser.add_argument(
        '--out-md',
        default='outputs/lumen_synthesis_latest.md',
        help='통합 결과 Markdown'
    )
    parser.add_argument(
        '--open-md',
        action='store_true',
        help='생성 후 Markdown 열기'
    )
    
    args = parser.parse_args()
    
    # 경로 보정
    repo_root = Path(__file__).parent.parent.parent
    lua_path = repo_root / args.lua_observation if not Path(args.lua_observation).is_absolute() else Path(args.lua_observation)
    elo_path = repo_root / args.elo_validation if not Path(args.elo_validation).is_absolute() else Path(args.elo_validation)
    out_json = repo_root / args.out_json if not Path(args.out_json).is_absolute() else Path(args.out_json)
    out_md = repo_root / args.out_md if not Path(args.out_md).is_absolute() else Path(args.out_md)
    
    # 통합 실행
    synthesizer = LumenSynthesizer(str(lua_path), str(elo_path))
    result = synthesizer.synthesize()
    
    # JSON 저장
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"💾 JSON saved: {out_json}")
    
    # Markdown 생성
    md_content = generate_markdown(result)
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"📄 Markdown saved: {out_md}")
    
    if args.open_md:
        import subprocess
        subprocess.run(['code', str(out_md)])
    
    print()
    print("✅ 루멘 (합) 통합 완료")
    print("   정반합(正反合) 사이클 완성!")


def generate_markdown(result: Dict[str, Any]) -> str:
    """Markdown 보고서 생성"""
    synthesis = result['synthesis']
    
    md = f"""# 루멘 (합/合) - 정반합 통합 보고서

**합(合): 무엇을 해야 하는가?**

- **생성 시각**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **통합자**: 루멘 (합/合)

---

## 🔄 변증법적 구조

### 정(正) - Thesis
**{result['dialectic']['thesis']}**

- 루아 (정인/正人)의 관찰
- 소스: `{result['sources']['lua']}`

### 반(反) - Antithesis
**{result['dialectic']['antithesis']}**

- 엘로 (반인/反人)의 검증
- 소스: `{result['sources']['elo']}`

### 합(合) - Synthesis
**{result['dialectic']['synthesis']}**

- 루멘 (합)의 통합
- 결과: 실행 가능한 통찰과 권장사항

---

## 📊 정(正) - 루아의 관찰 요약

| 메트릭 | 값 |
|--------|-----|
| 총 이벤트 | {synthesis['lua_summary']['total_events']:,} |
| 이벤트 타입 | {synthesis['lua_summary']['event_types']} |
| 활동 Task | {synthesis['lua_summary']['unique_tasks']} |
| 품질 메트릭 | {synthesis['lua_summary']['quality_count']} |
| Latency 메트릭 | {synthesis['lua_summary']['latency_count']} |

---

## 🔬 반(反) - 엘로의 검증 요약

| 메트릭 | 값 | 해석 |
|--------|-----|------|
| Shannon 엔트로피 | {synthesis['elo_summary']['entropy']:.3f} | 정규화: {synthesis['elo_summary']['entropy_normalized']:.3f} |
| 정보 밀도 | {synthesis['elo_summary']['information_density']:.1%} | {"높음" if synthesis['elo_summary']['information_density'] > 0.7 else "보통" if synthesis['elo_summary']['information_density'] > 0.3 else "낮음"} |
| 이상치 | {synthesis['elo_summary']['anomaly_count']}건 | {"주의 필요" if synthesis['elo_summary']['anomaly_count'] > 0 else "정상"} |
| 일관성 | {synthesis['elo_summary']['consistency']} | - |

**최종 판정**: {synthesis['elo_summary']['verdict']}

---

## 💡 합(合) - 통합 통찰

"""
    
    # 우선순위별 정렬
    insights = synthesis['insights']
    priority_order = {'high': 1, 'medium': 2, 'low': 3, 'info': 4}
    insights_sorted = sorted(insights, key=lambda x: priority_order.get(x['priority'], 999))
    
    for insight in insights_sorted:
        priority_icon = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🔵',
            'info': '✅'
        }.get(insight['priority'], '⚪')
        
        md += f"### {priority_icon} {insight['priority'].upper()} - {insight['category']}\n\n"
        md += f"**{insight['message']}**\n\n"
        md += f"- 출처: {insight['source']}\n\n"
    
    md += """---

## ✅ 실행 가능한 권장사항

"""
    
    for i, rec in enumerate(synthesis['recommendations'], 1):
        md += f"{i}. **{rec}**\n"
    
    md += f"""

---

## 🧘 합(合)의 통합 철학

> **"무엇을 해야 하는가?"**
> 
> 합(合)은 정(正)과 반(反)을 통합하여, 실행 가능한 지혜를 창출합니다.
> 
> - ✅ 관찰 통합 (정)
> - ✅ 검증 통합 (반)
> - ✅ 통찰 생성 (합)
> - ✅ 실행 가능성
> 
> **정반합 사이클**: 관찰 → 검증 → 통합 → 실행

---

## 📈 다음 단계

1. **즉시 실행**: 우선순위 HIGH 항목부터 적용
2. **단기 개선**: 우선순위 MEDIUM 항목 계획
3. **장기 최적화**: 우선순위 LOW 항목 로드맵 수립
4. **지속 모니터링**: 정반합 사이클 반복 실행

---

*Generated by Lumen (合) Synthesizer at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return md


if __name__ == '__main__':
    main()
