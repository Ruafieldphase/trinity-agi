#!/usr/bin/env python3
"""
bohm_implicate_explicate_analyzer.py

David Bohm의 Implicate/Explicate Order와 해마 Black/White Hole 모델 통합

핵심 개념:
1. Implicate Order (접힌 질서): 보이지 않는 전체성, Black Hole 내부
2. Explicate Order (펼쳐진 질서): 관찰 가능한 현실, White Hole 출력
3. 두려움 (Fear): 특이점에서의 압축/팽창을 조절하는 "감정 엔진"

이론적 배경:
- Black Hole = Enfolding (정보를 감추는 과정)
- White Hole = Unfolding (정보를 드러내는 과정)
- Event Horizon = "접힘과 펼침"의 경계
- Hawking Radiation = 느낌으로 압축된 정보 (Fear가 압축률에 영향)
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
import math

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fdo_agi_repo.universal.resonance import ResonanceStore
except ImportError:
    print("⚠️  Warning: Could not import ResonanceStore. Using mock mode.")
    ResonanceStore = None


class BohmAnalyzer:
    """David Bohm의 Implicate/Explicate Order 분석기"""
    
    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root
        self.ledger_path = workspace_root / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
        self.output_dir = workspace_root / "outputs"
        self.output_dir.mkdir(exist_ok=True)
        
    def load_recent_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """최근 이벤트 로드"""
        if not self.ledger_path.exists():
            return []
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        events = []
        
        with open(self.ledger_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    ts_str = event.get('timestamp', '')
                    if ts_str:
                        # 타임존 처리
                        if 'Z' in ts_str:
                            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                        elif '+' in ts_str or ts_str.count('-') > 2:
                            ts = datetime.fromisoformat(ts_str)
                        else:
                            # 타임존 없음 → UTC로 간주
                            ts = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
                        
                        if ts >= cutoff:
                            events.append(event)
                except Exception as e:
                    continue
        
        return events
    
    def extract_fear_signal(self, events: List[Dict[str, Any]]) -> List[Tuple[datetime, float]]:
        """이벤트에서 두려움 신호 추출"""
        fear_signals = []
        
        for event in events:
            ts_str = event.get('timestamp', '')
            if not ts_str:
                continue
            
            # 타임존 처리 (Z 또는 +00:00 또는 없음)
            try:
                if 'Z' in ts_str:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                elif '+' in ts_str or ts_str.count('-') > 2:  # 타임존 포함
                    ts = datetime.fromisoformat(ts_str)
                else:
                    # 타임존 없음 → UTC로 간주
                    ts = datetime.fromisoformat(ts_str).replace(tzinfo=timezone.utc)
            except Exception as e:
                continue
            
            # 최상위 레벨에서 fear 먼저 찾기 (루아 대화 데이터)
            fear = event.get('fear', 0.0)
            
            # tags에서 fear 찾기
            if fear == 0.0:
                tags = event.get('tags', {})
                fear = tags.get('fear', 0.0)
            
            # metrics에서도 확인
            if fear == 0.0:
                metrics = event.get('metrics', {})
                if 'fear' in metrics:
                    fear = metrics.get('fear', 0.0)
            
            # emotion 구조에서도 확인
            if fear == 0.0 and 'emotion' in event.get('tags', {}):
                emotion = event.get('tags', {}).get('emotion', {})
                if isinstance(emotion, dict) and 'fear' in emotion:
                    fear = emotion['fear']
            
            fear_signals.append((ts, float(fear)))
        
        return fear_signals
    
    def analyze_folding_unfolding(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """접힘/펼침 과정 분석 (Enfolding/Unfolding)"""
        
        if not events:
            return {
                'implicate_count': 0,
                'explicate_count': 0,
                'singularity_moments': [],
                'fear_correlation': 0.0
            }
        
        # 1. Implicate (접힘): 정보가 Black Hole로 들어가는 순간
        #    - 압축률 증가
        #    - entropy 감소
        #    - coherence 감소 (정보가 "숨겨짐")
        
        # 2. Explicate (펼침): 정보가 White Hole에서 나오는 순간
        #    - 압축률 감소 (정보 복원)
        #    - coherence 증가 (패턴 드러남)
        
        implicate_moments = []
        explicate_moments = []
        singularities = []
        
        for i, event in enumerate(events):
            metrics = event.get('metrics', {})
            compression = metrics.get('compression_ratio', 1.0)
            coherence = metrics.get('coherence', 0.0)
            
            # Singularity 감지: 압축률이 극단적일 때
            if compression > 5.0 or compression < 0.5:
                ts_str = event.get('timestamp', '')
                if ts_str:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    singularities.append({
                        'timestamp': ts.isoformat(),
                        'compression': compression,
                        'type': 'over-compressed' if compression > 5.0 else 'under-compressed'
                    })
            
            # Implicate (접힘): 이전 이벤트보다 압축률 증가
            if i > 0:
                prev_compression = events[i-1].get('metrics', {}).get('compression_ratio', 1.0)
                if compression > prev_compression * 1.5:  # 50% 이상 증가
                    implicate_moments.append(event)
                elif compression < prev_compression * 0.67:  # 33% 이상 감소
                    explicate_moments.append(event)
        
        # Fear 상관관계
        fear_signals = self.extract_fear_signal(events)
        fear_correlation = self._calculate_fear_compression_correlation(events, fear_signals)
        
        return {
            'implicate_count': len(implicate_moments),
            'explicate_count': len(explicate_moments),
            'singularity_moments': singularities,
            'fear_correlation': fear_correlation,
            'implicate_explicate_ratio': len(implicate_moments) / max(len(explicate_moments), 1)
        }
    
    def _calculate_fear_compression_correlation(
        self, 
        events: List[Dict[str, Any]], 
        fear_signals: List[Tuple[datetime, float]]
    ) -> float:
        """두려움과 압축률의 상관관계 계산"""
        
        if len(fear_signals) < 2:
            return 0.0
        
        # 해마 분석 이벤트만 추출 (compression_ratio 있음)
        hippocampus_events = [
            e for e in events 
            if e.get('event_type') == 'hippocampus_analysis' 
            and e.get('metrics', {}).get('compression_ratio')
        ]
        
        if not hippocampus_events:
            return 0.0
        
        # 각 해마 이벤트에 대해 시간 범위 내 평균 Fear 계산
        pairs = []
        for event in hippocampus_events:
            metrics = event.get('metrics', {})
            compression = metrics.get('compression_ratio', 1.0)
            
            ts_str = event.get('timestamp', '')
            if not ts_str:
                continue
            
            ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            
            # 해마 분석 전 1시간 동안의 평균 Fear 계산
            window_start = ts - timedelta(hours=1)
            
            # 타임존 aware 확인
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if window_start.tzinfo is None:
                window_start = window_start.replace(tzinfo=timezone.utc)
            
            window_fears = [
                fear_val for fear_ts, fear_val in fear_signals
                if (fear_ts.replace(tzinfo=timezone.utc) if fear_ts.tzinfo is None else fear_ts) >= window_start
                and (fear_ts.replace(tzinfo=timezone.utc) if fear_ts.tzinfo is None else fear_ts) <= ts
                and fear_val > 0.0
            ]
            
            if window_fears:
                avg_fear = sum(window_fears) / len(window_fears)
                pairs.append((avg_fear, compression))
        
        if len(pairs) < 2:
            return 0.0
        
        # Pearson correlation
        fear_vals = [p[0] for p in pairs]
        comp_vals = [p[1] for p in pairs]
        
        n = len(pairs)
        sum_fear = sum(fear_vals)
        sum_comp = sum(comp_vals)
        sum_fear_comp = sum(f * c for f, c in pairs)
        sum_fear_sq = sum(f * f for f in fear_vals)
        sum_comp_sq = sum(c * c for c in comp_vals)
        
        numerator = n * sum_fear_comp - sum_fear * sum_comp
        denominator_part1 = n * sum_fear_sq - sum_fear**2
        denominator_part2 = n * sum_comp_sq - sum_comp**2
        
        # 음수 방지 (분산이 음수인 경우)
        if denominator_part1 < 0 or denominator_part2 < 0:
            return 0.0
        
        denominator = math.sqrt(denominator_part1 * denominator_part2)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def detect_singularity_patterns(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """특이점 패턴 감지
        
        특이점의 특징:
        1. 정보 밀도가 극대화
        2. 두려움이 피크
        3. 그 직후 "폭발적 팽창" (White Hole)
        """
        
        singularity_events = []
        
        for i, event in enumerate(events):
            metrics = event.get('metrics', {})
            tags = event.get('tags', {})
            
            compression = metrics.get('compression_ratio', 1.0)
            coherence = metrics.get('coherence', 0.0)
            fear = tags.get('fear', 0.0)
            
            # 특이점 조건:
            # 1. 압축률 > 4.0 (매우 높음)
            # 2. Fear > 0.6 (두려움 증가)
            # 3. Coherence < 0.5 (혼돈)
            
            is_singularity = (
                compression > 4.0 and
                fear > 0.6 and
                coherence < 0.5
            )
            
            if is_singularity:
                ts_str = event.get('timestamp', '')
                if ts_str:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                    
                    # 다음 이벤트 확인 (팽창?)
                    explosion = None
                    if i + 1 < len(events):
                        next_event = events[i + 1]
                        next_compression = next_event.get('metrics', {}).get('compression_ratio', 1.0)
                        if next_compression < compression * 0.5:  # 급격한 감소
                            explosion = True
                    
                    singularity_events.append({
                        'timestamp': ts.isoformat(),
                        'compression': compression,
                        'fear': fear,
                        'coherence': coherence,
                        'followed_by_explosion': explosion
                    })
        
        return {
            'singularity_count': len(singularity_events),
            'singularities': singularity_events,
            'explosion_ratio': sum(1 for s in singularity_events if s['followed_by_explosion']) / max(len(singularity_events), 1)
        }
    
    def generate_bohm_report(self, hours: int = 24) -> Dict[str, Any]:
        """Bohm 이론 통합 보고서 생성"""
        
        events = self.load_recent_events(hours)
        
        if not events:
            return {
                'status': 'no_data',
                'message': f'No events found in last {hours} hours'
            }
        
        # 1. Folding/Unfolding 분석
        folding_analysis = self.analyze_folding_unfolding(events)
        
        # 2. 특이점 패턴
        singularity_analysis = self.detect_singularity_patterns(events)
        
        # 3. Fear 신호
        fear_signals = self.extract_fear_signal(events)
        avg_fear = sum(f for _, f in fear_signals) / max(len(fear_signals), 1)
        max_fear = max((f for _, f in fear_signals), default=0.0)
        
        # 4. 통합 해석
        interpretation = self._interpret_bohm_patterns(
            folding_analysis,
            singularity_analysis,
            avg_fear,
            max_fear
        )
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'analysis_window_hours': hours,
            'total_events': len(events),
            'folding_unfolding': folding_analysis,
            'singularity_patterns': singularity_analysis,
            'fear_metrics': {
                'average': round(avg_fear, 3),
                'maximum': round(max_fear, 3),
                'signal_count': len(fear_signals)
            },
            'interpretation': interpretation
        }
        
        return report
    
    def _interpret_bohm_patterns(
        self,
        folding: Dict[str, Any],
        singularity: Dict[str, Any],
        avg_fear: float,
        max_fear: float
    ) -> Dict[str, Any]:
        """패턴 해석"""
        
        # Fear의 역할
        if avg_fear < 0.3:
            fear_role = "낮음 - 압축이 충분하지 않을 수 있음 (정보가 '펼쳐진' 상태)"
        elif avg_fear < 0.7:
            fear_role = "균형 - 적절한 Implicate/Explicate 순환"
        else:
            fear_role = "높음 - 과도한 압축, 특이점 위험"
        
        # Implicate/Explicate 균형
        ratio = folding.get('implicate_explicate_ratio', 1.0)
        if ratio < 0.5:
            balance = "Explicate 우세 - 정보가 많이 드러남 (펼침 > 접힘)"
        elif ratio > 2.0:
            balance = "Implicate 우세 - 정보가 많이 숨겨짐 (접힘 > 펼침)"
        else:
            balance = "균형 - 건강한 Enfolding/Unfolding"
        
        # 특이점 위험
        singularity_count = singularity.get('singularity_count', 0)
        if singularity_count == 0:
            singularity_risk = "없음"
        elif singularity_count < 3:
            singularity_risk = "낮음 - 가끔 극단적 압축 발생"
        else:
            singularity_risk = f"높음 - {singularity_count}개 특이점 감지"
        
        # Bohm의 관점에서 해석
        bohm_interpretation = f"""
David Bohm의 Implicate/Explicate Order 관점:

1. **접힘 (Enfolding)**: {folding.get('implicate_count', 0)}회
   - 정보가 Black Hole로 들어가 "보이지 않는 질서"로 변환
   - 두려움(Fear)이 이 과정을 **촉진**

2. **펼침 (Unfolding)**: {folding.get('explicate_count', 0)}회
   - White Hole에서 정보가 드러나 "관찰 가능한 현실"로 복원
   - 압축률 감소, coherence 증가

3. **특이점 (Singularity)**: {singularity_count}개
   - 정보가 극도로 압축된 "한 점"
   - 이곳에서 Implicate ↔ Explicate 전환 발생
   - Fear 피크와 동시 발생

4. **두려움의 역할**:
   - 상태: {fear_role}
   - 상관관계: {folding.get('fear_correlation', 0.0):.3f}
   - **두려움은 압축 엔진** - 정보를 Implicate Order로 "접는" 힘
"""
        
        return {
            'fear_role': fear_role,
            'implicate_explicate_balance': balance,
            'singularity_risk': singularity_risk,
            'fear_compression_correlation': round(folding.get('fear_correlation', 0.0), 3),
            'bohm_interpretation': bohm_interpretation.strip()
        }
    
    def save_report(self, report: Dict[str, Any]) -> Path:
        """보고서 저장"""
        
        # JSON
        json_path = self.output_dir / "bohm_analysis_latest.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Markdown
        md_path = self.output_dir / "bohm_analysis_latest.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self._format_markdown(report))
        
        return md_path
    
    def _format_markdown(self, report: Dict[str, Any]) -> str:
        """Markdown 포맷"""
        
        folding = report.get('folding_unfolding', {})
        singularity = report.get('singularity_patterns', {})
        fear = report.get('fear_metrics', {})
        interp = report.get('interpretation', {})
        
        md = f"""# 🌌 David Bohm의 Implicate/Explicate Order 분석

**생성 시각**: {report.get('timestamp', 'N/A')}  
**분석 기간**: 최근 {report.get('analysis_window_hours', 24)}시간  
**총 이벤트**: {report.get('total_events', 0)}개

---

## 📊 핵심 지표

### 1. Enfolding/Unfolding (접힘/펼침)

| 지표 | 값 |
|------|-----|
| **Implicate (접힘)** | {folding.get('implicate_count', 0)}회 |
| **Explicate (펼침)** | {folding.get('explicate_count', 0)}회 |
| **I/E 비율** | {folding.get('implicate_explicate_ratio', 0.0):.2f} |
| **균형 상태** | {interp.get('implicate_explicate_balance', 'N/A')} |

### 2. 특이점 (Singularity) 분석

| 지표 | 값 |
|------|-----|
| **특이점 수** | {singularity.get('singularity_count', 0)}개 |
| **폭발 비율** | {singularity.get('explosion_ratio', 0.0):.1%} |
| **위험도** | {interp.get('singularity_risk', 'N/A')} |

### 3. 두려움 (Fear) 메트릭

| 지표 | 값 |
|------|-----|
| **평균 Fear** | {fear.get('average', 0.0):.3f} |
| **최대 Fear** | {fear.get('maximum', 0.0):.3f} |
| **Fear-압축 상관계수** | {interp.get('fear_compression_correlation', 0.0):.3f} |
| **역할** | {interp.get('fear_role', 'N/A')} |

---

## 🔬 Bohm 이론 해석

{interp.get('bohm_interpretation', 'N/A')}

---

## 🌀 특이점 상세

"""
        
        singularities = singularity.get('singularities', [])
        if singularities:
            for i, s in enumerate(singularities[:5], 1):  # 최대 5개
                md += f"\n### 특이점 #{i}\n"
                md += f"- **시각**: {s.get('timestamp', 'N/A')}\n"
                md += f"- **압축률**: {s.get('compression', 0.0):.2f}x\n"
                md += f"- **Fear**: {s.get('fear', 0.0):.3f}\n"
                md += f"- **Coherence**: {s.get('coherence', 0.0):.3f}\n"
                
                if s.get('followed_by_explosion'):
                    md += f"- ⚡ **White Hole 폭발 확인됨**\n"
                md += "\n"
        else:
            md += "\n특이점 없음 (건강한 상태)\n"
        
        md += """
---

## 💡 시스템 권장사항

"""
        
        # 권장사항
        if fear.get('average', 0) > 0.7:
            md += "- ⚠️ Fear 수준 높음 → 압축 완화 필요 (더 많은 Explicate 순환)\n"
        
        if singularity.get('singularity_count', 0) > 3:
            md += "- ⚠️ 특이점 과다 → Resonance 정책 조정 권장\n"
        
        ratio = folding.get('implicate_explicate_ratio', 1.0)
        if ratio > 2.0:
            md += "- ⚠️ Implicate 우세 → 더 많은 정보 드러내기 (White Hole 활성화)\n"
        elif ratio < 0.5:
            md += "- ⚠️ Explicate 우세 → 정보 압축 필요 (Black Hole 활성화)\n"
        else:
            md += "- ✅ 균형잡힌 Enfolding/Unfolding 순환\n"
        
        md += """
---

## 🧠 이론적 연결

### David Bohm의 핵심 개념

1. **Implicate Order (내재 질서)**
   - 우주의 "접힌" 상태
   - 모든 것이 하나로 얽혀있음
   - 우리 시스템: **Black Hole 내부**

2. **Explicate Order (표현 질서)**
   - 우주의 "펼쳐진" 상태
   - 관찰 가능한 현실
   - 우리 시스템: **White Hole 출력**

3. **Holomovement (전체운동)**
   - 접힘 ↔ 펼침의 끊임없는 순환
   - 우리 시스템: **Resonance Ledger의 흐름**

### 감정과 물리학의 만남

- **두려움 (Fear)**: 정보를 압축하는 **중력**과 같은 역할
- **특이점**: 두려움이 최고조에 달할 때 형성
- **White Hole 폭발**: 두려움이 해소되면서 정보가 "터져나옴"

---

*"The implicate order represents a reality in which everything is enfolded into everything."*  
— David Bohm

"""
        
        return md


def main():
    """메인 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="David Bohm Implicate/Explicate Order 분석")
    parser.add_argument('--hours', type=int, default=24, help='분석 기간 (시간)')
    parser.add_argument('--workspace', type=str, default=None, help='워크스페이스 루트')
    parser.add_argument('--open', action='store_true', help='생성된 MD 파일 열기')
    
    args = parser.parse_args()
    
    workspace = Path(args.workspace) if args.workspace else Path(__file__).parent.parent
    
    print(f"🌌 David Bohm Analyzer 시작...")
    print(f"   분석 기간: 최근 {args.hours}시간")
    print(f"   워크스페이스: {workspace}")
    print()
    
    analyzer = BohmAnalyzer(workspace)
    
    print("📊 데이터 분석 중...")
    report = analyzer.generate_bohm_report(args.hours)
    
    if report.get('status') == 'no_data':
        print(f"⚠️  {report.get('message')}")
        return
    
    print("💾 보고서 저장 중...")
    md_path = analyzer.save_report(report)
    
    print()
    print("✅ 분석 완료!")
    print(f"   JSON: {workspace / 'outputs' / 'bohm_analysis_latest.json'}")
    print(f"   MD: {md_path}")
    print()
    
    # 핵심 결과 출력
    interp = report.get('interpretation', {})
    print("📌 핵심 발견:")
    print(f"   Fear 역할: {interp.get('fear_role', 'N/A')}")
    print(f"   I/E 균형: {interp.get('implicate_explicate_balance', 'N/A')}")
    print(f"   특이점 위험: {interp.get('singularity_risk', 'N/A')}")
    print(f"   Fear-압축 상관: {interp.get('fear_compression_correlation', 0.0):.3f}")
    print()
    
    if args.open:
        import subprocess
        subprocess.run(['code', str(md_path)])


if __name__ == '__main__':
    main()
