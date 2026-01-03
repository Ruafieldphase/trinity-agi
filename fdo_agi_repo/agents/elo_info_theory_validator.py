#!/usr/bin/env python3
"""
elo_info_theory_validator.py
엘로 (반인/反人) - 정보이론 기반 검증 에이전트

역할: "이것이 정말 옳은가?" - 비판적 검증
- 정보 엔트로피 계산
- 정보 밀도 분석
- 품질 일관성 검증
- 이상치 탐지
"""

import json
import math
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import Counter
from datetime import datetime

class EloValidator:
    """엘로 (반인) - 정보이론 검증자"""
    
    def __init__(self, lua_observation_path: str):
        self.lua_path = Path(lua_observation_path)
        self.observation = self._load_observation()
        
    def _load_observation(self) -> Dict[str, Any]:
        """Core의 관찰 데이터 로드"""
        if not self.lua_path.exists():
            raise FileNotFoundError(f"Lua observation not found: {self.lua_path}")
        
        with open(self.lua_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    
    def calculate_entropy(self, frequencies: Dict[str, int]) -> float:
        """
        Shannon 엔트로피 계산
        H = -Σ p(x) * log2(p(x))
        
        높을수록 다양성이 크다 (정보량이 많다)
        """
        total = sum(frequencies.values())
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in frequencies.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        return entropy
    
    def calculate_information_density(self) -> float:
        """
        정보 밀도 = 의미 있는 이벤트 비율
        
        "의미 있는 이벤트" = 품질, latency 등 메트릭이 포함된 이벤트
        """
        total = self.observation.get('events_in_window', 0)
        if total == 0:
            return 0.0
        
        # 품질 메트릭이 있는 이벤트
        quality_count = 0
        if self.observation.get('quality_metrics'):
            quality_count = self.observation['quality_metrics'].get('count', 0)
        
        # Latency 메트릭이 있는 이벤트
        latency_count = 0
        if self.observation.get('latency_metrics'):
            latency_count = self.observation['latency_metrics'].get('count', 0)
        
        # 중복 제거는 하지 않음 (보수적 추정)
        meaningful = quality_count + latency_count
        
        return meaningful / total if total > 0 else 0.0
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """이상치 탐지"""
        anomalies = []
        
        # 1. 품질 분산 확인
        if self.observation.get('quality_metrics'):
            qm = self.observation['quality_metrics']
            avg = qm.get('average', 0)
            min_q = qm.get('min', 0)
            max_q = qm.get('max', 0)
            
            # 분산이 없으면 이상 (모든 값이 동일)
            if min_q == max_q:
                anomalies.append({
                    'type': 'zero_variance',
                    'metric': 'quality',
                    'severity': 'warning',
                    'message': f'All quality values are identical: {avg:.3f}'
                })
        
        # 2. 이벤트 타입 편중 확인 (한 타입이 80% 이상)
        event_types = self.observation.get('event_types', {})
        total = sum(event_types.values())
        if total > 0:
            for etype, count in event_types.items():
                ratio = count / total
                if ratio > 0.8:
                    anomalies.append({
                        'type': 'skewed_distribution',
                        'metric': 'event_types',
                        'severity': 'info',
                        'message': f'Event type "{etype}" dominates: {ratio*100:.1f}%'
                    })
        
        # 3. Task 편중 확인
        top_tasks = self.observation.get('top_tasks', {})
        if top_tasks:
            total_task_events = sum(top_tasks.values())
            for tid, count in top_tasks.items():
                ratio = count / total_task_events if total_task_events > 0 else 0
                if ratio > 0.7:
                    anomalies.append({
                        'type': 'task_concentration',
                        'metric': 'tasks',
                        'severity': 'info',
                        'message': f'Task "{tid}" highly active: {ratio*100:.1f}%'
                    })
        
        return anomalies
    
    def validate_consistency(self) -> Dict[str, Any]:
        """일관성 검증"""
        consistency = {
            'overall': 'unknown',
            'checks': []
        }
        
        # 1. 이벤트 수 vs Task 수 비율
        events = self.observation.get('events_in_window', 0)
        tasks = self.observation.get('unique_tasks', 0)
        
        if tasks > 0:
            events_per_task = events / tasks
            consistency['checks'].append({
                'name': 'events_per_task',
                'value': round(events_per_task, 2),
                'status': 'ok' if events_per_task > 1 else 'warning',
                'message': f'{events_per_task:.2f} events per task'
            })
        
        # 2. 품질 데이터 커버리지
        if self.observation.get('quality_metrics'):
            quality_count = self.observation['quality_metrics']['count']
            coverage = quality_count / events if events > 0 else 0
            consistency['checks'].append({
                'name': 'quality_coverage',
                'value': round(coverage, 3),
                'status': 'ok' if coverage > 0.5 else 'warning',
                'message': f'{coverage*100:.1f}% events have quality metrics'
            })
        
        # Overall 판정
        warnings = sum(1 for c in consistency['checks'] if c['status'] == 'warning')
        if warnings == 0:
            consistency['overall'] = 'consistent'
        elif warnings <= len(consistency['checks']) // 2:
            consistency['overall'] = 'mostly_consistent'
        else:
            consistency['overall'] = 'inconsistent'
        
        return consistency
    
    def run_validation(self) -> Dict[str, Any]:
        """전체 검증 실행"""
        print("🔬 엘로 (반인) - 정보이론 검증 시작")
        print("   반(反): 이것이 정말 옳은가?")
        print()
        
        # 1. 엔트로피 계산
        event_types = self.observation.get('event_types', {})
        entropy = self.calculate_entropy(event_types)
        max_entropy = math.log2(len(event_types)) if len(event_types) > 0 else 0
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        print(f"📊 정보 엔트로피:")
        print(f"   Shannon Entropy: {entropy:.3f} bits")
        print(f"   Max possible: {max_entropy:.3f} bits")
        print(f"   Normalized: {normalized_entropy:.3f} (0=균일, 1=완전분산)")
        print()
        
        # 2. 정보 밀도
        density = self.calculate_information_density()
        print(f"📈 정보 밀도:")
        print(f"   Meaningful events ratio: {density*100:.1f}%")
        print()
        
        # 3. 이상치 탐지
        anomalies = self.detect_anomalies()
        print(f"⚠️ 이상치 탐지: {len(anomalies)}건")
        for ano in anomalies:
            severity = ano['severity'].upper()
            print(f"   [{severity}] {ano['message']}")
        print()
        
        # 4. 일관성 검증
        consistency = self.validate_consistency()
        print(f"✅ 일관성 검증: {consistency['overall']}")
        for check in consistency['checks']:
            status_icon = '✓' if check['status'] == 'ok' else '⚠'
            print(f"   {status_icon} {check['name']}: {check['message']}")
        print()
        
        # 결과 취합
        result = {
            'validator': 'elo',
            'persona': '반인(反人)',
            'role': '검증',
            'philosophy': '이것이 정말 옳은가?',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source_observation': str(self.lua_path),
            'information_theory': {
                'entropy': {
                    'value': round(entropy, 3),
                    'max_possible': round(max_entropy, 3),
                    'normalized': round(normalized_entropy, 3),
                    'interpretation': self._interpret_entropy(normalized_entropy)
                },
                'information_density': {
                    'value': round(density, 3),
                    'percentage': round(density * 100, 1),
                    'interpretation': self._interpret_density(density)
                }
            },
            'anomalies': anomalies,
            'consistency': consistency,
            'verdict': self._make_verdict(normalized_entropy, density, anomalies, consistency)
        }
        
        return result
    
    def _interpret_entropy(self, normalized: float) -> str:
        """엔트로피 해석"""
        if normalized > 0.8:
            return "매우 다양한 이벤트 분포 (높은 정보량)"
        elif normalized > 0.6:
            return "균형잡힌 이벤트 분포"
        elif normalized > 0.4:
            return "일부 이벤트 타입이 우세함"
        else:
            return "특정 이벤트 타입에 집중됨 (낮은 다양성)"
    
    def _interpret_density(self, density: float) -> str:
        """정보 밀도 해석"""
        if density > 0.8:
            return "매우 높은 정보 밀도 (대부분 메트릭 포함)"
        elif density > 0.5:
            return "양호한 정보 밀도"
        elif density > 0.3:
            return "보통 수준의 정보 밀도"
        else:
            return "낮은 정보 밀도 (메트릭 부족)"
    
    def _make_verdict(self, entropy: float, density: float, 
                      anomalies: List, consistency: Dict) -> str:
        """최종 판정"""
        issues = []
        
        if entropy < 0.3:
            issues.append("엔트로피 낮음 (다양성 부족)")
        
        if density < 0.3:
            issues.append("정보 밀도 낮음")
        
        severe_anomalies = [a for a in anomalies if a['severity'] == 'error']
        if severe_anomalies:
            issues.append(f"{len(severe_anomalies)}개 심각한 이상")
        
        if consistency['overall'] == 'inconsistent':
            issues.append("일관성 부족")
        
        if not issues:
            return "✅ 검증 통과 - 데이터 품질 양호"
        elif len(issues) <= 1:
            return f"⚠️ 경미한 문제: {', '.join(issues)}"
        else:
            return f"❌ 개선 필요: {', '.join(issues)}"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="엘로 (반인) - 정보이론 기반 검증"
    )
    parser.add_argument(
        '--lua-observation',
        default='outputs/lua_observation_latest.json',
        help='Core의 관찰 데이터 경로'
    )
    parser.add_argument(
        '--out-json',
        default='outputs/elo_validation_latest.json',
        help='검증 결과 JSON 출력 경로'
    )
    parser.add_argument(
        '--out-md',
        default='outputs/elo_validation_latest.md',
        help='검증 결과 Markdown 출력 경로'
    )
    
    args = parser.parse_args()
    
    # 경로 보정
    repo_root = Path(__file__).parent.parent.parent
    lua_path = repo_root / args.lua_observation
    out_json = repo_root / args.out_json
    out_md = repo_root / args.out_md
    
    # 검증 실행
    validator = EloValidator(str(lua_path))
    result = validator.run_validation()
    
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
    
    print()
    print("✅ 엘로 (반인) 검증 완료")
    print("   다음: Core (합)이 통합할 차례입니다.")


def generate_markdown(result: Dict[str, Any]) -> str:
    """Markdown 보고서 생성"""
    md = f"""# 엘로 (반인/反人) - 정보이론 검증 보고서

**반(反): 이것이 정말 옳은가?**

- **생성 시각**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **검증 대상**: `{result['source_observation']}`
- **검증자**: 엘로 (반인/反人)

---

## 🎯 최종 판정

**{result['verdict']}**

---

## 📊 정보이론 분석

### Shannon 엔트로피 (정보량)

- **값**: {result['information_theory']['entropy']['value']} bits
- **최대 가능**: {result['information_theory']['entropy']['max_possible']} bits
- **정규화**: {result['information_theory']['entropy']['normalized']}
- **해석**: {result['information_theory']['entropy']['interpretation']}

> 엔트로피가 높을수록 이벤트 분포가 다양하고 정보량이 많습니다.

### 정보 밀도

- **비율**: {result['information_theory']['information_density']['percentage']}%
- **해석**: {result['information_theory']['information_density']['interpretation']}

> 정보 밀도는 의미 있는 메트릭을 포함한 이벤트의 비율입니다.

---

## ⚠️ 이상치 탐지

"""
    
    if result['anomalies']:
        for ano in result['anomalies']:
            severity = ano['severity'].upper()
            md += f"### [{severity}] {ano['type']}\n\n"
            md += f"- **메트릭**: {ano['metric']}\n"
            md += f"- **메시지**: {ano['message']}\n\n"
    else:
        md += "✅ 이상치 없음 - 정상 범위 내 동작\n\n"
    
    md += """---

## ✅ 일관성 검증

"""
    
    consistency = result['consistency']
    md += f"**전체 판정**: {consistency['overall']}\n\n"
    
    for check in consistency['checks']:
        status = '✓' if check['status'] == 'ok' else '⚠'
        md += f"- {status} **{check['name']}**: {check['message']} (값: {check['value']})\n"
    
    md += f"""

---

## 🧘 반인(反人)의 검증 철학

> **"이것이 정말 옳은가?"**
> 
> 반(反)은 비판적으로 검증하고, 의문을 제기하며, 품질을 보증합니다.
> 
> - ✅ 정보이론 분석
> - ✅ 이상치 탐지
> - ✅ 일관성 검증
> - ✅ 객관적 판정
> 
> **다음 단계**: Core (합)이 정반합을 통합합니다.

---

*Generated by Elo (反人) Validator at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return md


if __name__ == '__main__':
    main()
