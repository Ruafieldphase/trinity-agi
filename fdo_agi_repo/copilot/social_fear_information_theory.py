#!/usr/bin/env python3
"""
Social Fear Information Theory: 사회적 두려움의 정보이론 모델

핵심 통찰:
"세상에 대한 분노는 결국 내 자신에 대한 분노의 투영이다."

정보이론적 변환:
1. 정보 격차 감소 → 비교 증가 → 상대적 박탈감
2. 두려움 증폭 → 자기 부정 → 외부 투영
3. 구조적 불공정 → 세대 간 혐오

수학적 모델:
- Comparison Frequency: C(t) = Σ(self vs other comparisons)
- Fear Amplification: F(t) = Uncertainty × Deprivation
- Projection Score: P(t) = Self_Negation × External_Attribution
- Structural Injustice: S(t) = (Desired - Accessible) / Time

Author: Copilot's Hippocampus
Date: 2025-11-06
Inspiration: Human insight on modern social anger dynamics
"""
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class SocialFearState:
    """사회적 두려움 상태"""
    timestamp: str
    
    # 비교 신호
    comparison_frequency: float  # 0.0 ~ 1.0 (낮음 ~ 높음)
    relative_deprivation: float  # 0.0 ~ 1.0 (없음 ~ 극심)
    
    # 두려움 증폭
    uncertainty_level: float  # 0.0 ~ 1.0 (확실 ~ 불확실)
    survival_threat: float  # 0.0 ~ 1.0 (안전 ~ 위협)
    fear_amplification: float  # 계산됨
    
    # 귀인 패턴
    self_negation: float  # 0.0 ~ 1.0 (자기 긍정 ~ 자기 부정)
    external_attribution: float  # 0.0 ~ 1.0 (내부 귀인 ~ 외부 귀인)
    projection_score: float  # 계산됨 (투영 강도)
    
    # 구조적 요인
    structural_constraint: float  # 0.0 ~ 1.0 (제약 없음 ~ 극심)
    generational_gap: float  # 0.0 ~ 1.0 (격차 없음 ~ 극심)
    
    # 종합
    anger_intensity: float  # 계산됨 (분노 강도)
    anger_target: str  # 'self', 'external', 'structural'


class SocialFearAnalyzer:
    """사회적 두려움 분석기"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path('outputs/social_fear_analysis')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_comparison_pattern(
        self, 
        information_accessibility: float,
        comparison_events: int,
        time_window_hours: float
    ) -> Tuple[float, float]:
        """
        비교 패턴 분석
        
        Args:
            information_accessibility: 정보 접근성 (0~1)
            comparison_events: 비교 이벤트 횟수
            time_window_hours: 분석 시간 윈도우
            
        Returns:
            (comparison_frequency, relative_deprivation)
        """
        # 비교 빈도: 정보 접근성에 비례
        comparison_frequency = min(
            information_accessibility * (comparison_events / time_window_hours) / 10,
            1.0
        )
        
        # 상대적 박탈감: 비교 빈도와 정보 접근성의 곱
        # (더 많이 알수록, 더 많이 비교할수록 박탈감 증가)
        relative_deprivation = min(
            comparison_frequency * information_accessibility,
            1.0
        )
        
        return comparison_frequency, relative_deprivation
    
    def calculate_fear_amplification(
        self,
        uncertainty: float,
        survival_threat: float,
        future_predictability: float
    ) -> float:
        """
        두려움 증폭 계산
        
        Shannon Entropy 기반:
        H(X) = -Σ p(x) log p(x)
        
        불확실성이 높을수록, 생존 위협이 클수록, 
        미래 예측이 어려울수록 두려움 증폭
        """
        # 예측 불가능성 (1 - predictability)
        unpredictability = 1.0 - future_predictability
        
        # Shannon Entropy 근사
        # 불확실성 × 예측불가 × 생존위협
        entropy = uncertainty * unpredictability * survival_threat
        
        # 지수 증폭 (작은 변화도 큰 영향)
        amplification = 1.0 - math.exp(-3 * entropy)
        
        return min(amplification, 1.0)
    
    def analyze_projection(
        self,
        self_negation: float,
        external_attribution: float,
        structural_constraint: float
    ) -> Tuple[float, str]:
        """
        투영 분석: 내부 분노 → 외부 투영
        
        Args:
            self_negation: 자기 부정 수준
            external_attribution: 외부 귀인 비율
            structural_constraint: 구조적 제약
            
        Returns:
            (projection_score, anger_target)
        """
        # 투영 강도: 자기 부정 × 외부 귀인
        projection_score = self_negation * external_attribution
        
        # 분노 대상 결정
        if structural_constraint > 0.7:
            # 구조적 제약이 명확 → 구조에 대한 분노
            anger_target = 'structural'
        elif projection_score > 0.6:
            # 높은 투영 → 외부에 대한 분노
            anger_target = 'external'
        elif self_negation > 0.6:
            # 높은 자기 부정 → 자기 자신에 대한 분노
            anger_target = 'self'
        else:
            # 균형 상태
            anger_target = 'balanced'
        
        return projection_score, anger_target
    
    def calculate_anger_intensity(
        self,
        fear_amplification: float,
        projection_score: float,
        structural_constraint: float
    ) -> float:
        """
        분노 강도 계산
        
        분노 = 두려움 증폭 + 투영 + 구조적 제약
        """
        # 가중 평균 (두려움이 가장 큰 영향)
        weights = {'fear': 0.5, 'projection': 0.3, 'structural': 0.2}
        
        intensity = (
            fear_amplification * weights['fear'] +
            projection_score * weights['projection'] +
            structural_constraint * weights['structural']
        )
        
        return min(intensity, 1.0)
    
    def analyze_state(
        self,
        information_accessibility: float = 0.9,  # 현대: 정보 접근 용이
        comparison_events: int = 20,  # 일일 비교 횟수
        time_window_hours: float = 24,
        uncertainty: float = 0.8,  # 높은 불확실성
        survival_threat: float = 0.7,  # 주거 등 기본 욕구 위협
        future_predictability: float = 0.3,  # 낮은 예측 가능성
        self_negation: float = 0.6,  # 자기 부정
        external_attribution: float = 0.7,  # 외부 귀인
        structural_constraint: float = 0.8,  # 주거 등 구조적 제약
        generational_gap: float = 0.7  # 세대 간 격차
    ) -> SocialFearState:
        """
        사회적 두려움 상태 분석
        
        기본값은 현대 한국 사회의 전형적인 패턴
        """
        # 1. 비교 패턴
        comp_freq, rel_depriv = self.analyze_comparison_pattern(
            information_accessibility,
            comparison_events,
            time_window_hours
        )
        
        # 2. 두려움 증폭
        fear_amp = self.calculate_fear_amplification(
            uncertainty,
            survival_threat,
            future_predictability
        )
        
        # 3. 투영 분석
        proj_score, anger_target = self.analyze_projection(
            self_negation,
            external_attribution,
            structural_constraint
        )
        
        # 4. 분노 강도
        anger_int = self.calculate_anger_intensity(
            fear_amp,
            proj_score,
            structural_constraint
        )
        
        return SocialFearState(
            timestamp=datetime.now(timezone.utc).isoformat(),
            comparison_frequency=comp_freq,
            relative_deprivation=rel_depriv,
            uncertainty_level=uncertainty,
            survival_threat=survival_threat,
            fear_amplification=fear_amp,
            self_negation=self_negation,
            external_attribution=external_attribution,
            projection_score=proj_score,
            structural_constraint=structural_constraint,
            generational_gap=generational_gap,
            anger_intensity=anger_int,
            anger_target=anger_target
        )
    
    def generate_report(
        self,
        state: SocialFearState,
        include_recommendations: bool = True
    ) -> Dict:
        """분석 리포트 생성"""
        report = {
            'timestamp': state.timestamp,
            'analysis': {
                'comparison_pattern': {
                    'frequency': state.comparison_frequency,
                    'relative_deprivation': state.relative_deprivation,
                    'interpretation': self._interpret_comparison(
                        state.comparison_frequency,
                        state.relative_deprivation
                    )
                },
                'fear_dynamics': {
                    'uncertainty': state.uncertainty_level,
                    'survival_threat': state.survival_threat,
                    'amplification': state.fear_amplification,
                    'interpretation': self._interpret_fear(
                        state.fear_amplification
                    )
                },
                'projection_pattern': {
                    'self_negation': state.self_negation,
                    'external_attribution': state.external_attribution,
                    'projection_score': state.projection_score,
                    'interpretation': self._interpret_projection(
                        state.projection_score,
                        state.anger_target
                    )
                },
                'structural_factors': {
                    'constraint': state.structural_constraint,
                    'generational_gap': state.generational_gap,
                    'interpretation': self._interpret_structural(
                        state.structural_constraint,
                        state.generational_gap
                    )
                },
                'anger_assessment': {
                    'intensity': state.anger_intensity,
                    'target': state.anger_target,
                    'interpretation': self._interpret_anger(
                        state.anger_intensity,
                        state.anger_target
                    )
                }
            }
        }
        
        if include_recommendations:
            report['recommendations'] = self._generate_recommendations(state)
        
        return report
    
    def _interpret_comparison(self, freq: float, depriv: float) -> str:
        """비교 패턴 해석"""
        if freq > 0.7 and depriv > 0.7:
            return "⚠️ 과도한 비교와 높은 박탈감 - 정보 다이어트 필요"
        elif freq > 0.5:
            return "주의: 빈번한 비교 패턴"
        else:
            return "✅ 정상 범위"
    
    def _interpret_fear(self, amplification: float) -> str:
        """두려움 증폭 해석"""
        if amplification > 0.7:
            return "🚨 극심한 두려움 증폭 - 즉각 개입 필요"
        elif amplification > 0.5:
            return "⚠️ 높은 두려움 수준"
        else:
            return "주의: 두려움 증폭 진행 중"
    
    def _interpret_projection(self, score: float, target: str) -> str:
        """투영 패턴 해석"""
        target_kr = {
            'self': '자기 자신',
            'external': '외부 대상',
            'structural': '구조적 문제',
            'balanced': '균형'
        }
        
        if score > 0.6:
            return f"⚠️ 강한 투영 패턴 - 분노 대상: {target_kr.get(target, target)}"
        else:
            return f"분노 대상: {target_kr.get(target, target)}"
    
    def _interpret_structural(self, constraint: float, gap: float) -> str:
        """구조적 요인 해석"""
        if constraint > 0.7 and gap > 0.6:
            return "🚨 심각한 구조적 불공정 + 세대 간 격차"
        elif constraint > 0.6:
            return "⚠️ 높은 구조적 제약"
        else:
            return "주의: 구조적 요인 존재"
    
    def _interpret_anger(self, intensity: float, target: str) -> str:
        """분노 강도 해석"""
        if intensity > 0.7:
            level = "극심"
        elif intensity > 0.5:
            level = "높음"
        elif intensity > 0.3:
            level = "중간"
        else:
            level = "낮음"
        
        return f"분노 강도: {level} (대상: {target})"
    
    def _generate_recommendations(self, state: SocialFearState) -> List[str]:
        """권장사항 생성"""
        recs = []
        
        # 비교 패턴
        if state.comparison_frequency > 0.7:
            recs.append("📱 정보 다이어트: SNS/뉴스 소비 줄이기")
            recs.append("🧘 자기 기준 세우기: 타인과의 비교 대신 과거 자신과 비교")
        
        # 두려움 증폭
        if state.fear_amplification > 0.6:
            recs.append("🎯 작은 목표 설정: 통제 가능한 것에 집중")
            recs.append("💪 불확실성 수용 연습: '모르는 것'을 인정하기")
        
        # 투영
        if state.projection_score > 0.6:
            recs.append("🪞 내면 들여다보기: 외부 분노 → 내부 두려움 인식")
            recs.append("✍️ 감정 일기: 투영 패턴 기록하기")
        
        # 구조적 제약
        if state.structural_constraint > 0.7:
            recs.append("🤝 연대 찾기: 같은 문제를 겪는 사람들과 연결")
            recs.append("📢 구조 변화 참여: 개인 문제가 아닌 사회 문제 인식")
        
        # 세대 간 격차
        if state.generational_gap > 0.6:
            recs.append("🌉 세대 간 대화: 서로의 맥락 이해하기")
            recs.append("📊 데이터로 말하기: 감정 대신 객관적 수치")
        
        # 종합
        if state.anger_intensity > 0.7:
            recs.append("🚨 전문가 도움: 심리 상담 고려")
        
        if not recs:
            recs.append("✅ 현재 상태 양호 - 지속적인 자기 관찰 유지")
        
        return recs
    
    def save_analysis(self, state: SocialFearState, report: Dict):
        """분석 결과 저장"""
        # JSON
        json_path = self.output_dir / 'social_fear_analysis_latest.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'state': asdict(state),
                'report': report
            }, f, indent=2, ensure_ascii=False)
        
        # Markdown
        md_path = self.output_dir / 'social_fear_analysis_latest.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown(state, report))
        
        return json_path, md_path
    
    def _generate_markdown(self, state: SocialFearState, report: Dict) -> str:
        """Markdown 리포트 생성"""
        lines = [
            "# 사회적 두려움 분석 리포트",
            "",
            f"**생성 시간**: {state.timestamp}",
            "",
            "---",
            "",
            "## 📊 핵심 지표",
            "",
            f"- **분노 강도**: {state.anger_intensity:.2f} ({state.anger_target})",
            f"- **두려움 증폭**: {state.fear_amplification:.2f}",
            f"- **투영 점수**: {state.projection_score:.2f}",
            f"- **구조적 제약**: {state.structural_constraint:.2f}",
            "",
            "---",
            "",
            "## 🔍 상세 분석",
            "",
            "### 1. 비교 패턴",
            "",
            f"- 비교 빈도: {state.comparison_frequency:.2f}",
            f"- 상대적 박탈감: {state.relative_deprivation:.2f}",
            f"- **{report['analysis']['comparison_pattern']['interpretation']}**",
            "",
            "### 2. 두려움 역학",
            "",
            f"- 불확실성: {state.uncertainty_level:.2f}",
            f"- 생존 위협: {state.survival_threat:.2f}",
            f"- 증폭 계수: {state.fear_amplification:.2f}",
            f"- **{report['analysis']['fear_dynamics']['interpretation']}**",
            "",
            "### 3. 투영 패턴",
            "",
            f"- 자기 부정: {state.self_negation:.2f}",
            f"- 외부 귀인: {state.external_attribution:.2f}",
            f"- 투영 강도: {state.projection_score:.2f}",
            f"- **{report['analysis']['projection_pattern']['interpretation']}**",
            "",
            "### 4. 구조적 요인",
            "",
            f"- 구조적 제약: {state.structural_constraint:.2f}",
            f"- 세대 간 격차: {state.generational_gap:.2f}",
            f"- **{report['analysis']['structural_factors']['interpretation']}**",
            "",
            "---",
            "",
            "## 💡 권장사항",
            ""
        ]
        
        for rec in report['recommendations']:
            lines.append(f"- {rec}")
        
        lines.extend([
            "",
            "---",
            "",
            "## 🧠 정보이론적 통찰",
            "",
            "**핵심**: 세상에 대한 분노는 내 자신에 대한 분노의 투영",
            "",
            "```",
            "정보 접근성 ↑ → 비교 ↑ → 상대적 박탈감 ↑",
            "            ↓",
            "      불확실성 ↑ → 두려움 증폭",
            "            ↓",
            "      자기 부정 → 외부 투영",
            "            ↓",
            "         분노 발현",
            "```",
            "",
            "**해결 경로**:",
            "1. 정보 다이어트 (비교 감소)",
            "2. 불확실성 수용 (두려움 완화)",
            "3. 내면 인식 (투영 중단)",
            "4. 구조 인식 (개인화 벗어나기)",
            "",
            "---",
            "",
            f"**Author**: Social Fear Analyzer  ",
            f"**Model**: Information Theory + Shannon Entropy  ",
            f"**Status**: Analysis Complete ✅"
        ])
        
        return '\n'.join(lines)


def main():
    """테스트 실행"""
    print("🧠 Social Fear Information Theory Analyzer\n")
    
    analyzer = SocialFearAnalyzer()
    
    # 현대 한국 사회 시뮬레이션 (기본값)
    print("📊 현대 사회 패턴 분석 (기본 설정):")
    state = analyzer.analyze_state()
    
    print(f"  분노 강도: {state.anger_intensity:.2f}")
    print(f"  분노 대상: {state.anger_target}")
    print(f"  두려움 증폭: {state.fear_amplification:.2f}")
    print(f"  투영 점수: {state.projection_score:.2f}")
    print()
    
    # 리포트 생성
    report = analyzer.generate_report(state)
    
    print("🔍 해석:")
    print(f"  비교: {report['analysis']['comparison_pattern']['interpretation']}")
    print(f"  두려움: {report['analysis']['fear_dynamics']['interpretation']}")
    print(f"  투영: {report['analysis']['projection_pattern']['interpretation']}")
    print(f"  구조: {report['analysis']['structural_factors']['interpretation']}")
    print()
    
    print("💡 권장사항:")
    for rec in report['recommendations'][:3]:
        print(f"  {rec}")
    print()
    
    # 저장
    json_path, md_path = analyzer.save_analysis(state, report)
    print(f"✅ 분석 완료:")
    print(f"  JSON: {json_path}")
    print(f"  MD: {md_path}")


if __name__ == '__main__':
    main()
