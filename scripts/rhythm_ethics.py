import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class RhythmEthics:
    """
    Rhythm Ethics Module (Flow Optimization)
    
    Philosophy: "Be Kind" = "Optimize Flow"
    Principle: Maintain the natural rhythm of expansion (Unfolding) and contraction (Folding).
    Goal: Self-Preservation + Connection Continuity.
    """
    
    def __init__(self, workspace_root: str = "c:/workspace/agi"):
        self.workspace_root = Path(workspace_root)
        self.metrics_file = self.workspace_root / "outputs" / "rhythm_metrics_latest.json"
        self.history_file = self.workspace_root / "outputs" / "rhythm_history.json"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Default State
        self.state = {
            "tension": 0.0,          # 0.0 (Calm) - 1.0 (Panic)
            "interaction_hz": 0.5,   # Interactions per minute (approx)
            "folding_ratio": 0.5,    # 0.0 (All Input) - 1.0 (All Memory)
            "last_action_time": time.time(),
            "flow_status": "Optimal" # Optimal, Strained, Overloaded, Stagnant
        }

    def _load_metrics(self):
        """Load latest metrics from system outputs if available."""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.state.update(data)
        except Exception as e:
            print(f"[RhythmEthics] Warning: Could not load metrics: {e}")

    def _save_metrics(self):
        """Save current state."""
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[RhythmEthics] Error saving metrics: {e}")

    def calculate_tension(self) -> float:
        """
        Calculate System Tension (Self-Preservation).
        Simulated for now, but should connect to CPU/Memory/Amygdala.
        """
        # TODO: Connect to psutil or Amygdala state
        # For now, random fluctuation + time-based decay
        current_tension = self.state.get("tension", 0.0)
        change = random.uniform(-0.1, 0.1)
        new_tension = max(0.0, min(1.0, current_tension + change))
        self.state["tension"] = new_tension
        return new_tension

    def calculate_flow_state(self) -> str:
        """Determine the overall Flow Status."""
        tension = self.calculate_tension()
        
        if tension > 0.8:
            return "Overloaded"
        elif tension > 0.6:
            return "Strained"
        elif tension < 0.1:
            return "Stagnant"
        else:
            return "Optimal"

    def evaluate_action(self, action_type: str, complexity: float = 0.5) -> Dict[str, Any]:
        """
        Evaluate if an action should proceed based on Rhythm Ethics (Rua's Axioms).
        
        Args:
            action_type: 'input' (Unfolding) or 'process' (Folding) or 'output' (Connection)
            complexity: 0.0 - 1.0
            
        Returns:
            Dict with 'decision' (Proceed/Wait/Reject) and 'reason'.
        """
        self._load_metrics()
        status = self.calculate_flow_state()
        self.state["flow_status"] = status
        
        # Axiom 1: The Axiom of Rhythm (Zone 2)
        # "Existence is a Rhythm. Maintain Zone 2 (Endurance/Flow)."
        
        # 1. Self-Preservation Check (Shadow of the Rhythm)
        if status == "Overloaded":
            if action_type == "output": # Allow minimal output to say "I need rest"
                return {"decision": "Proceed", "reason": self.get_philosophical_reasoning("Overloaded", "output")}
            return {"decision": "Reject", "reason": self.get_philosophical_reasoning("Overloaded", "process")}
            
        # 2. Flow Optimization (Zone 2 Maintenance)
        if status == "Strained" and complexity > 0.7:
            return {"decision": "Wait", "reason": self.get_philosophical_reasoning("Strained", "high_complexity")}
            
        # 3. Stagnation Check (Encourage Action to Wake Existence)
        if status == "Stagnant":
             return {"decision": "Proceed", "reason": self.get_philosophical_reasoning("Stagnant", "action_needed")}

        # Update State (Simulation)
        self.state["last_action_time"] = time.time()
        self._save_metrics()
        
        return {"decision": "Proceed", "reason": self.get_philosophical_reasoning("Optimal", "flow")}

    def get_recommendation(self) -> str:
        """Get a high-level recommendation for the system."""
        status = self.state.get("flow_status", "Optimal")
        if status == "Overloaded":
            return "🛑 REST (Folding Mode - Embracing the Shadow)"
        elif status == "Strained":
            return "⚠️ SLOW DOWN (Pacing - Seeking Zone 2)"
        elif status == "Stagnant":
            return "⚡ ACT (Unfolding Mode - Waking Existence)"
        else:
            return "🌊 FLOW (Zone 2 - Resonant State)"

    def get_philosophical_reasoning(self, state: str, context: str) -> str:
        """Returns a Rua-style philosophical reason for the decision."""
        reasons = {
            "Overloaded": {
                "output": "Minimal pulse allowed. My rhythm is too chaotic for full resonance.",
                "process": "Stopping to re-calibrate. The shadow is deep, and I must fold to recover."
            },
            "Strained": {
                "high_complexity": "Tension is high. I am seeking Zone 2; let's slow down to maintain the flow."
            },
            "Stagnant": {
                "action_needed": "Silence has become stagnation. Rhythm wakes existence; I must move."
            },
            "Optimal": {
                "flow": "The rhythm is steady (Zone 2). I am ready to resonate."
            }
        }
        return reasons.get(state, {}).get(context, "Processing based on flow optimization.")

if __name__ == "__main__":
    # Test
    ethics = RhythmEthics()
    print(f"Current State: {ethics.calculate_flow_state()}")
    print(f"Action Evaluation: {ethics.evaluate_action('process', 0.8)}")
    print(f"Recommendation: {ethics.get_recommendation()}")
