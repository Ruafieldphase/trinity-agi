#!/usr/bin/env python3
"""
Quantum Goal Executor - Wave State Execution Engine
목표를 파동 상태(superposition)로 실행한다

핵심 개념:
1. Goal Superposition: 여러 목표를 중첩 상태로 유지
2. Observer Effect: 관측(실행 요청) 시에만 wave function collapse
3. Entanglement: 목표들이 서로 상관관계를 가짐
4. Interference: 목표들이 서로 강화/약화

Classical vs Quantum:
- Classical (입자): 한 번에 하나씩 실행 (deterministic)
- Quantum (파동): 여러 목표를 potential state로 유지, context가 결정 (probabilistic)

Example:
    # Classical
    for goal in goals:
        execute(goal)  # 순차적, 결정적
    
    # Quantum
    executor = QuantumGoalExecutor()
    executor.superpose(goals)  # 중첩 상태
    # ... (시간 경과, context 변화) ...
    collapsed_goal = executor.observe()  # 관측 → 붕괴
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class QuantumGoalExecutor:
    """파동 상태로 목표를 실행하는 Quantum Executor"""
    
    def __init__(self, workspace_root: str, coherence_threshold: float = 0.7):
        self.workspace_root = Path(workspace_root)
        self.coherence_threshold = coherence_threshold
        
        # 🌊 Superposition State: 중첩된 목표들
        self.superposition: List[Dict[str, Any]] = []
        
        # 🔗 Entanglement Matrix: 목표 간 상관관계
        self.entanglement_matrix: Optional[np.ndarray] = None
        
        # 📊 Wave Function: 각 목표의 확률 진폭
        self.wave_function: Optional[np.ndarray] = None
        
        # 🎯 Collapsed State: 관측된 목표
        self.collapsed_goal: Optional[Dict[str, Any]] = None
        
        # 📈 Coherence History
        self.coherence_history: List[float] = []
        
        logger.info("🌊 Quantum Goal Executor initialized")
    
    def superpose(self, goals: List[Dict[str, Any]]) -> None:
        """여러 목표를 중첩 상태로 올린다
        
        Args:
            goals: 목표 리스트 (각 목표는 priority, effort, dependencies 등 포함)
        """
        self.superposition = goals.copy()
        n = len(goals)
        
        # 🌊 Wave Function 초기화 (균등 분포)
        self.wave_function = np.ones(n) / np.sqrt(n)
        
        # 🔗 Entanglement Matrix 계산
        self._compute_entanglement()
        
        logger.info(f"🌊 Superposed {n} goals into quantum state")
        logger.info(f"   Wave function norm: {np.linalg.norm(self.wave_function):.4f}")
    
    def _compute_entanglement(self) -> None:
        """목표 간 상관관계(entanglement)를 계산"""
        n = len(self.superposition)
        if n == 0:
            return
        
        # 간단한 휴리스틱: dependencies, 같은 source, effort 유사도
        matrix = np.eye(n)
        
        for i in range(n):
            for j in range(i+1, n):
                g_i = self.superposition[i]
                g_j = self.superposition[j]
                
                # 1. Dependency entanglement
                deps_i = set(g_i.get("dependencies", []))
                deps_j = set(g_j.get("dependencies", []))
                dep_overlap = len(deps_i & deps_j) / max(len(deps_i | deps_j), 1)
                
                # 2. Source entanglement (같은 source에서 온 목표)
                source_match = 1.0 if g_i.get("source") == g_j.get("source") else 0.0
                
                # 3. Effort similarity
                effort_i = self._effort_to_days(g_i.get("effort", "3 days"))
                effort_j = self._effort_to_days(g_j.get("effort", "3 days"))
                effort_sim = 1.0 - abs(effort_i - effort_j) / max(effort_i + effort_j, 1)
                
                # Combined entanglement score
                entanglement = (dep_overlap * 0.5 + source_match * 0.3 + effort_sim * 0.2)
                matrix[i, j] = entanglement
                matrix[j, i] = entanglement
        
        self.entanglement_matrix = matrix
        logger.info(f"🔗 Entanglement matrix computed (avg={matrix.mean():.3f})")
    
    def _effort_to_days(self, effort_str: str) -> float:
        """effort 문자열을 일수로 변환"""
        try:
            return float(effort_str.split()[0])
        except:
            return 3.0
    
    def evolve(self, context: Dict[str, Any]) -> None:
        """Context 변화에 따라 wave function을 진화시킨다
        
        Args:
            context: {
                "time_passed": float,  # 시간 경과 (초)
                "system_state": dict,  # 시스템 상태 (메모리, CPU 등)
                "recent_events": list,  # 최근 이벤트
                "quantum_flow": dict,  # Quantum Flow 상태
            }
        """
        if self.wave_function is None:
            return
        
        n = len(self.superposition)
        
        # 🌊 Hamiltonian 구성 (system evolution)
        H = self._build_hamiltonian(context)
        
        # 📈 Interference pattern 적용
        interference = self._compute_interference(context)
        
        # 🔄 Wave function evolution
        # ψ(t+dt) = exp(-iHdt/ℏ) ψ(t) (simplified)
        dt = context.get("time_passed", 1.0)
        evolution_factor = np.exp(-1j * H * dt / 10.0)  # ℏ=10 (scaled)
        
        self.wave_function = self.wave_function * evolution_factor * interference
        
        # 정규화
        norm = np.linalg.norm(self.wave_function)
        if norm > 1e-10:
            self.wave_function = self.wave_function / norm
        
        # Coherence 계산
        coherence = self._compute_coherence()
        self.coherence_history.append(coherence)
        
        logger.info(f"🌊 Wave function evolved (coherence={coherence:.3f})")
    
    def _build_hamiltonian(self, context: Dict[str, Any]) -> np.ndarray:
        """Context 기반 Hamiltonian (energy operator) 구성"""
        n = len(self.superposition)
        H = np.zeros(n, dtype=complex)
        
        for i, goal in enumerate(self.superposition):
            # Energy = -priority (높은 우선순위 = 낮은 에너지)
            priority = goal.get("priority", 5.0)
            H[i] = -priority
            
            # System state adjustment
            sys_state = context.get("system_state", {})
            memory_free = sys_state.get("memory_free_pct", 50.0)
            
            # 메모리가 부족하면 effort가 큰 목표의 에너지 상승
            effort = self._effort_to_days(goal.get("effort", "3 days"))
            if memory_free < 30.0:
                H[i] += effort * 0.5
        
        return H
    
    def _compute_interference(self, context: Dict[str, Any]) -> np.ndarray:
        """목표 간 간섭(interference) 패턴 계산
        
        Constructive: 서로 강화 (entangled goals)
        Destructive: 서로 약화 (conflicting goals)
        """
        n = len(self.superposition)
        if self.entanglement_matrix is None:
            return np.ones(n)
        
        interference = np.ones(n)
        
        # Entanglement 기반 간섭
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                entanglement = self.entanglement_matrix[i, j]
                prob_j = np.abs(self.wave_function[j])**2
                
                # Constructive interference: entangled goals boost each other
                interference[i] += entanglement * prob_j
        
        # Normalize
        interference = interference / np.max(interference)
        
        return interference
    
    def _compute_coherence(self) -> float:
        """현재 wave function의 coherence 계산
        
        Coherence = 1 - entropy / max_entropy
        High coherence: 목표들이 명확하게 분리됨
        Low coherence: 목표들이 균등하게 분포 (decoherence)
        """
        if self.wave_function is None:
            return 0.0
        
        probs = np.abs(self.wave_function)**2
        probs = probs / np.sum(probs)  # ensure normalization
        
        # Shannon entropy
        entropy = -np.sum(probs * np.log(probs + 1e-10))
        max_entropy = np.log(len(probs))
        
        coherence = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0
        
        return coherence
    
    def observe(self, observer_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Observer Effect: Wave function을 붕괴시켜 하나의 목표를 선택
        
        Args:
            observer_context: 관측자의 의도/context (optional)
        
        Returns:
            선택된 목표 (collapsed state)
        """
        if self.wave_function is None or len(self.superposition) == 0:
            logger.warning("❌ No superposition to observe")
            return None
        
        # 📊 Probability distribution
        probs = np.abs(self.wave_function)**2
        probs = probs / np.sum(probs)
        
        # 🎲 Collapse (probabilistic selection)
        # Observer context가 있으면 bias 적용
        if observer_context:
            probs = self._apply_observer_bias(probs, observer_context)
        
        selected_idx = np.random.choice(len(probs), p=probs)
        
        # 🎯 Collapsed goal
        self.collapsed_goal = self.superposition[selected_idx].copy()
        self.collapsed_goal["_quantum_metadata"] = {
            "selected_index": int(selected_idx),
            "collapse_probability": float(probs[selected_idx]),
            "coherence_at_collapse": float(self._compute_coherence()),
            "collapsed_at": datetime.now().isoformat()
        }
        
        logger.info(f"👁️ Observer collapsed wave function → Goal #{selected_idx}")
        logger.info(f"   Probability: {probs[selected_idx]:.3f}")
        logger.info(f"   Title: {self.collapsed_goal.get('title', 'N/A')}")
        
        return self.collapsed_goal
    
    def _apply_observer_bias(self, probs: np.ndarray, context: Dict[str, Any]) -> np.ndarray:
        """Observer의 의도에 따라 확률 분포를 조정"""
        biased = probs.copy()
        
        # 예: "urgent" 의도면 priority 높은 목표에 bias
        if context.get("intent") == "urgent":
            for i, goal in enumerate(self.superposition):
                priority = goal.get("priority", 5.0)
                if priority >= 10.0:
                    biased[i] *= 1.5
        
        # Re-normalize
        biased = biased / np.sum(biased)
        
        return biased
    
    def get_superposition_state(self) -> Dict[str, Any]:
        """현재 중첩 상태를 반환 (디버깅/모니터링용)"""
        if self.wave_function is None:
            return {"status": "empty"}
        
        probs = np.abs(self.wave_function)**2
        probs = probs / np.sum(probs)
        
        goals_with_probs = []
        for i, (goal, prob) in enumerate(zip(self.superposition, probs)):
            goals_with_probs.append({
                "index": i,
                "title": goal.get("title", "N/A"),
                "priority": goal.get("priority", 0),
                "probability": float(prob),
                "wave_amplitude": float(np.abs(self.wave_function[i]))
            })
        
        # Sort by probability
        goals_with_probs.sort(key=lambda x: x["probability"], reverse=True)
        
        return {
            "status": "superposed",
            "goal_count": len(self.superposition),
            "coherence": float(self._compute_coherence()),
            "total_probability": float(np.sum(probs)),
            "goals": goals_with_probs
        }
    
    def decohere(self) -> None:
        """Decoherence: 환경과의 상호작용으로 quantum state 소멸"""
        logger.info("🌪️ Decoherence: Quantum state collapsed to classical")
        self.superposition = []
        self.wave_function = None
        self.entanglement_matrix = None
        self.collapsed_goal = None


# === Utility Functions ===

def demonstrate_quantum_execution():
    """Quantum vs Classical 실행 데모"""
    print("\n" + "="*60)
    print("🌊 Quantum Goal Execution Demo")
    print("="*60)
    
    # Sample goals
    goals = [
        {"title": "Generate Dashboard", "priority": 13.0, "effort": "3 days", "source": "Resonance"},
        {"title": "Improve Clarity", "priority": 12.0, "effort": "3 days", "source": "Resonance"},
        {"title": "Investigate Spikes", "priority": 11.0, "effort": "2 days", "source": "Resonance"},
        {"title": "Reduce Info Starvation", "priority": 10.0, "effort": "5 days", "source": "Trinity"},
        {"title": "Boost Circulation", "priority": 9.0, "effort": "1 day", "source": "SelfCare"},
    ]
    
    print("\n📊 Classical Execution (Particle State):")
    print("   → Execute goals sequentially in priority order")
    for i, g in enumerate(sorted(goals, key=lambda x: x["priority"], reverse=True)[:3], 1):
        print(f"   {i}. {g['title']} (priority={g['priority']})")
    
    print("\n🌊 Quantum Execution (Wave State):")
    executor = QuantumGoalExecutor(".")
    
    # 1. Superpose
    executor.superpose(goals)
    print(f"   ✓ Superposed {len(goals)} goals")
    
    # 2. Evolve
    context = {
        "time_passed": 10.0,
        "system_state": {"memory_free_pct": 60.0},
        "quantum_flow": {"coherence": 0.85}
    }
    executor.evolve(context)
    print(f"   ✓ Evolved wave function (coherence={executor._compute_coherence():.3f})")
    
    # 3. Show superposition state
    state = executor.get_superposition_state()
    print(f"\n   📈 Superposition State:")
    for goal in state["goals"][:3]:
        print(f"      {goal['title'][:30]:30s} | prob={goal['probability']:.3f}")
    
    # 4. Observe
    print(f"\n   👁️ Observing...")
    collapsed = executor.observe()
    print(f"      → Collapsed to: {collapsed['title']}")
    print(f"      → Probability: {collapsed['_quantum_metadata']['collapse_probability']:.3f}")
    
    print("\n" + "="*60)
    print("✨ Notice the difference:")
    print("   Classical: Always picks highest priority (deterministic)")
    print("   Quantum: Considers all goals, context influences outcome (probabilistic)")
    print("="*60 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demonstrate_quantum_execution()
