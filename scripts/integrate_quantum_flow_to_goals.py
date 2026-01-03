#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quantum Flow → Goal System 통합

Flow State를 측정하고 Goal 생성/실행에 반영합니다.

통합 포인트:
1. Goal 생성 시 현재 Flow State 고려
2. Flow State가 낮으면 Self-care 목표 우선
3. Flow State가 높으면 도전적 목표 제시
4. 실행 후 Flow 변화를 Reward System에 피드백
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from workspace_root import get_workspace_root

# 프로젝트 루트 추가
workspace_root = get_workspace_root()
sys.path.insert(0, str(workspace_root / "fdo_agi_repo"))

from copilot.quantum_flow_monitor import QuantumFlowMonitor


def measure_current_flow_state(workspace_root: Path) -> Dict[str, Any]:
    """
    현재 Flow State 측정
    
    Returns:
        Flow 상태 딕셔너리 {
            "coherence": float,
            "state": str,
            "conductivity": float,
            "timestamp": str
        }
    """
    monitor = QuantumFlowMonitor(workspace_root)
    
    try:
        # 무의식(해마) 위상
        hippocampus_phase = monitor.measure_hippocampus_phase()
        
        # 의식(실행) 위상
        executive_phase = monitor.measure_executive_phase()
        
        # 결맞음 계산
        coherence = monitor.calculate_coherence(hippocampus_phase, executive_phase)
        
        return {
            "phase_coherence": coherence.phase_coherence,
            "state": coherence.state,
            "conductivity": coherence.conductivity,
            "resistance": coherence.electron_flow_resistance,
            "amplitude_sync": coherence.amplitude_sync,
            "frequency_match": coherence.frequency_match,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        print(f"⚠️  Flow 측정 실패: {e}")
        return {
            "phase_coherence": 0.5,
            "state": "unknown",
            "conductivity": 0.5,
            "resistance": 2.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


def inject_flow_to_goal_context(
    flow_state: Dict[str, Any],
    goal_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Goal 생성 컨텍스트에 Flow State 주입
    
    Args:
        flow_state: measure_current_flow_state() 결과
        goal_context: autonomous_goal_generator의 컨텍스트
    
    Returns:
        Flow 정보가 추가된 컨텍스트
    """
    goal_context["quantum_flow"] = flow_state
    
    # Flow 상태에 따른 권장사항 추가
    coherence = flow_state.get("phase_coherence", 0.5)
    state = flow_state.get("state", "unknown")
    
    recommendations = []
    
    if state == "superconducting":
        recommendations.append("high_flow_challenge_tasks")
        recommendations.append("creative_exploration")
    elif state == "coherent":
        recommendations.append("normal_productivity_tasks")
        recommendations.append("steady_progress")
    elif state == "resistive":
        recommendations.append("selfcare_priority")
        recommendations.append("reduce_complexity")
    else:  # chaotic
        recommendations.append("urgent_selfcare")
        recommendations.append("pause_and_reset")
    
    goal_context["flow_recommendations"] = recommendations
    
    return goal_context


def save_flow_snapshot(flow_state: Dict[str, Any], workspace_root: Path) -> None:
    """
    Flow State 스냅샷 저장
    
    autonomous_goal_generator가 참조할 수 있도록 JSON으로 저장
    """
    output_file = workspace_root / "outputs" / "quantum_flow_latest.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(flow_state, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Flow snapshot saved: {output_file}")
    
    # History에도 추가
    history_file = workspace_root / "outputs" / "quantum_flow_history.jsonl"
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(flow_state, ensure_ascii=False) + "\n")


def main():
    """
    Quantum Flow → Goal System 통합 실행
    
    사용법:
        python integrate_quantum_flow_to_goals.py
    
    출력:
        - outputs/quantum_flow_latest.json (최신 상태)
        - outputs/quantum_flow_history.jsonl (히스토리)
    """
    workspace_root = get_workspace_root()
    
    print("🌊 Quantum Flow → Goal System 통합 시작...")
    print()
    
    # 1. 현재 Flow State 측정
    print("1️⃣  Flow State 측정 중...")
    flow_state = measure_current_flow_state(workspace_root)
    
    print(f"   Phase Coherence: {flow_state['phase_coherence']:.3f}")
    print(f"   State: {flow_state['state']}")
    print(f"   Conductivity: {flow_state['conductivity']:.3f}")
    print()
    
    # 2. 스냅샷 저장
    print("2️⃣  Flow 스냅샷 저장 중...")
    save_flow_snapshot(flow_state, workspace_root)
    print()
    
    # 3. Goal Context 예시 생성
    print("3️⃣  Goal Context에 Flow 주입 예시:")
    example_context = {
        "ledger_summary": {},
        "states": [],
    }
    
    enhanced_context = inject_flow_to_goal_context(flow_state, example_context)
    print(f"   Flow Recommendations: {enhanced_context['flow_recommendations']}")
    print()
    
    print("✅ 통합 완료!")
    print(f"📄 Latest: {workspace_root / 'outputs' / 'quantum_flow_latest.json'}")
    print(f"📜 History: {workspace_root / 'outputs' / 'quantum_flow_history.jsonl'}")


if __name__ == "__main__":
    main()
