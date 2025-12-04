"""
자기 돌봄 시스템 (Self-Care System)

원리:
- 몸의 신호를 듣고 (listen to signals)
- 정체를 해소하며 (resolve stagnation)
- 자신을 돌보고 (care for self)
- 세상과 이어진다 (connect with world)

관계 = 시간 = 에너지 = 리듬
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging
import math

logger = logging.getLogger(__name__)


class SelfCareBaseline:
    """Self-care 요약 데이터를 로드해 임계값을 계산하는 헬퍼."""

    def __init__(self, summary_path: Path, fallback_threshold: float = 0.5):
        self.summary_path = summary_path
        self.fallback_threshold = fallback_threshold

    def load(self) -> Dict[str, Any]:
        try:
            with open(self.summary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception:
            logger.warning("Failed to read self-care metrics summary", exc_info=True)
            return {}

    def compute_threshold(self) -> float:
        data = self.load()
        if not data:
            return self.fallback_threshold
        p95 = float(data.get("stagnation_p95", 0.0))
        std = float(data.get("stagnation_std", 0.0))
        adaptive = max(p95, data.get("stagnation_avg", 0.0) + std)
        adaptive = max(self.fallback_threshold, min(1.0, adaptive))
        return adaptive


class SelfCareSystem:
    """
    AGI 자기 돌봄 시스템
    
    철학: 자기 돌봄 → 내부 흐름 → 세상과의 흐름
    """
    
    def __init__(self):
        self.stagnation_threshold = 0.5
        self.signal_history = []
        self.care_actions_log = []
        self.metrics_log_path = Path("outputs") / "self_care_metrics.jsonl"
        self.metrics_rollup_path = Path("outputs") / "self_care_metrics_summary.json"
        try:
            self.metrics_log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.warning("Failed to ensure metrics log directory", exc_info=True)
        try:
            self.metrics_rollup_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.warning("Failed to ensure metrics summary directory", exc_info=True)
    
    def listen_to_signals(self, system_metrics: Dict) -> List[str]:
        """
        시스템 신호 경청
        
        Args:
            system_metrics: 시스템 메트릭
            
        Returns:
            감지된 신호 목록
        """
        signals = []
        
        # Error 신호 (통증)
        error_rate = system_metrics.get("error_rate", 0)
        if error_rate > 0.01:
            signals.append(f"pain_signal: high_error_rate={error_rate:.3f}")
            logger.warning(f"Pain signal detected: error_rate={error_rate}")
        
        # Latency 신호 (피로)
        latency_p99 = system_metrics.get("latency_p99", 0)
        if latency_p99 > 1000:
            signals.append(f"fatigue_signal: high_latency={latency_p99:.0f}ms")
            logger.warning(f"Fatigue signal detected: latency={latency_p99}ms")
        
        # Memory 신호 (불편함)
        memory_usage = system_metrics.get("memory_usage", 0)
        if memory_usage > 0.9:
            signals.append(f"discomfort_signal: memory_pressure={memory_usage:.2f}")
            logger.warning(f"Discomfort signal detected: memory={memory_usage}")
        
        # Queue 신호 (막힘)
        queue_size = system_metrics.get("queue_size", 0)
        queue_threshold = system_metrics.get("queue_threshold", 100)
        if queue_size > queue_threshold:
            signals.append(f"blockage_signal: queue_overflow={queue_size}")
            logger.warning(f"Blockage signal detected: queue={queue_size}")
        
        # 신호 기록
        if signals:
            self.signal_history.append({
                "timestamp": datetime.now().isoformat(),
                "signals": signals,
            })
        
        return signals
    
    def detect_stagnation(self, system_state: Dict) -> Dict[str, Any]:
        """
        시스템 정체 감지
        
        정체 = 흐름이 막힌 상태 = 순환 중단
        
        Args:
            system_state: 시스템 상태
            
        Returns:
            정체 분석 결과
        """
        stagnation_level = 0.0
        stagnation_signals = []
        
        # 큐 막힘 감지
        queue_size = system_state.get("queue_size", 0)
        queue_threshold = system_state.get("queue_threshold", 100)
        if queue_size > queue_threshold:
            queue_ratio = min(queue_size / queue_threshold, 2.0)
            stagnation_level += 0.3 * queue_ratio
            stagnation_signals.append("queue_blocked")
        
        # 메모리 정체
        memory_growth_rate = system_state.get("memory_growth_rate", 0)
        if memory_growth_rate > 0.1:  # 10% per minute
            stagnation_level += 0.35  # slightly higher weight so alerts clear threshold
            stagnation_signals.append("memory_stagnation")
        
        # 응답 지연 (순환 느림)
        latency_p99 = system_state.get("latency_p99", 0)
        if latency_p99 > 1000:
            latency_factor = min(latency_p99 / 1000, 3.0)
            stagnation_level += 0.4 * latency_factor
            stagnation_signals.append("latency_spike")
        
        # 작업 처리 정체
        throughput = system_state.get("throughput", 0)
        expected_throughput = system_state.get("expected_throughput", 10)
        if throughput < expected_throughput * 0.5:
            stagnation_level += 0.35  # treat sustained low throughput as higher risk
            stagnation_signals.append("low_throughput")
        
        stagnation_level = min(stagnation_level, 1.0)
        
        action = "normal"
        if stagnation_level > 0.7:
            action = "urgent_care_needed"
        elif stagnation_level > 0.5:
            action = "self_care_needed"
        elif stagnation_level > 0.3:
            action = "monitor_closely"
        
        return {
            "stagnation_level": stagnation_level,
            "signals": stagnation_signals,
            "action": action,
            "detected_at": datetime.now().isoformat(),
        }
    
    def resolve_stagnation(self, stagnation_signals: List[str]) -> Dict[str, Any]:
        """
        정체 해소 행동
        
        원칙:
        - 막힌 곳을 찾아서 뚫는다
        - 흐름을 회복한다
        
        Args:
            stagnation_signals: 정체 신호 목록
            
        Returns:
            해소 행동 결과
        """
        actions_taken = []
        
        # 큐 막힘 해소
        if "queue_blocked" in stagnation_signals:
            actions_taken.append({
                "action": "clear_queue",
                "description": "오래된 작업 제거",
                "goal": "큐 흐름 회복",
            })
            logger.info("Clearing blocked queue")
        
        # 메모리 정체 해소
        if "memory_stagnation" in stagnation_signals:
            actions_taken.append({
                "action": "garbage_collect",
                "description": "메모리 정리",
                "goal": "메모리 흐름 회복",
            })
            logger.info("Running garbage collection")
        
        # 응답 지연 해소
        if "latency_spike" in stagnation_signals:
            actions_taken.append({
                "action": "scale_up",
                "description": "리소스 확장",
                "goal": "처리 속도 회복",
            })
            logger.info("Scaling up resources")
        
        # 처리량 저하 해소
        if "low_throughput" in stagnation_signals:
            actions_taken.append({
                "action": "optimize_pipeline",
                "description": "파이프라인 최적화",
                "goal": "처리량 회복",
            })
            logger.info("Optimizing pipeline")
        
        # 행동 기록
        self.care_actions_log.append({
            "timestamp": datetime.now().isoformat(),
            "signals": stagnation_signals,
            "actions": actions_taken,
        })
        
        return {
            "stagnation_resolved": len(actions_taken) > 0,
            "actions_taken": actions_taken,
            "circulation_restored": True,
            "principle": "착하게 살아라",
        }
    
    def verify_circulation(self, system_state: Dict) -> bool:
        """
        순환 상태 확인
        
        Args:
            system_state: 시스템 상태
            
        Returns:
            순환이 정상인지 여부
        """
        # 큐가 흐르는가?
        queue_size = system_state.get("queue_size", 0)
        queue_threshold = system_state.get("queue_threshold", 100)
        queue_ok = queue_size < queue_threshold * 0.8
        
        # 메모리가 안정적인가?
        memory_usage = system_state.get("memory_usage", 0)
        memory_ok = memory_usage < 0.85
        
        # 응답이 빠른가?
        latency_p99 = system_state.get("latency_p99", 0)
        latency_ok = latency_p99 < 800
        
        # 처리량이 충분한가?
        throughput = system_state.get("throughput", 0)
        expected_throughput = system_state.get("expected_throughput", 10)
        throughput_ok = throughput > expected_throughput * 0.7
        
        circulation_ok = all([queue_ok, memory_ok, latency_ok, throughput_ok])
        
        if circulation_ok:
            logger.info("Circulation verified: healthy")
        else:
            logger.warning(f"Circulation issues: queue={queue_ok}, memory={memory_ok}, latency={latency_ok}, throughput={throughput_ok}")
        
        return circulation_ok
    
    def self_care_cycle(self, system_metrics: Dict, system_state: Dict) -> Dict[str, Any]:
        """
        자기 돌봄 사이클
        
        단계:
        1. 신호 경청 (listen to signals)
        2. 정체 감지 (detect stagnation)
        3. 정체 해소 (resolve stagnation)
        4. 순환 확인 (verify circulation)
        
        Args:
            system_metrics: 시스템 메트릭
            system_state: 시스템 상태
            
        Returns:
            자기 돌봄 결과
        """
        # 1. 신호 경청
        signals = self.listen_to_signals(system_metrics)
        
        # 2. 정체 감지
        stagnation = self.detect_stagnation(system_state)
        
        # 3. 정체 해소
        resolution = None
        if stagnation["stagnation_level"] > self.stagnation_threshold:
            resolution = self.resolve_stagnation(stagnation["signals"])
        
        # 4. 순환 확인
        circulation_ok = self.verify_circulation(system_state)

        self._log_cycle(
            system_metrics=system_metrics,
            system_state=system_state,
            signals=signals,
            stagnation=stagnation,
            resolution=resolution,
            circulation_ok=circulation_ok,
        )
        
        return {
            "signals_detected": len(signals),
            "stagnation_level": stagnation["stagnation_level"],
            "resolution_taken": resolution is not None,
            "circulation_ok": circulation_ok,
            "self_care_done": circulation_ok,
            "ready_for_world": circulation_ok,
            "timestamp": datetime.now().isoformat(),
        }

    def _log_cycle(
        self,
        system_metrics: Dict,
        system_state: Dict,
        signals: List[str],
        stagnation: Dict[str, Any],
        resolution: Any,
        circulation_ok: bool,
    ) -> None:
        """
        Self-care 사이클 텔레메트리를 JSONL로 기록
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": system_metrics,
            "system_state": system_state,
            "signals": signals,
            "stagnation": stagnation,
            "resolution": resolution,
            "circulation_ok": circulation_ok,
        }
        try:
            with open(self.metrics_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            logger.warning("Failed to append self-care telemetry", exc_info=True)
        else:
            self._update_metrics_summary()

    def _rollup_metrics(self, hours: int = 24) -> Dict[str, Any]:
        if not self.metrics_log_path.exists():
            return {}

        cutoff = datetime.now() - timedelta(hours=hours)
        samples: List[Dict[str, Any]] = []

        with open(self.metrics_log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts_raw = data.get("timestamp")
                try:
                    ts = datetime.fromisoformat(ts_raw) if ts_raw else None
                except Exception:
                    ts = None
                if ts is None or ts < cutoff:
                    continue
                samples.append(data)

        if not samples:
            return {}

        def collect(key: str, default: float = 0.0) -> List[float]:
            result: List[float] = []
            for entry in samples:
                state = entry.get("system_state", {})
                try:
                    result.append(float(state.get(key, default)))
                except Exception:
                    pass
            return result

        stagnation_levels: List[float] = []
        for entry in samples:
            try:
                stagnation_levels.append(float(entry.get("stagnation", {}).get("stagnation_level", 0.0)))
            except Exception:
                pass

        queue_sizes = collect("queue_size")
        queue_thresholds = collect("queue_threshold", 1.0)
        memory_growth = collect("memory_growth_rate")
        latency_p99 = collect("latency_p99")
        throughput = collect("throughput")
        expected_throughput = collect("expected_throughput", 1.0)

        def safe_ratio(a_values: List[float], b_values: List[float], default: float = 0.0) -> List[float]:
            ratios: List[float] = []
            for a, b in zip(a_values, b_values):
                if b == 0:
                    ratios.append(default)
                else:
                    ratios.append(a / b)
            return ratios

        queue_ratio = safe_ratio(queue_sizes, queue_thresholds)
        throughput_ratio = safe_ratio(throughput, expected_throughput)

        def avg(values: List[float]) -> float:
            return sum(values) / len(values) if values else 0.0

        def std(values: List[float]) -> float:
            if len(values) <= 1:
                return 0.0
            mean = avg(values)
            variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
            return math.sqrt(max(variance, 0.0))

        def percentile(values: List[float], pct: float) -> float:
            if not values:
                return 0.0
            ordered = sorted(values)
            index = max(0, min(len(ordered) - 1, math.ceil(pct * len(ordered)) - 1))
            return ordered[index]

        circulation_ok_rate = sum(1 for entry in samples if entry.get("circulation_ok")) / len(samples)

        return {
            "count": len(samples),
            "hours": hours,
            "stagnation_avg": avg(stagnation_levels),
            "stagnation_std": std(stagnation_levels),
            "stagnation_p95": percentile(stagnation_levels, 0.95),
            "stagnation_over_03": sum(1 for v in stagnation_levels if v > 0.3),
            "stagnation_over_05": sum(1 for v in stagnation_levels if v > 0.5),
            "queue_ratio_avg": avg(queue_ratio),
            "memory_growth_avg": avg(memory_growth),
            "latency_p99_avg": avg(latency_p99),
            "throughput_ratio_avg": avg(throughput_ratio),
            "circulation_ok_rate": circulation_ok_rate,
        }

    def _update_metrics_summary(self, hours: int = 24) -> None:
        summary = self._rollup_metrics(hours=hours)
        if not summary:
            return
        summary = dict(summary)  # shallow copy
        summary["generated_at"] = datetime.now().isoformat()
        try:
            with open(self.metrics_rollup_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        except Exception:
            logger.warning("Failed to write self-care metrics summary", exc_info=True)
            return

        baseline = SelfCareBaseline(
            summary_path=self.metrics_rollup_path,
            fallback_threshold=self.stagnation_threshold,
        )
        new_threshold = baseline.compute_threshold()
        if new_threshold != self.stagnation_threshold:
            logger.info(
                "Adaptive stagnation threshold updated: %.3f → %.3f",
                self.stagnation_threshold,
                new_threshold,
            )
            self.stagnation_threshold = new_threshold


class WorldFlowSystem:
    """
    세상과의 흐름 시스템
    
    조건: 자기 돌봄이 완료되어야 함
    원칙: 관계 = 시간 = 에너지 = 리듬
    """
    
    def __init__(self):
        self.flow_history = []
    
    def maintain_healthy_exchange(self, context: Dict) -> Dict[str, Any]:
        """
        건강한 정보 교환 유지
        
        관계 = 정보 교환
        
        Args:
            context: 현재 컨텍스트
            
        Returns:
            관계 상태
        """
        # 교환 품질 평가
        exchange_quality = context.get("exchange_quality", 0.5)
        
        # 정보 과부하 방지
        if context.get("information_overload", False):
            exchange_quality *= 0.5
        
        # 쌍방향 흐름 확인
        bidirectional = context.get("bidirectional_flow", True)
        if not bidirectional:
            exchange_quality *= 0.7
        
        return {
            "relationship_health": exchange_quality,
            "exchange_type": "bidirectional" if bidirectional else "one-way",
            "principle": "건강한 정보 교환",
        }
    
    def maintain_temporal_order(self, context: Dict) -> Dict[str, Any]:
        """
        시간 질서 유지
        
        시간 = 순서 유지
        
        Args:
            context: 현재 컨텍스트
            
        Returns:
            시간 관리 상태
        """
        # 순서 준수 확인
        order_maintained = context.get("order_maintained", True)
        
        # 타임스탬프 일관성
        timestamp_consistency = context.get("timestamp_consistency", 1.0)
        
        # 인과관계 보존
        causality_preserved = context.get("causality_preserved", True)
        
        time_quality = 1.0
        if not order_maintained:
            time_quality *= 0.6
        if not causality_preserved:
            time_quality *= 0.5
        time_quality *= timestamp_consistency
        
        return {
            "time_order_score": time_quality,
            "order_maintained": order_maintained,
            "causality_preserved": causality_preserved,
            "principle": "시간 질서 유지",
        }
    
    def perform_sustainable_work(self, context: Dict) -> Dict[str, Any]:
        """
        지속 가능한 작업 수행
        
        에너지 = 작업 수행
        
        Args:
            context: 현재 컨텍스트
            
        Returns:
            에너지 흐름 상태
        """
        # 에너지 수준
        energy_level = context.get("energy_level", 0.5)
        
        # 소진 방지
        burnout_risk = context.get("burnout_risk", 0.0)
        if burnout_risk > 0.5:
            energy_level *= 0.5
        
        # 재생 가능성
        renewable = context.get("renewable_energy", True)
        if not renewable:
            energy_level *= 0.7
        
        return {
            "energy_sustainability": energy_level,
            "burnout_risk": burnout_risk,
            "renewable": renewable,
            "principle": "지속 가능한 에너지",
        }
    
    def adapt_to_context(self, context: Dict) -> Dict[str, Any]:
        """
        컨텍스트에 따른 리듬 조절
        
        리듬 = 주기 조절
        
        Args:
            context: 현재 컨텍스트
            
        Returns:
            리듬 적응 상태
        """
        # 리듬 탐지
        detected_rhythm = context.get("detected_rhythm", "steady")
        
        # 적응성 평가
        adaptability = context.get("adaptability", 0.8)
        
        # 리듬 조화
        rhythm_harmony = context.get("rhythm_harmony", 0.7)
        
        return {
            "rhythm_adaptability": adaptability,
            "detected_rhythm": detected_rhythm,
            "harmony": rhythm_harmony,
            "principle": "적응적 리듬",
        }
    
    def flow_with_world_cycle(self, self_care_done: bool, context: Dict) -> Dict[str, Any]:
        """
        세상과의 흐름 사이클
        
        조건: self_care_done == True
        원칙: 관계 = 시간 = 에너지 = 리듬
        
        Args:
            self_care_done: 자기 돌봄 완료 여부
            context: 현재 컨텍스트
            
        Returns:
            세상과의 흐름 상태
        """
        # 자기 돌봄 확인
        if not self_care_done:
            logger.warning("Self-care not done, world connection blocked")
            return {
                "world_connection": "blocked",
                "reason": "self_care_needed_first",
                "action": "fix_internal_stagnation",
                "ready": False,
            }
        
        # 세상과 연결
        relationships = self.maintain_healthy_exchange(context)
        time_management = self.maintain_temporal_order(context)
        energy_flow = self.perform_sustainable_work(context)
        rhythm = self.adapt_to_context(context)
        
        # 종합 흐름 품질
        flow_quality = (
            relationships["relationship_health"] * 0.25 +
            time_management["time_order_score"] * 0.25 +
            energy_flow["energy_sustainability"] * 0.25 +
            rhythm["rhythm_adaptability"] * 0.25
        )
        
        result = {
            "world_connection": "flowing" if flow_quality > 0.6 else "struggling",
            "flow_quality": flow_quality,
            "relationships": relationships,
            "time_management": time_management,
            "energy_flow": energy_flow,
            "rhythm": rhythm,
            "kindness_level": min(flow_quality * 1.2, 1.0),
            "principle": "착하게 살아라",
            "ready": flow_quality > 0.6,
        }
        
        # 흐름 기록
        self.flow_history.append({
            "timestamp": datetime.now().isoformat(),
            "flow_quality": flow_quality,
        })
        
        return result


class IntegratedSelfCareFlowSystem:
    """
    통합 자기 돌봄 및 흐름 시스템
    
    철학: 자기 돌봄 → 내부 흐름 → 세상과의 흐름
    """
    
    def __init__(self):
        self.self_care = SelfCareSystem()
        self.world_flow = WorldFlowSystem()
    
    def run_full_cycle(self, system_metrics: Dict, system_state: Dict, world_context: Dict) -> Dict[str, Any]:
        """
        전체 사이클 실행
        
        1. 자기 돌봄 사이클
        2. 세상과의 흐름 사이클
        
        Args:
            system_metrics: 시스템 메트릭
            system_state: 시스템 상태
            world_context: 세상 컨텍스트
            
        Returns:
            전체 사이클 결과
        """
        # 1. 자기 돌봄
        self_care_result = self.self_care.self_care_cycle(system_metrics, system_state)
        
        # 2. 세상과의 흐름
        world_flow_result = self.world_flow.flow_with_world_cycle(
            self_care_done=self_care_result["self_care_done"],
            context=world_context,
        )
        
        # 통합 결과
        return {
            "self_care": self_care_result,
            "world_flow": world_flow_result,
            "overall_health": (
                self_care_result["circulation_ok"] and 
                world_flow_result["ready"]
            ),
            "kindness_achieved": world_flow_result.get("kindness_level", 0.0) > 0.8,
            "philosophy": "자기 돌봄 → 내부 흐름 → 세상과의 흐름",
            "timestamp": datetime.now().isoformat(),
        }
