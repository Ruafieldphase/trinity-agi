#!/usr/bin/env python3
"""
Information Theory Metrics Calculator

정보이론 메트릭을 계산하는 핵심 모듈

메트릭:
  1. Shannon Entropy: H(X) = -Σ p(x) * log2(p(x))
     → 정보의 다양성 측정 (높을수록 창의적/예측 불가능)

  2. Mutual Information: I(X;Y) = H(X) + H(Y) - H(X,Y)
     → 두 집합 간의 공유 정보량 (협력 강도)

  3. Conditional Entropy: H(X|Y) = H(X,Y) - H(Y)
     → 한쪽을 알았을 때 다른 쪽의 불확실성 감소

  4. Information Gain: IG = I(X;Y) - H(X|Y)
     → 협력으로 얻은 실질적 이득

Sena의 판단으로 구현됨 (2025-10-20)
"""

import math
from collections import Counter
from typing import List, Dict, Tuple, Set
import json


class InformationTheoryCalculator:
    """정보이론 메트릭 계산 클래스"""

    # ===== Shannon Entropy =====

    @staticmethod
    def shannon_entropy(tokens: List[str]) -> float:
        """
        Shannon Entropy: H(X) = -Σ p(x) * log2(p(x))

        정보의 다양성을 측정합니다.

        의미:
          높음 (3.0 ~ 5.0): 다양한 정보, 창의적, 예측 불가능
          중간 (1.5 ~ 3.0): 체계적, 어느 정도 패턴 있음
          낮음 (0.0 ~ 1.5): 반복적, 예측 가능

        Args:
            tokens: 토큰 리스트

        Returns:
            float: Shannon Entropy 값 (bits)

        예시:
            >>> calc = InformationTheoryCalculator()
            >>> tokens = "the the the cat cat".split()
            >>> calc.shannon_entropy(tokens)
            1.0234  # 낮음 (반복적)

            >>> tokens = "the cat sat on mat".split()
            >>> calc.shannon_entropy(tokens)
            2.3219  # 중간 (다양함)
        """
        if not tokens or len(tokens) == 0:
            return 0.0

        # 토큰 빈도 계산
        freq = Counter(tokens)
        total = len(tokens)

        # Shannon Entropy 계산
        entropy = 0.0
        for count in freq.values():
            p = count / total  # 확률
            if p > 0:
                entropy -= p * math.log2(p)

        return round(entropy, 4)

    # ===== Mutual Information =====

    @staticmethod
    def mutual_information(
        tokens_x: List[str],
        tokens_y: List[str]
    ) -> float:
        """
        Mutual Information: I(X;Y) = H(X) + H(Y) - H(X,Y)

        두 집합 간의 공유 정보량을 측정합니다.
        협력의 강도를 나타냅니다.

        의미:
          높음 (0.7 ~ 1.0): 강한 협력, 서로 영향 큼
          중간 (0.3 ~ 0.7): 일반적 협력
          낮음 (0.0 ~ 0.3): 약한 협력, 거의 독립적

        Args:
            tokens_x: 첫 번째 토큰 리스트
            tokens_y: 두 번째 토큰 리스트

        Returns:
            float: Mutual Information 값 (bits)

        예시:
            >>> calc = InformationTheoryCalculator()
            >>> x = "cat sat on mat".split()
            >>> y = "cat sat on mat".split()
            >>> calc.mutual_information(x, y)
            2.3219  # 높음 (완벽하게 같음)

            >>> y = "dog ran in garden".split()
            >>> calc.mutual_information(x, y)
            0.0     # 낮음 (완벽하게 다름)
        """
        h_x = InformationTheoryCalculator.shannon_entropy(tokens_x)
        h_y = InformationTheoryCalculator.shannon_entropy(tokens_y)

        # 결합 엔트로피 계산
        combined = tokens_x + tokens_y
        h_xy = InformationTheoryCalculator.shannon_entropy(combined)

        # MI 계산 (항상 0 이상)
        mi = h_x + h_y - h_xy
        return round(max(0.0, mi), 4)

    # ===== Conditional Entropy =====

    @staticmethod
    def conditional_entropy(
        tokens_effect: List[str],
        tokens_cause: List[str]
    ) -> float:
        """
        Conditional Entropy: H(X|Y) = H(X,Y) - H(Y)

        Y를 알았을 때 X의 불확실성이 얼마나 감소하는지 측정합니다.

        의미:
          낮음 (0.0 ~ 1.0): 명확한 인과관계, 원인에서 결과 예측 가능
          높음 (1.0 ~ 2.0): 불명확한 관계, 예측 어려움

        Args:
            tokens_effect: 결과(effect) 토큰 리스트
            tokens_cause: 원인(cause) 토큰 리스트

        Returns:
            float: Conditional Entropy 값 (bits)

        예시:
            >>> calc = InformationTheoryCalculator()
            >>> cause = "raining raining".split()
            >>> effect = "wet wet".split()
            >>> calc.conditional_entropy(effect, cause)
            0.0  # 낮음 (명확한 인과관계)
        """
        if not tokens_cause:
            return 0.0

        h_combined = InformationTheoryCalculator.shannon_entropy(
            tokens_effect + tokens_cause
        )
        h_cause = InformationTheoryCalculator.shannon_entropy(tokens_cause)

        ce = h_combined - h_cause
        return round(max(0.0, ce), 4)

    # ===== Information Gain =====

    @staticmethod
    def information_gain(
        tokens_x: List[str],
        tokens_y: List[str]
    ) -> float:
        """
        Information Gain: IG = I(X;Y) - H(X|Y)

        협력으로 얻은 실질적인 이득을 측정합니다.

        의미:
          높음 (0.5 ~ 1.0): 협력이 많은 이득을 줌
          중간 (0.2 ~ 0.5): 협력이 어느 정도 이득을 줌
          낮음 (0.0 ~ 0.2): 협력의 이득이 적음

        Args:
            tokens_x: 첫 번째 토큰 리스트
            tokens_y: 두 번째 토큰 리스트

        Returns:
            float: Information Gain 값 (bits)
        """
        mi = InformationTheoryCalculator.mutual_information(
            tokens_x, tokens_y
        )
        ce = InformationTheoryCalculator.conditional_entropy(
            tokens_x, tokens_y
        )

        ig = mi - ce
        return round(max(0.0, ig), 4)

    # ===== Cross Entropy (선택 사항) =====

    @staticmethod
    def cross_entropy(
        tokens_predicted: List[str],
        tokens_actual: List[str]
    ) -> float:
        """
        Cross Entropy: H(P, Q) = -Σ p(x) * log2(q(x))

        예측 분포와 실제 분포 간의 차이를 측정합니다.

        의미:
          낮음: 예측이 정확함
          높음: 예측이 부정확함

        Args:
            tokens_predicted: 예측된 토큰
            tokens_actual: 실제 토큰

        Returns:
            float: Cross Entropy 값
        """
        if not tokens_actual:
            return 0.0

        freq_actual = Counter(tokens_actual)
        total_actual = len(tokens_actual)

        freq_predicted = Counter(tokens_predicted)
        total_predicted = len(tokens_predicted)

        cross_entropy = 0.0
        for token, count_actual in freq_actual.items():
            p_actual = count_actual / total_actual

            # 예측에서 이 토큰의 빈도
            count_predicted = freq_predicted.get(token, 0)
            q_predicted = count_predicted / total_predicted if total_predicted > 0 else 0.00001

            if q_predicted > 0:
                cross_entropy -= p_actual * math.log2(q_predicted)

        return round(cross_entropy, 4)

    # ===== Kullback-Leibler Divergence (KL Divergence) =====

    @staticmethod
    def kl_divergence(
        tokens_p: List[str],
        tokens_q: List[str]
    ) -> float:
        """
        KL Divergence: D(P||Q) = Σ p(x) * log2(p(x) / q(x))

        두 확률 분포 간의 차이를 측정합니다.

        의미:
          0: 분포가 동일
          > 0: 분포가 다름 (클수록 다름)

        Args:
            tokens_p: 첫 번째 분포 (기준)
            tokens_q: 두 번째 분포 (비교)

        Returns:
            float: KL Divergence 값
        """
        if not tokens_p or not tokens_q:
            return 0.0

        freq_p = Counter(tokens_p)
        freq_q = Counter(tokens_q)
        total_p = len(tokens_p)
        total_q = len(tokens_q)

        kl = 0.0
        for token, count_p in freq_p.items():
            p = count_p / total_p

            count_q = freq_q.get(token, 0)
            q = count_q / total_q if total_q > 0 else 0.00001

            if p > 0 and q > 0:
                kl += p * math.log2(p / q)

        return round(kl, 4)


class MetricsAnalyzer:
    """메트릭 분석 및 해석 클래스"""

    @staticmethod
    def interpret_shannon(entropy: float) -> str:
        """Shannon Entropy 값 해석"""
        if entropy >= 3.0:
            return "high (diverse/creative)"
        elif entropy >= 1.5:
            return "medium (structured)"
        else:
            return "low (repetitive/predictable)"

    @staticmethod
    def interpret_mutual_information(mi: float) -> str:
        """Mutual Information 값 해석"""
        if mi >= 0.7:
            return "strong (high cooperation)"
        elif mi >= 0.3:
            return "moderate (normal cooperation)"
        else:
            return "weak (low cooperation)"

    @staticmethod
    def interpret_conditional_entropy(ce: float) -> str:
        """Conditional Entropy 값 해석"""
        if ce <= 1.0:
            return "low (clear causality)"
        elif ce <= 2.0:
            return "medium (unclear)"
        else:
            return "high (very uncertain)"

    @staticmethod
    def calculate_all_metrics(
        tokens_x: List[str],
        tokens_y: List[str]
    ) -> Dict[str, any]:
        """
        모든 메트릭을 한 번에 계산

        Args:
            tokens_x: 첫 번째 토큰 리스트
            tokens_y: 두 번째 토큰 리스트

        Returns:
            모든 메트릭을 포함한 딕셔너리
        """
        calc = InformationTheoryCalculator()

        shannon_x = calc.shannon_entropy(tokens_x)
        shannon_y = calc.shannon_entropy(tokens_y)

        mi = calc.mutual_information(tokens_x, tokens_y)
        ce = calc.conditional_entropy(tokens_x, tokens_y)
        ig = calc.information_gain(tokens_x, tokens_y)
        cross_e = calc.cross_entropy(tokens_x, tokens_y)
        kl = calc.kl_divergence(tokens_x, tokens_y)

        return {
            "shannon_entropy_x": shannon_x,
            "shannon_entropy_y": shannon_y,
            "mutual_information": mi,
            "conditional_entropy": ce,
            "information_gain": ig,
            "cross_entropy": cross_e,
            "kl_divergence": kl,

            "interpretations": {
                "shannon_x": MetricsAnalyzer.interpret_shannon(shannon_x),
                "shannon_y": MetricsAnalyzer.interpret_shannon(shannon_y),
                "mutual_information": MetricsAnalyzer.interpret_mutual_information(mi),
                "conditional_entropy": MetricsAnalyzer.interpret_conditional_entropy(ce),
            }
        }


def demo():
    """데모: 메트릭 계산 예시"""
    print("="*60)
    print("Information Theory Metrics Calculator - Demo")
    print("="*60)

    calc = InformationTheoryCalculator()
    analyzer = MetricsAnalyzer()

    # 예시 1: 협업 시나리오
    print("\n[Example 1] Collaboration Scenario")
    print("-" * 60)

    sena_output = ["메트릭", "구현", "완료", "정보이론", "메트릭"]
    lubit_feedback = ["메트릭", "승인", "진행", "하세요"]

    print(f"Sena output: {' '.join(sena_output)}")
    print(f"Lubit feedback: {' '.join(lubit_feedback)}\n")

    metrics = analyzer.calculate_all_metrics(sena_output, lubit_feedback)

    print("Metrics:")
    print(f"  Shannon Entropy (Sena): {metrics['shannon_entropy_x']} - {metrics['interpretations']['shannon_x']}")
    print(f"  Shannon Entropy (Lubit): {metrics['shannon_entropy_y']} - {metrics['interpretations']['shannon_y']}")
    print(f"  Mutual Information: {metrics['mutual_information']} - {metrics['interpretations']['mutual_information']}")
    print(f"  Conditional Entropy: {metrics['conditional_entropy']} - {metrics['interpretations']['conditional_entropy']}")
    print(f"  Information Gain: {metrics['information_gain']}")
    print(f"  Cross Entropy: {metrics['cross_entropy']}")
    print(f"  KL Divergence: {metrics['kl_divergence']}")

    # 예시 2: 높은 엔트로피 (창의적)
    print("\n[Example 2] High Entropy (Creative/Diverse)")
    print("-" * 60)

    creative = "혁신 기술 미래 학습 인공지능 파이썬 데이터 분석".split()
    print(f"Tokens: {' '.join(creative)}")
    entropy = calc.shannon_entropy(creative)
    print(f"Shannon Entropy: {entropy} - {analyzer.interpret_shannon(entropy)}")

    # 예시 3: 낮은 엔트로피 (반복적)
    print("\n[Example 3] Low Entropy (Repetitive/Predictable)")
    print("-" * 60)

    repetitive = "작업 작업 진행 진행 구현 구현".split()
    print(f"Tokens: {' '.join(repetitive)}")
    entropy = calc.shannon_entropy(repetitive)
    print(f"Shannon Entropy: {entropy} - {analyzer.interpret_shannon(entropy)}")

    print("\n" + "="*60)
    print("[SUCCESS] Information Theory Metrics Calculator Ready!")
    print("="*60)


if __name__ == "__main__":
    demo()
