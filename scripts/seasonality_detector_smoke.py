"""
Seasonality Detector Smoke Test

원본 anomaly_detection.py의 SeasonalAnomalyDetector 핵심 로직을 추출하여
간단한 합성 시계열 데이터로 계절성 위배(SEASONALITY_VIOLATION) 탐지를 검증합니다.

Exit Code:
  0 = PASS (모든 테스트 통과)
  1 = FAIL (탐지 실패 또는 오류)
"""
import sys
import numpy as np
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from enum import Enum


class AnomalyType(Enum):
    """이상 유형"""
    SEASONALITY_VIOLATION = "seasonality_violation"


class AnomalySeverity(Enum):
    """이상 심각도"""
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AnomalyAlert:
    """이상 알림"""
    metric_name: str
    metric_value: float
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    baseline: float
    deviation: float
    confidence: float
    description: str


class SeasonalAnomalyDetector:
    """계절성 기반 이상 탐지 (원본: original_data/anomaly_detection.py)"""

    def __init__(self, period: int = 1440):
        """
        Args:
            period: 계절 주기 (기본: 1440분 = 1일)
        """
        self.name = "Seasonal"
        self.period = period
        self.seasonal_data: Dict[int, List[float]] = {}
        self.counter = 0

    def get_seasonal_baseline(self, current_period: int) -> Tuple[float, float]:
        """계절적 기준값 계산"""
        if current_period not in self.seasonal_data:
            return 0.0, 1.0

        seasonal_values = self.seasonal_data[current_period]
        if len(seasonal_values) < 2:
            return np.mean(seasonal_values), 1.0

        baseline = np.mean(seasonal_values)
        std = np.std(seasonal_values)

        return baseline, max(std, 1.0)

    def detect(self, metric_value: float, metric_name: str = "metric") -> Optional[AnomalyAlert]:
        """이상 탐지"""
        self.counter += 1
        current_period = self.counter % self.period

        if current_period not in self.seasonal_data:
            self.seasonal_data[current_period] = []

        # 최소 3개 데이터 필요
        if len(self.seasonal_data[current_period]) < 3:
            # 학습 단계: 그냥 추가
            self.seasonal_data[current_period].append(metric_value)
            return None

        # 베이스라인 계산 (현재 값 추가 전)
        baseline, std = self.get_seasonal_baseline(current_period)
        deviation = abs(metric_value - baseline) / std if std > 0 else 0

        # 이상 여부 판단
        is_anomaly = deviation > 3.0

        if is_anomaly:
            # 이상치 발견: 알림 생성하고 베이스라인에는 추가하지 않음
            if deviation > 5:
                severity = AnomalySeverity.CRITICAL
            elif deviation > 4:
                severity = AnomalySeverity.HIGH
            else:
                severity = AnomalySeverity.MEDIUM

            confidence = min(0.99, (deviation - 3.0) / 3.0)

            alert = AnomalyAlert(
                metric_name=metric_name,
                metric_value=metric_value,
                anomaly_type=AnomalyType.SEASONALITY_VIOLATION,
                severity=severity,
                baseline=baseline,
                deviation=deviation,
                confidence=confidence,
                description=f"Seasonal deviation: {deviation:.2f}σ"
            )

            return alert
        else:
            # 정상: 베이스라인에 추가
            self.seasonal_data[current_period].append(metric_value)
            return None


def generate_seasonal_timeseries(period: int = 24, cycles: int = 5, noise: float = 0.1) -> np.ndarray:
    """계절성 있는 합성 시계열 생성 (사인파 + 노이즈)"""
    t = np.arange(period * cycles)
    # 기본 사인파 패턴 (진폭 10, 평균 50)
    seasonal_pattern = 50 + 10 * np.sin(2 * np.pi * t / period)
    # 작은 노이즈 추가
    data = seasonal_pattern + np.random.normal(0, noise, len(t))
    return data


def main():
    print("=" * 70)
    print("Seasonality Detector Smoke Test")
    print("=" * 70)

    # 테스트 파라미터
    PERIOD = 24  # 24시간 주기
    CYCLES = 5   # 5 사이클 (5일치 데이터)

    detector = SeasonalAnomalyDetector(period=PERIOD)

    # Test 1: 정상 계절성 데이터 (알림 없어야 함)
    print("\n[Test 1] Normal seasonal pattern (should NOT trigger alert)")
    normal_data = generate_seasonal_timeseries(period=PERIOD, cycles=CYCLES, noise=0.1)
    
    alert_count = 0
    for i, value in enumerate(normal_data):
        alert = detector.detect(value, metric_name="normal_metric")
        if alert:
            alert_count += 1
    
    print(f"  ✓ Processed {len(normal_data)} points")
    print(f"  ✓ Alerts triggered: {alert_count}")
    assert alert_count == 0, f"Expected 0 alerts for normal data, got {alert_count}"
    print("  ✓ PASS: No false positives")

    # Test 2: 계절성 위배 (이상치 주입)
    print("\n[Test 2] Seasonal violation (should trigger alert)")
    detector2 = SeasonalAnomalyDetector(period=PERIOD)
    
    # 정상 데이터 5 사이클 학습 (충분한 베이스라인)
    learning_data = generate_seasonal_timeseries(period=PERIOD, cycles=5, noise=0.1)
    for value in learning_data:
        detector2.detect(value, metric_name="test_metric")
    
    print(f"  ✓ Baseline established with {len(learning_data)} points")
    
    # 베이스라인 확인
    test_position = PERIOD // 2
    baseline, std = detector2.get_seasonal_baseline(test_position)
    print(f"  ✓ Baseline at position {test_position}: {baseline:.2f} ± {std:.2f}")
    
    # 6번째 사이클 중간에 명확한 이상치 주입
    anomaly_injected = False
    anomaly_detected = False
    
    for i in range(PERIOD):
        if i == test_position:  # 중간 지점에 이상치
            anomalous_value = 200.0  # 정상 범위(40-60)를 크게 벗어남
            anomaly_injected = True
            
            # 디버깅: 탐지 전 상태 출력
            current_period = (detector2.counter + 1) % detector2.period
            baseline_pre, std_pre = detector2.get_seasonal_baseline(current_period)
            deviation_pre = abs(anomalous_value - baseline_pre) / std_pre if std_pre > 0 else 0
            print(f"  [DEBUG] Before detect:")
            print(f"    - current_period: {current_period}")
            print(f"    - baseline: {baseline_pre:.2f}, std: {std_pre:.2f}")
            print(f"    - expected deviation: {deviation_pre:.2f}σ")
            
            alert = detector2.detect(anomalous_value, metric_name="test_metric")
            if alert:
                anomaly_detected = True
                print(f"  ✓ Anomaly detected at position {i}")
                print(f"    - Value: {anomalous_value:.2f}")
                print(f"    - Baseline: {alert.baseline:.2f}")
                print(f"    - Deviation: {alert.deviation:.2f}σ")
                print(f"    - Severity: {alert.severity.name}")
                print(f"    - Confidence: {alert.confidence:.2f}")
            else:
                print(f"  ! No alert at position {i} (value={anomalous_value:.2f})")
                print(f"    - Deviation was: {deviation_pre:.2f}σ (threshold: 3.0σ)")
        else:
            # 정상 값
            normal_value = 50 + 10 * np.sin(2 * np.pi * i / PERIOD) + np.random.normal(0, 0.1)
            detector2.detect(normal_value, metric_name="test_metric")
    
    assert anomaly_injected, "Anomaly injection failed"
    assert anomaly_detected, f"Anomaly detection failed (expected alert not triggered)"
    print("  ✓ PASS: Seasonal violation correctly detected")

    # Test 3: 다양한 주기 테스트
    print("\n[Test 3] Different periods (hourly vs daily)")
    
    # 시간별 주기 (60분)
    detector_hourly = SeasonalAnomalyDetector(period=60)
    hourly_data = generate_seasonal_timeseries(period=60, cycles=3, noise=0.2)
    
    for value in hourly_data:
        detector_hourly.detect(value, metric_name="hourly")
    
    print(f"  ✓ Hourly detector initialized: period={detector_hourly.period}")
    print(f"  ✓ Processed {len(hourly_data)} hourly points")
    
    # 일별 주기 (1440분)
    detector_daily = SeasonalAnomalyDetector(period=1440)
    daily_data = generate_seasonal_timeseries(period=1440, cycles=2, noise=0.5)
    
    for value in daily_data:
        detector_daily.detect(value, metric_name="daily")
    
    print(f"  ✓ Daily detector initialized: period={detector_daily.period}")
    print(f"  ✓ Processed {len(daily_data)} daily points")
    print("  ✓ PASS: Multiple period configurations work")

    print("\n" + "=" * 70)
    print("PASS: All seasonality detector tests passed.")
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
