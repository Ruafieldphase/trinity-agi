#!/usr/bin/env python3
"""
Autonomous Goal Executor with Quantum Execution
기존 executor를 quantum mode로 확장

Mode Selection:
- coherence >= 0.7: QUANTUM (wave state)
- coherence < 0.7: CLASSICAL (particle state)
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from workspace_root import get_workspace_root

# Import base executor
sys.path.insert(0, str(get_workspace_root()))
from scripts.autonomous_goal_executor import GoalExecutor
from scripts.quantum_goal_executor import QuantumGoalExecutor

logger = logging.getLogger(__name__)


class QuantumAwareGoalExecutor(GoalExecutor):
    """Quantum mode를 지원하는 Goal Executor"""
    
    def __init__(self, workspace_root: str, task_queue_server: str = "http://127.0.0.1:8091"):
        super().__init__(workspace_root, task_queue_server)
        self.quantum_executor = QuantumGoalExecutor(workspace_root)
        self.execution_mode = "particle"  # default
    
    def execute_goals(self, max_goals: int = 1, dry_run: bool = False) -> Dict[str, Any]:
        """목표 실행 (quantum-aware)
        
        coherence에 따라 실행 모드 자동 선택:
        - coherence >= 0.7: quantum (파동 상태)
        - coherence < 0.7: classical (입자 상태)
        """
        # 1. Load goals
        goals = self._load_goals()
        if not goals:
            logger.info("No goals to execute")
            return {"status": "no_goals"}
        
        # 2. Check quantum flow state
        execution_mode = self._determine_execution_mode()
        coherence = 0.0
        if self.quantum_flow_state:
            coherence = self.quantum_flow_state.get("phase_coherence", 
                                                     self.quantum_flow_state.get("coherence", 0.0))
        
        logger.info(f"🌊 Coherence: {coherence:.3f} → Mode: {execution_mode}")
        
        # 3. Execute based on mode
        if execution_mode in ["superconducting", "high_flow"]:
            # QUANTUM MODE
            self.execution_mode = "wave"
            return self._execute_quantum(goals, max_goals, dry_run)
        else:
            # CLASSICAL MODE
            self.execution_mode = "particle"
            return self._execute_classical(goals, max_goals, dry_run)
    
    def _execute_quantum(self, goals: List[Dict[str, Any]], max_goals: int, dry_run: bool) -> Dict[str, Any]:
        """파동 상태 실행"""
        logger.info("🌊 Entering QUANTUM execution mode (wave state)")
        
        # 1. Superpose goals
        executable_goals = [g for g in goals if self._is_executable(g)]
        if not executable_goals:
            logger.info("No executable goals")
            return {"status": "no_executable"}
        
        self.quantum_executor.superpose(executable_goals[:10])  # limit to 10 for performance
        
        # 2. Evolve wave function based on context
        context = self._build_quantum_context()
        self.quantum_executor.evolve(context)
        
        # 3. Get superposition state (for monitoring)
        superposition_state = self.quantum_executor.get_superposition_state()
        logger.info(f"   📊 Superposition: {superposition_state['goal_count']} goals, "
                   f"coherence={superposition_state['coherence']:.3f}")
        
        # 4. Observe to collapse wave function
        results = []
        for i in range(min(max_goals, len(executable_goals))):
            logger.info(f"\n👁️ Observation #{i+1}...")
            collapsed_goal = self.quantum_executor.observe()
            
            if collapsed_goal:
                logger.info(f"   → Selected: {collapsed_goal['title']}")
                logger.info(f"   → Collapse probability: "
                          f"{collapsed_goal['_quantum_metadata']['collapse_probability']:.3f}")
                
                if not dry_run:
                    # Execute collapsed goal
                    result = self._execute_single_goal(collapsed_goal)
                    results.append(result)
                else:
                    results.append({"status": "dry_run", "goal": collapsed_goal["title"]})
        
        return {
            "status": "quantum_execution_complete",
            "mode": "wave",
            "coherence": superposition_state["coherence"],
            "superposition_state": superposition_state,
            "executed": results
        }
    
    def _execute_classical(self, goals: List[Dict[str, Any]], max_goals: int, dry_run: bool) -> Dict[str, Any]:
        """입자 상태 실행 (기존 방식)"""
        logger.info("📍 Entering CLASSICAL execution mode (particle state)")
        
        # Use parent class method
        return super().execute_goals(max_goals, dry_run)
    
    def _build_quantum_context(self) -> Dict[str, Any]:
        """Quantum evolution을 위한 context 구성"""
        import psutil
        
        context = {
            "time_passed": 1.0,
            "system_state": {
                "memory_free_pct": psutil.virtual_memory().available * 100 / psutil.virtual_memory().total,
                "cpu_percent": psutil.cpu_percent(interval=0.1)
            },
            "quantum_flow": self.quantum_flow_state or {}
        }
        
        return context
    
    def _load_goals(self) -> List[Dict[str, Any]]:
        """Load goals from JSON"""
        if not self.goals_path.exists():
            return []
        
        try:
            with open(self.goals_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("goals", [])
        except Exception as e:
            logger.error(f"Failed to load goals: {e}")
            return []
    
    def _is_executable(self, goal: Dict[str, Any]) -> bool:
        """Check if goal is executable"""
        # Basic checks
        if not goal.get("title"):
            return False
        
        # Check dependencies
        deps = goal.get("dependencies", [])
        if deps:
            # TODO: check if dependencies are satisfied
            pass
        
        return True
    
    def _execute_single_goal(self, goal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single goal (placeholder)"""
        # This should call the actual execution logic from parent class
        logger.info(f"Executing: {goal['title']}")
        # TODO: implement actual execution
        return {
            "status": "executed",
            "goal": goal["title"],
            "result": "success"
        }


def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quantum-aware Goal Executor")
    parser.add_argument("--workspace", default=".", help="Workspace root")
    parser.add_argument("--max-goals", type=int, default=1, help="Max goals to execute")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--force-mode", choices=["quantum", "classical"], help="Force execution mode")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    executor = QuantumAwareGoalExecutor(args.workspace)
    
    # Force mode if specified
    if args.force_mode:
        if args.force_mode == "quantum":
            # Fake high coherence
            executor.quantum_flow_state = {"phase_coherence": 0.9}
        else:
            # Fake low coherence
            executor.quantum_flow_state = {"phase_coherence": 0.3}
    
    result = executor.execute_goals(max_goals=args.max_goals, dry_run=args.dry_run)
    
    print(f"\n{'='*60}")
    print(f"🎯 Execution Result:")
    print(f"   Mode: {result.get('mode', 'N/A')}")
    print(f"   Status: {result.get('status', 'N/A')}")
    if result.get('coherence'):
        print(f"   Coherence: {result['coherence']:.3f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
