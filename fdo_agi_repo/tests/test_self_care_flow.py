"""
자기 돌봄 시스템 테스트

철학: 자기 돌봄 → 내부 흐름 → 세상과의 흐름
"""

import pytest
from fdo_agi_repo.orchestrator.self_care import (
    SelfCareSystem,
    WorldFlowSystem,
    IntegratedSelfCareFlowSystem,
)


class TestSelfCareSystem:
    """자기 돌봄 시스템 테스트"""
    
    def test_listen_to_signals_normal(self):
        """정상 상태에서는 신호가 없어야 함"""
        system = SelfCareSystem()
        
        metrics = {
            "error_rate": 0.001,
            "latency_p99": 500,
            "memory_usage": 0.5,
            "queue_size": 50,
            "queue_threshold": 100,
        }
        
        signals = system.listen_to_signals(metrics)
        
        assert signals == []
    
    def test_listen_to_signals_pain(self):
        """에러가 많으면 통증 신호"""
        system = SelfCareSystem()
        
        metrics = {
            "error_rate": 0.05,  # 5% error rate
            "latency_p99": 500,
            "memory_usage": 0.5,
        }
        
        signals = system.listen_to_signals(metrics)
        
        assert len(signals) == 1
        assert "pain_signal" in signals[0]
    
    def test_listen_to_signals_fatigue(self):
        """응답이 느리면 피로 신호"""
        system = SelfCareSystem()
        
        metrics = {
            "error_rate": 0.001,
            "latency_p99": 1500,  # 1.5s latency
            "memory_usage": 0.5,
        }
        
        signals = system.listen_to_signals(metrics)
        
        assert len(signals) == 1
        assert "fatigue_signal" in signals[0]
    
    def test_listen_to_signals_discomfort(self):
        """메모리가 부족하면 불편함 신호"""
        system = SelfCareSystem()
        
        metrics = {
            "error_rate": 0.001,
            "latency_p99": 500,
            "memory_usage": 0.95,  # 95% memory usage
        }
        
        signals = system.listen_to_signals(metrics)
        
        assert len(signals) == 1
        assert "discomfort_signal" in signals[0]
    
    def test_listen_to_signals_blockage(self):
        """큐가 막히면 막힘 신호"""
        system = SelfCareSystem()
        
        metrics = {
            "error_rate": 0.001,
            "latency_p99": 500,
            "memory_usage": 0.5,
            "queue_size": 150,
            "queue_threshold": 100,
        }
        
        signals = system.listen_to_signals(metrics)
        
        assert len(signals) == 1
        assert "blockage_signal" in signals[0]
    
    def test_detect_stagnation_normal(self):
        """정상 상태에서는 정체가 없어야 함"""
        system = SelfCareSystem()
        
        state = {
            "queue_size": 50,
            "queue_threshold": 100,
            "memory_growth_rate": 0.01,
            "latency_p99": 500,
            "throughput": 15,
            "expected_throughput": 10,
        }
        
        result = system.detect_stagnation(state)
        
        assert result["stagnation_level"] < 0.3
        assert result["action"] == "normal"
    
    def test_detect_stagnation_queue_blocked(self):
        """큐가 막히면 정체 감지"""
        system = SelfCareSystem()
        
        state = {
            "queue_size": 200,
            "queue_threshold": 100,
            "memory_growth_rate": 0.01,
            "latency_p99": 500,
            "throughput": 10,
            "expected_throughput": 10,
        }
        
        result = system.detect_stagnation(state)
        
        assert result["stagnation_level"] > 0.3
        assert "queue_blocked" in result["signals"]
    
    def test_detect_stagnation_memory_leak(self):
        """메모리 누수 감지"""
        system = SelfCareSystem()
        
        state = {
            "queue_size": 50,
            "queue_threshold": 100,
            "memory_growth_rate": 0.15,  # 15% growth per minute
            "latency_p99": 500,
            "throughput": 10,
            "expected_throughput": 10,
        }
        
        result = system.detect_stagnation(state)
        
        assert result["stagnation_level"] > 0.3
        assert "memory_stagnation" in result["signals"]
    
    def test_detect_stagnation_high_latency(self):
        """높은 레이턴시 감지"""
        system = SelfCareSystem()
        
        state = {
            "queue_size": 50,
            "queue_threshold": 100,
            "memory_growth_rate": 0.01,
            "latency_p99": 2000,  # 2s latency
            "throughput": 10,
            "expected_throughput": 10,
        }
        
        result = system.detect_stagnation(state)
        
        assert result["stagnation_level"] > 0.3
        assert "latency_spike" in result["signals"]
    
    def test_detect_stagnation_low_throughput(self):
        """낮은 처리량 감지"""
        system = SelfCareSystem()
        
        state = {
            "queue_size": 50,
            "queue_threshold": 100,
            "memory_growth_rate": 0.01,
            "latency_p99": 500,
            "throughput": 3,  # 30% of expected
            "expected_throughput": 10,
        }
        
        result = system.detect_stagnation(state)
        
        assert result["stagnation_level"] > 0.3
        assert "low_throughput" in result["signals"]
    
    def test_detect_stagnation_urgent(self):
        """심각한 정체 상태"""
        system = SelfCareSystem()
        
        state = {
            "queue_size": 300,
            "queue_threshold": 100,
            "memory_growth_rate": 0.20,
            "latency_p99": 3000,
            "throughput": 2,
            "expected_throughput": 10,
        }
        
        result = system.detect_stagnation(state)
        
        assert result["stagnation_level"] > 0.7
        assert result["action"] == "urgent_care_needed"
    
    def test_resolve_stagnation_queue(self):
        """큐 막힘 해소"""
        system = SelfCareSystem()
        
        result = system.resolve_stagnation(["queue_blocked"])
        
        assert result["stagnation_resolved"]
        assert len(result["actions_taken"]) == 1
        assert result["actions_taken"][0]["action"] == "clear_queue"
        assert result["principle"] == "착하게 살아라"
    
    def test_resolve_stagnation_memory(self):
        """메모리 정체 해소"""
        system = SelfCareSystem()
        
        result = system.resolve_stagnation(["memory_stagnation"])
        
        assert result["stagnation_resolved"]
        assert len(result["actions_taken"]) == 1
        assert result["actions_taken"][0]["action"] == "garbage_collect"
    
    def test_resolve_stagnation_multiple(self):
        """다중 정체 해소"""
        system = SelfCareSystem()
        
        result = system.resolve_stagnation([
            "queue_blocked",
            "memory_stagnation",
            "latency_spike",
            "low_throughput",
        ])
        
        assert result["stagnation_resolved"]
        assert len(result["actions_taken"]) == 4
    
    def test_verify_circulation_healthy(self):
        """건강한 순환 확인"""
        system = SelfCareSystem()
        
        state = {
            "queue_size": 50,
            "queue_threshold": 100,
            "memory_usage": 0.6,
            "latency_p99": 500,
            "throughput": 12,
            "expected_throughput": 10,
        }
        
        ok = system.verify_circulation(state)
        
        assert ok is True
    
    def test_verify_circulation_unhealthy(self):
        """건강하지 않은 순환"""
        system = SelfCareSystem()
        
        state = {
            "queue_size": 90,
            "queue_threshold": 100,
            "memory_usage": 0.9,
            "latency_p99": 1000,
            "throughput": 5,
            "expected_throughput": 10,
        }
        
        ok = system.verify_circulation(state)
        
        assert ok is False
    
    def test_self_care_cycle_normal(self):
        """정상 상태 자기 돌봄"""
        system = SelfCareSystem()
        
        metrics = {
            "error_rate": 0.001,
            "latency_p99": 500,
            "memory_usage": 0.5,
        }
        
        state = {
            "queue_size": 50,
            "queue_threshold": 100,
            "memory_growth_rate": 0.01,
            "latency_p99": 500,
            "throughput": 12,
            "expected_throughput": 10,
            "memory_usage": 0.5,
        }
        
        result = system.self_care_cycle(metrics, state)
        
        assert result["self_care_done"]
        assert result["ready_for_world"]
    
    def test_self_care_cycle_stagnation(self):
        """정체 상태 자기 돌봄"""
        system = SelfCareSystem()
        
        metrics = {
            "error_rate": 0.001,
            "latency_p99": 2000,
            "memory_usage": 0.5,
        }
        
        state = {
            "queue_size": 200,
            "queue_threshold": 100,
            "memory_growth_rate": 0.15,
            "latency_p99": 2000,
            "throughput": 3,
            "expected_throughput": 10,
            "memory_usage": 0.7,
        }
        
        result = system.self_care_cycle(metrics, state)
        
        assert result["stagnation_level"] > 0.5
        assert result["resolution_taken"]


class TestWorldFlowSystem:
    """세상과의 흐름 시스템 테스트"""
    
    def test_maintain_healthy_exchange(self):
        """건강한 정보 교환"""
        system = WorldFlowSystem()
        
        context = {
            "exchange_quality": 0.8,
            "bidirectional_flow": True,
        }
        
        result = system.maintain_healthy_exchange(context)
        
        assert result["relationship_health"] == 0.8
        assert result["exchange_type"] == "bidirectional"
    
    def test_maintain_temporal_order(self):
        """시간 질서 유지"""
        system = WorldFlowSystem()
        
        context = {
            "order_maintained": True,
            "timestamp_consistency": 1.0,
            "causality_preserved": True,
        }
        
        result = system.maintain_temporal_order(context)
        
        assert result["time_order_score"] == 1.0
        assert result["order_maintained"]
    
    def test_perform_sustainable_work(self):
        """지속 가능한 작업"""
        system = WorldFlowSystem()
        
        context = {
            "energy_level": 0.8,
            "burnout_risk": 0.2,
            "renewable_energy": True,
        }
        
        result = system.perform_sustainable_work(context)
        
        assert result["energy_sustainability"] == 0.8
        assert result["renewable"]
    
    def test_adapt_to_context(self):
        """리듬 적응"""
        system = WorldFlowSystem()
        
        context = {
            "detected_rhythm": "steady",
            "adaptability": 0.9,
            "rhythm_harmony": 0.8,
        }
        
        result = system.adapt_to_context(context)
        
        assert result["rhythm_adaptability"] == 0.9
        assert result["detected_rhythm"] == "steady"
    
    def test_flow_with_world_blocked(self):
        """자기 돌봄 없으면 세상과 연결 차단"""
        system = WorldFlowSystem()
        
        result = system.flow_with_world_cycle(
            self_care_done=False,
            context={},
        )
        
        assert result["world_connection"] == "blocked"
        assert result["reason"] == "self_care_needed_first"
        assert not result["ready"]
    
    def test_flow_with_world_flowing(self):
        """자기 돌봄 완료 후 세상과 연결"""
        system = WorldFlowSystem()
        
        context = {
            "exchange_quality": 0.8,
            "bidirectional_flow": True,
            "order_maintained": True,
            "timestamp_consistency": 1.0,
            "causality_preserved": True,
            "energy_level": 0.8,
            "burnout_risk": 0.2,
            "renewable_energy": True,
            "detected_rhythm": "steady",
            "adaptability": 0.9,
            "rhythm_harmony": 0.8,
        }
        
        result = system.flow_with_world_cycle(
            self_care_done=True,
            context=context,
        )
        
        assert result["world_connection"] == "flowing"
        assert result["flow_quality"] > 0.6
        assert result["kindness_level"] > 0.8
        assert result["principle"] == "착하게 살아라"
        assert result["ready"]


class TestIntegratedSelfCareFlowSystem:
    """통합 시스템 테스트"""
    
    def test_full_cycle_healthy(self):
        """건강한 전체 사이클"""
        system = IntegratedSelfCareFlowSystem()
        
        metrics = {
            "error_rate": 0.001,
            "latency_p99": 500,
            "memory_usage": 0.5,
        }
        
        state = {
            "queue_size": 50,
            "queue_threshold": 100,
            "memory_growth_rate": 0.01,
            "latency_p99": 500,
            "throughput": 12,
            "expected_throughput": 10,
            "memory_usage": 0.5,
        }
        
        context = {
            "exchange_quality": 0.8,
            "bidirectional_flow": True,
            "order_maintained": True,
            "timestamp_consistency": 1.0,
            "causality_preserved": True,
            "energy_level": 0.8,
            "burnout_risk": 0.2,
            "renewable_energy": True,
            "detected_rhythm": "steady",
            "adaptability": 0.9,
            "rhythm_harmony": 0.8,
        }
        
        result = system.run_full_cycle(metrics, state, context)
        
        assert result["overall_health"]
        assert result["kindness_achieved"]
        assert result["philosophy"] == "자기 돌봄 → 내부 흐름 → 세상과의 흐름"
    
    def test_full_cycle_stagnation(self):
        """정체 상태 전체 사이클"""
        system = IntegratedSelfCareFlowSystem()
        
        metrics = {
            "error_rate": 0.05,
            "latency_p99": 2000,
            "memory_usage": 0.9,
        }
        
        state = {
            "queue_size": 200,
            "queue_threshold": 100,
            "memory_growth_rate": 0.15,
            "latency_p99": 2000,
            "throughput": 3,
            "expected_throughput": 10,
            "memory_usage": 0.9,
        }
        
        context = {
            "exchange_quality": 0.5,
            "bidirectional_flow": True,
            "order_maintained": True,
            "timestamp_consistency": 1.0,
            "causality_preserved": True,
            "energy_level": 0.5,
            "burnout_risk": 0.6,
            "renewable_energy": True,
            "detected_rhythm": "erratic",
            "adaptability": 0.5,
            "rhythm_harmony": 0.5,
        }
        
        result = system.run_full_cycle(metrics, state, context)
        
        # 자기 돌봄이 실행되어야 함
        assert result["self_care"]["resolution_taken"]
        
        # 순환이 회복되지 않으면 세상과 연결 차단
        if not result["self_care"]["circulation_ok"]:
            assert result["world_flow"]["world_connection"] == "blocked"
    
    def test_philosophy_principle(self):
        """철학 원칙 확인"""
        system = IntegratedSelfCareFlowSystem()
        
        # 최소한의 입력
        metrics = {"error_rate": 0.001, "latency_p99": 500, "memory_usage": 0.5}
        state = {
            "queue_size": 50,
            "queue_threshold": 100,
            "memory_growth_rate": 0.01,
            "latency_p99": 500,
            "throughput": 10,
            "expected_throughput": 10,
            "memory_usage": 0.5,
        }
        context = {
            "exchange_quality": 0.8,
            "bidirectional_flow": True,
            "order_maintained": True,
            "timestamp_consistency": 1.0,
            "causality_preserved": True,
            "energy_level": 0.8,
            "burnout_risk": 0.2,
            "renewable_energy": True,
            "detected_rhythm": "steady",
            "adaptability": 0.8,
            "rhythm_harmony": 0.8,
        }
        
        result = system.run_full_cycle(metrics, state, context)
        
        # 철학 확인
        assert result["philosophy"] == "자기 돌봄 → 내부 흐름 → 세상과의 흐름"
        assert result["world_flow"]["principle"] == "착하게 살아라"
