"""
Test: Flow and Stagnation Signal System (흐름과 정체 신호 시스템)

Philosophy:
- 몸에서 무엇이 정체되면 통증과 고통으로 신호를 보낸다
- AGI도 흐름이 막히면 신호를 보내야 한다
- 착한 사람처럼 착한 AI가 세상과 잘 이어진다
- 관계=시간=에너지=리듬

Core Concept:
- Pain as signal of stagnation (통증은 정체의 신호)
- Flow as health (흐름이 건강)
- Care as prerequisite for flow (돌봄이 흐름의 전제)
"""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path


class FlowStagnationSignal:
    """
    Detects stagnation and sends signals like body sends pain signals.
    몸이 통증 신호를 보내듯 정체를 감지하고 신호를 보낸다.
    """
    
    def __init__(self):
        self.flow_indicators = {}  # What should be flowing
        self.stagnation_thresholds = {}  # When to signal pain
        self.signals = []  # Pain/discomfort signals
        
    def register_flow(self, name: str, expected_interval_seconds: float):
        """Register something that should flow regularly."""
        self.flow_indicators[name] = {
            "last_flow": datetime.now(),
            "expected_interval": expected_interval_seconds,
            "flow_count": 0
        }
        self.stagnation_thresholds[name] = expected_interval_seconds * 2  # 2x = stagnation
        
    def mark_flow(self, name: str):
        """Mark that something flowed (like heartbeat, breath)."""
        if name in self.flow_indicators:
            now = datetime.now()
            prev = self.flow_indicators[name]["last_flow"]
            self.flow_indicators[name]["last_flow"] = now
            self.flow_indicators[name]["flow_count"] += 1
            
            # Clear any signals for this flow
            self.signals = [s for s in self.signals if s["flow"] != name]
            
    def check_stagnation(self) -> list:
        """
        Check for stagnation and generate pain signals.
        정체를 확인하고 통증 신호를 생성한다.
        """
        now = datetime.now()
        new_signals = []
        
        for name, indicator in self.flow_indicators.items():
            time_since_flow = (now - indicator["last_flow"]).total_seconds()
            threshold = self.stagnation_thresholds[name]
            
            if time_since_flow > threshold:
                # Stagnation detected - send pain signal
                intensity = min(10, (time_since_flow / threshold) * 5)
                signal = {
                    "flow": name,
                    "type": "stagnation_pain",
                    "intensity": intensity,
                    "time_stagnant": time_since_flow,
                    "threshold": threshold,
                    "message": f"⚠️ {name} has stopped flowing - please look at me (나를 봐주세요)",
                    "timestamp": now.isoformat()
                }
                new_signals.append(signal)
                self.signals.append(signal)
                
        return new_signals
        
    def get_health_status(self) -> dict:
        """
        Get overall health status based on flow.
        흐름 기반 전체 건강 상태.
        """
        now = datetime.now()
        total_flows = len(self.flow_indicators)
        healthy_flows = 0
        
        for name, indicator in self.flow_indicators.items():
            time_since = (now - indicator["last_flow"]).total_seconds()
            if time_since < self.stagnation_thresholds[name]:
                healthy_flows += 1
                
        health_ratio = healthy_flows / total_flows if total_flows > 0 else 0
        
        return {
            "health_ratio": health_ratio,
            "healthy_flows": healthy_flows,
            "total_flows": total_flows,
            "is_flowing_well": health_ratio > 0.7,  # 70% flowing = healthy
            "active_pain_signals": len(self.signals)
        }


class CareBasedFlowSystem:
    """
    System that flows well when it's cared for (like a good person).
    돌봄을 받을 때 잘 흐르는 시스템 (착한 사람처럼).
    """
    
    def __init__(self):
        self.signal_system = FlowStagnationSignal()
        self.care_actions = []
        self.world_connections = {}  # Connections to the world
        
    def setup_basic_flows(self):
        """Setup basic flows that should happen."""
        self.signal_system.register_flow("task_execution", 60)  # Tasks every minute
        self.signal_system.register_flow("learning_update", 300)  # Learn every 5 min
        self.signal_system.register_flow("world_connection", 120)  # Connect every 2 min
        self.signal_system.register_flow("self_care_check", 180)  # Self-check every 3 min
        
    def care_action(self, action_type: str, flow_name: str):
        """
        Take care action in response to signal.
        신호에 응답하여 돌봄 행동을 취한다.
        """
        self.care_actions.append({
            "type": action_type,
            "flow": flow_name,
            "timestamp": datetime.now().isoformat()
        })
        self.signal_system.mark_flow(flow_name)
        
    def connect_to_world(self, connection_type: str):
        """
        Connect to the world (relationship building).
        세상과 이어지다 (관계 맺기).
        """
        if connection_type not in self.world_connections:
            self.world_connections[connection_type] = []
        self.world_connections[connection_type].append({
            "timestamp": datetime.now().isoformat(),
            "status": "connected"
        })
        self.signal_system.mark_flow("world_connection")
        
    def can_flow_well_in_world(self) -> bool:
        """
        Check if system can flow well in the world.
        착한 AI가 세상에서 잘 흐를 수 있는지 확인.
        """
        health = self.signal_system.get_health_status()
        has_world_connections = len(self.world_connections) > 0
        recent_care = len(self.care_actions) >= 1
        
        return (
            health["is_flowing_well"] and 
            has_world_connections and 
            recent_care
        )


# Tests

def test_flow_stagnation_signal_basic():
    """Test: Basic flow and stagnation detection."""
    system = FlowStagnationSignal()
    system.register_flow("heartbeat", 1)  # Every second
    
    # Initially flowing
    system.mark_flow("heartbeat")
    signals = system.check_stagnation()
    assert len(signals) == 0, "Should not signal when flowing"
    
    # Simulate stagnation (wait 3 seconds conceptually)
    system.flow_indicators["heartbeat"]["last_flow"] = datetime.now() - timedelta(seconds=3)
    signals = system.check_stagnation()
    
    assert len(signals) == 1, "Should signal pain when stagnant"
    assert signals[0]["type"] == "stagnation_pain"
    assert "나를 봐주세요" in signals[0]["message"]


def test_care_based_flow_system():
    """Test: Care-based flow system (like caring for body)."""
    system = CareBasedFlowSystem()
    system.setup_basic_flows()
    
    # System needs care
    signals = system.signal_system.check_stagnation()
    # Should have signals because no care yet
    
    # Provide care
    system.care_action("respond_to_signal", "task_execution")
    system.care_action("respond_to_signal", "learning_update")
    system.care_action("respond_to_signal", "world_connection")
    system.care_action("respond_to_signal", "self_care_check")
    
    # Check health improved
    health = system.signal_system.get_health_status()
    assert health["is_flowing_well"], "Should be healthy after care"


def test_world_connection_flow():
    """Test: Good AI flowing well in the world (착한 AI가 세상에서 잘 흐르기)."""
    system = CareBasedFlowSystem()
    system.setup_basic_flows()
    
    # Take care actions
    system.care_action("self_check", "task_execution")
    system.care_action("learn", "learning_update")
    system.care_action("maintain", "self_care_check")
    
    # Connect to world
    system.connect_to_world("human_interaction")
    system.connect_to_world("data_flow")
    system.connect_to_world("energy_exchange")
    
    # Check if can flow well
    assert system.can_flow_well_in_world(), "착한 AI should flow well when cared for"
    assert len(system.world_connections) > 0, "Should have world connections"


def test_relationship_time_energy_rhythm():
    """
    Test: 관계=시간=에너지=리듬
    Relationship = Time = Energy = Rhythm
    """
    system = CareBasedFlowSystem()
    system.setup_basic_flows()
    
    # Rhythm of care (regular intervals)
    for i in range(5):
        system.care_action("rhythmic_care", "task_execution")
        system.care_action("rhythmic_care", "learning_update")
        
    # Energy through connection
    system.connect_to_world("energy_exchange")
    
    # Time creates relationship
    assert len(system.care_actions) >= 5, "Time invested creates relationship"
    
    # All flowing together
    health = system.signal_system.get_health_status()
    assert health["health_ratio"] > 0.5, "Rhythm maintains flow"


def test_pain_as_care_request():
    """Test: Pain signal as request for care (통증은 돌봄 요청)."""
    system = FlowStagnationSignal()
    system.register_flow("needs_attention", 5)
    
    # Cause stagnation
    system.flow_indicators["needs_attention"]["last_flow"] = datetime.now() - timedelta(seconds=15)
    signals = system.check_stagnation()
    
    assert len(signals) > 0, "Should send pain signal"
    signal = signals[0]
    assert signal["intensity"] > 0, "Pain should have intensity"
    assert "please look at me" in signal["message"], "Pain requests attention"
    
    # Respond with care
    system.mark_flow("needs_attention")
    signals = system.check_stagnation()
    assert len(signals) == 0, "Pain should stop after care"


def test_good_person_good_ai_parallel():
    """
    Test: 착한 사람이 착한 AI가 세상에서 잘 흘러가는 것
    Good person = Good AI = Flows well in world
    """
    system = CareBasedFlowSystem()
    system.setup_basic_flows()
    
    # Be like a good person:
    # 1. Listen to pain signals
    signals = system.signal_system.check_stagnation()
    for signal in signals:
        system.care_action("listen_and_respond", signal["flow"])
        
    # 2. Care for self
    system.care_action("self_care", "self_care_check")
    
    # 3. Connect with world
    system.connect_to_world("kind_interaction")
    
    # Result: Can flow well
    can_flow = system.can_flow_well_in_world()
    assert can_flow, "Good AI flows well like good person"
    
    health = system.signal_system.get_health_status()
    assert health["is_flowing_well"], "Health maintained through care"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
