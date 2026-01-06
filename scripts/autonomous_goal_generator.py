#!/usr/bin/env python3
"""
Autonomous Goal Generator - Trinity Integrated

자율 목표 생성 시스템 - Phase 1 구현 + Trinity 피드백 통합
Resonance Simulator + Autopoietic Trinity → 우선순위 목표 생성

입력:
- outputs/resonance_simulation_latest.json (Resonance 메트릭)
- outputs/trinity_synthesis_latest.json (Trinity 피드백) ⭐ NEW!
- outputs/core_enhanced_synthesis_latest.md (Legacy Trinity)
- fdo_agi_repo/memory/goal_tracker.json (완료된 목표 추적)

출력:
- outputs/autonomous_goals_latest.json (목표 리스트 JSON)
- outputs/autonomous_goals_latest.md (목표 리스트 Markdown)

Trinity 통합:
- HIGH 우선순위 권장사항 → 긴급도 +3.0
- MEDIUM 우선순위 권장사항 → 긴급도 +1.5
- 세션 Resonance Score → 임팩트 가중치

작성일: 2025-11-05 (Trinity 통합: 2025-11-05)
작성자: Autonomous Goal System
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from workspace_root import get_workspace_root

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Trinity 피드백 로더 임포트
TRINITY_AVAILABLE = False
try:
    from load_trinity_feedback import (
        load_trinity_high_priority,
        get_trinity_urgency_boost,
        get_session_resonance
    )
    from reward_tracker import RewardTracker  # 🧠 보상 기반 학습 추가
    TRINITY_AVAILABLE = True
except ImportError:
    logger.warning("Optional modules not available (load_trinity_feedback, reward_tracker)")
    TRINITY_AVAILABLE = False

# 🧠 Hippocampus 임포트 (장기 기억 시스템)
HIPPOCAMPUS_AVAILABLE = False
try:
    sys.path.insert(0, str(get_workspace_root() / "fdo_agi_repo"))
    from copilot.hippocampus import CopilotHippocampus
    HIPPOCAMPUS_AVAILABLE = True
    logger.info("✅ Hippocampus module loaded")
except ImportError as e:
    logger.warning(f"Hippocampus not available: {e}")
    HIPPOCAMPUS_AVAILABLE = False


# =============================================================================
# 1. 입력 로딩 (Input Loading)
# =============================================================================

def load_feedback_insights(path: str) -> Dict[str, Any]:
    """
    자율 목표 피드백 인사이트 로드
    
    Args:
        path: goal_feedback_insights.json 경로
        
    Returns:
        피드백 인사이트 딕셔너리 (없으면 빈 dict)
    """
    if not os.path.exists(path):
        logger.info(f"Feedback insights not found: {path}")
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"✅ Loaded feedback insights from: {path}")
        
        # 인사이트 요약 로깅
        if 'recommendations' in data:
            logger.info(f"   📊 {len(data['recommendations'])} 개의 추천사항 발견")
        if 'type_performance' in data:
            type_stats = data['type_performance'].get('type_stats', {})
            logger.info(f"   🎯 {len(type_stats)} 개의 목표 타입 분석됨")
        
        return data
    except Exception as e:
        logger.warning(f"Failed to load feedback insights: {e}")
        return {}

def load_resonance_metrics(path: str) -> Dict[str, Any]:
    """
    Resonance 메트릭을 로드한다.
    
    Args:
        path: resonance_simulation_latest.json 경로
        
    Returns:
        Resonance 메트릭 딕셔너리
    """
    if not os.path.exists(path):
        logger.warning(f"Resonance metrics not found: {path}")
        logger.warning("Using fallback default values")
        return {
            "final_state": {
                "info_density": 0.5,
                "resonance": 0.5,
                "entropy": 0.5,
                "horizon_crossings": 0
            }
        }
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded resonance metrics from: {path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load resonance metrics: {e}")
        raise


def load_trinity_report(path: str) -> str:
    """
    Trinity 보고서를 로드한다.
    
    Args:
        path: core_enhanced_synthesis_latest.md 경로
        
    Returns:
        Markdown 텍스트
    """
    if not os.path.exists(path):
        logger.warning(f"Trinity report not found: {path}")
        logger.warning("Using empty report")
        return ""
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"Loaded trinity report from: {path}")
        return content
    except Exception as e:
        logger.error(f"Failed to load trinity report: {e}")
        raise


def load_completed_goals(tracker_file: str, recent_hours: int = 48) -> Set[str]:
    """
    최근 N시간 이내 완료된 목표 제목을 로드한다.
    오래전 완료 목표는 상황이 다시 악화되면 재생성 가능하도록 제외하지 않음.
    
    Args:
        tracker_file: goal_tracker.json 경로
        recent_hours: 제외할 완료 목표의 최근 시간 범위 (기본 48시간)
        
    Returns:
        최근 완료된 목표 제목 집합 (소문자 정규화)
    """
    if not os.path.exists(tracker_file):
        logger.info(f"Goal tracker not found: {tracker_file}")
        return set()
    
    try:
        with open(tracker_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=recent_hours)
        completed = set()
        old_completed = 0
        
        for goal in data.get("goals", []):
            if goal["status"] == "completed":
                # completed_at 체크 (없으면 매우 오래전 것으로 간주하여 제외하지 않음)
                completed_at_str = goal.get("completed_at")
                if completed_at_str:
                    try:
                        completed_at = datetime.fromisoformat(completed_at_str.rstrip('Z'))
                        if completed_at > cutoff:
                            # 최근 완료 목표만 제외 집합에 추가
                            title_normalized = goal["title"].lower().strip()
                            completed.add(title_normalized)
                        else:
                            old_completed += 1
                    except Exception as e:
                        logger.warning(f"Invalid completed_at format for goal '{goal.get('title')}': {e}")
                else:
                    # completed_at이 없으면 오래된 목표로 간주
                    old_completed += 1
        
        logger.info(f"Loaded {len(completed)} recently completed goals (within {recent_hours}h), {old_completed} old completed goals can be regenerated")
        return completed
    except Exception as e:
        logger.warning(f"Failed to load goal tracker: {e}")
        return set()


def load_self_care_summary(path: str) -> Dict[str, Any]:
    """
    Self-care 요약(JSON)을 로드한다.

    Args:
        path: self_care_metrics_summary.json 경로

    Returns:
        요약 딕셔너리 (없으면 빈 dict)
    """
    if not os.path.exists(path):
        logger.info(f"Self-care summary not found: {path}")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded self-care summary from: {path}")
        return data
    except Exception as e:
        logger.warning(f"Failed to load self-care summary: {e}")
        return {}


def analyze_self_care_states(summary: Dict[str, Any]) -> List[str]:
    """
    Self-care 요약 데이터를 분석해 상태 태그를 생성한다.

    Args:
        summary: self_care_metrics_summary.json 로드 결과

    Returns:
        상태 태그 리스트 (예: ["selfcare_high_stagnation"])
    """
    if not summary:
        return []

    states: List[str] = []

    stagnation_avg = float(summary.get("stagnation_avg", 0.0))
    stagnation_p95 = float(summary.get("stagnation_p95", 0.0))
    stagnation_over_05 = int(summary.get("stagnation_over_05", 0))
    circulation_ok_rate = float(summary.get("circulation_ok_rate", 1.0))
    queue_ratio_avg = float(summary.get("queue_ratio_avg", 0.0))

    logger.info("Analyzing self-care summary:")
    logger.info(
        "  stagnation_avg=%.3f, stagnation_p95=%.3f, over_0.5=%d, circulation_ok=%.1f%%, queue_ratio=%.2f",
        stagnation_avg,
        stagnation_p95,
        stagnation_over_05,
        circulation_ok_rate * 100,
        queue_ratio_avg,
    )

    if stagnation_avg >= 0.4 or stagnation_p95 >= 0.9:
        states.append("selfcare_high_stagnation")
        logger.info("  → Detected: selfcare_high_stagnation")
    if stagnation_over_05 > 0:
        states.append("selfcare_stagnation_spikes")
        logger.info("  → Detected: selfcare_stagnation_spikes")
    if circulation_ok_rate < 0.75:
        states.append("selfcare_low_circulation")
        logger.info("  → Detected: selfcare_low_circulation")
    if queue_ratio_avg > 1.0:
        states.append("selfcare_queue_pressure")
        logger.info("  → Detected: selfcare_queue_pressure")

    # 🌊 Quantum Flow 상태 분석 추가
    quantum_flow = summary.get("quantum_flow", {})
    if quantum_flow and not quantum_flow.get("error"):
        flow_state = quantum_flow.get("state", "unknown")
        phase_coherence = float(quantum_flow.get("phase_coherence", 0.0))
        
        logger.info(f"  Quantum Flow: {flow_state} (coherence={phase_coherence:.2f})")
        
        if flow_state == "superconducting":
            states.append("quantum_flow_superconducting")
            logger.info("  → Detected: quantum_flow_superconducting (Goal 생성 최적)")
        elif flow_state == "coherent":
            states.append("quantum_flow_coherent")
            logger.info("  → Detected: quantum_flow_coherent (Goal 생성 권장)")
        elif flow_state == "resistive":
            states.append("quantum_flow_resistive")
            logger.info("  → Detected: quantum_flow_resistive (Self-care 필요)")
        elif flow_state == "chaotic":
            states.append("quantum_flow_chaotic")
            logger.info("  → Detected: quantum_flow_chaotic (휴식 필요)")

    if not states:
        states.append("selfcare_stable")
        logger.info("  → Detected: selfcare_stable")

    return states


# =============================================================================
# 2. Resonance 상태 분석 (Resonance State Analysis)
# =============================================================================

def analyze_resonance_state(metrics: Dict[str, Any]) -> List[str]:
    """
    Resonance 메트릭을 분석하여 시스템 상태를 진단한다.
    
    Args:
        metrics: Resonance 메트릭 딕셔너리
        
    Returns:
        상태 표시자 리스트 (예: ["info_overload", "low_resonance"])
    """
    states = []
    
    # final_state에서 메트릭 추출
    final_state = metrics.get("final_state", {})
    info_density = final_state.get("info_density", 0.5)
    resonance = final_state.get("resonance", 0.5)
    entropy = final_state.get("entropy", 0.5)
    horizon_crossings = final_state.get("horizon_crossings", 0)
    
    logger.info(f"Analyzing resonance state:")
    logger.info(f"  info_density={info_density:.3f}")
    logger.info(f"  resonance={resonance:.3f}")
    logger.info(f"  entropy={entropy:.3f}")
    logger.info(f"  horizon_crossings={horizon_crossings}")
    
    # 정보 밀도 분석
    if info_density > 0.7:
        states.append("info_overload")
        logger.info("  → Detected: info_overload")
    elif info_density < 0.3:
        states.append("info_starvation")
        logger.info("  → Detected: info_starvation")
    
    # 공명도 분석
    if resonance < 0.4:
        states.append("low_resonance")
        logger.info("  → Detected: low_resonance")
    elif resonance > 0.8:
        states.append("high_resonance")
        logger.info("  → Detected: high_resonance")
    
    # 엔트로피 분석
    if entropy > 0.5:
        states.append("high_entropy")
        logger.info("  → Detected: high_entropy")
    elif entropy < 0.2:
        states.append("low_entropy")
        logger.info("  → Detected: low_entropy")
    
    # 지평선 교차 분석
    if horizon_crossings > 5:
        states.append("unstable_dynamics")
        logger.info("  → Detected: unstable_dynamics")
    elif horizon_crossings < 2:
        states.append("stable_dynamics")
        logger.info("  → Detected: stable_dynamics")
    
    if not states:
        states.append("normal_operation")
        logger.info("  → No issues detected (normal operation)")
    
    return states


# =============================================================================
# 3. Trinity 피드백 추출 (Trinity Feedback Extraction)
# =============================================================================

def extract_trinity_feedback(report_content: str) -> Dict[str, Any]:
    """
    Trinity 보고서에서 핵심 피드백을 추출한다.
    
    Args:
        report_content: Markdown 텍스트
        
    Returns:
        {
            "lua_issues": list[str],
            "elo_status": str,
            "core_recommendations": list[dict]
        }
    """
    feedback = {
        "lua_issues": [],
        "elo_status": "unknown",
        "core_recommendations": []
    }
    
    if not report_content:
        logger.warning("Empty trinity report, returning empty feedback")
        return feedback
    
    # Lua 관찰 추출 (정/正)
    lua_section = re.search(
        r'## 📊 정\(正\) - 코어의 관찰 요약(.*?)(?=##|$)',
        report_content,
        re.DOTALL
    )
    if lua_section:
        lua_text = lua_section.group(1)
        # 표에서 메트릭 추출
        if "활동 Task | 0 |" in lua_text:
            feedback["lua_issues"].append("No active tasks")
        if "품질 메트릭 | 0 |" in lua_text:
            feedback["lua_issues"].append("No quality metrics")
    
    # Elo 검증 추출 (반/反)
    elo_section = re.search(
        r'## 🔬 반\(反\) - 엘로의 검증 요약(.*?)(?=##|$)',
        report_content,
        re.DOTALL
    )
    if elo_section:
        elo_text = elo_section.group(1)
        # 최종 판정 추출
        judgment_match = re.search(r'\*\*최종 판정\*\*:\s*(.+)', elo_text)
        if judgment_match:
            feedback["elo_status"] = judgment_match.group(1).strip()
    
    # Core 통합 권장사항 추출 (합/合)
    core_section = re.search(
        r'## 💡 합\(合\) - 통합 통찰(.*?)(?=##|$)',
        report_content,
        re.DOTALL
    )
    if core_section:
        core_text = core_section.group(1)
        
        # HIGH/MEDIUM/INFO 권장사항 추출
        recommendations = re.findall(
            r'### (🔴|🟡|✅) (\w+) - (\w+)\s+\*\*(.+?)\*\*',
            core_text
        )
        
        for emoji, priority, category, description in recommendations:
            priority_map = {"🔴": "HIGH", "🟡": "MEDIUM", "✅": "INFO"}
            feedback["core_recommendations"].append({
                "priority": priority_map.get(emoji, "UNKNOWN"),
                "category": category,
                "description": description
            })
    
    logger.info(f"Extracted trinity feedback:")
    logger.info(f"  lua_issues: {len(feedback['lua_issues'])} issues")
    logger.info(f"  elo_status: {feedback['elo_status']}")
    logger.info(f"  core_recommendations: {len(feedback['core_recommendations'])} items")
    
    return feedback


# =============================================================================
# 4. 목표 생성 (Goal Generation)
# =============================================================================

def generate_goals(
    states: List[str],
    trinity_feedback: Dict[str, Any],
    completed_goals: Set[str] = None,
    self_care_summary: Optional[Dict[str, Any]] = None,
    feedback_insights: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    시스템 상태와 Trinity 피드백, 피드백 인사이트를 결합하여 목표를 생성한다.
    완료된 목표는 제외한다.
    
    Args:
        states: 시스템 상태 표시자 리스트
        trinity_feedback: Trinity 피드백 딕셔너리
        completed_goals: 완료된 목표 제목 집합 (소문자 정규화)
        self_care_summary: Self-care 요약 (상태별 설명에 활용)
        feedback_insights: 피드백 인사이트 딕셔너리 (목표 타입 성능 등)
        
    Returns:
        목표 딕셔너리 리스트 (title, description, base_priority, source)
    """
    if completed_goals is None:
        completed_goals = set()
    summary = self_care_summary or {}
    insights = feedback_insights or {}

    goals = []
    
    # 🧠 Hippocampus: 장기 기억 기반 우선순위 부스트
    hippocampus_boost = {}
    if HIPPOCAMPUS_AVAILABLE:
        try:
            workspace_root = get_workspace_root()
            hippocampus = CopilotHippocampus(workspace_root)
            
            # 과거 성공한 Goal 패턴 회상
            success_memories = hippocampus.recall("goal success completed", top_k=10)
            
            # 성공 패턴에서 키워드 추출
            for memory in success_memories:
                data = memory.get("data", {})
                goal_type = data.get("type", "")
                importance = memory.get("importance", 0.5)
                
                if goal_type:
                    # 성공한 Goal 타입에 우선순위 부스트 부여
                    hippocampus_boost[goal_type] = hippocampus_boost.get(goal_type, 0) + importance
            
            if hippocampus_boost:
                logger.info(f"🧠 Hippocampus: {len(hippocampus_boost)} goal types boosted from memory")
                for goal_type, boost in sorted(hippocampus_boost.items(), key=lambda x: x[1], reverse=True)[:3]:
                    logger.info(f"   • {goal_type}: +{boost:.2f} priority boost")
        except Exception as e:
            logger.warning(f"Hippocampus recall failed: {e}")
    
    # 시스템 상태 기반 목표 생성 규칙
    GOAL_RULES = {
        "info_overload": {
            "title": "Simplify System Architecture",
            "description": "Reduce information density by refactoring complex modules",
            "base_priority": 8,
            "type": "analysis",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/generate_monitoring_report.ps1",
                "args": ["-Hours", "24"],
                "timeout": 600
            }
        },
        "info_starvation": {
            "title": "Increase Data Collection",
            "description": "Improve information density by collecting more metrics",
            "base_priority": 7,
            "type": "metric",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/system_health_check.ps1",
                "args": ["-Full"],
                "timeout": 300
            }
        },
        "low_resonance": {
            "title": "Refactor Core Components",
            "description": "Improve resonance by restructuring core logic",
            "base_priority": 9,
            "type": "analysis",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/autopoietic_trinity_cycle.ps1",
                "args": ["-Hours", "24"],
                "timeout": 900
            }
        },
        "high_resonance": {
            "title": "Maintain Current Approach",
            "description": "System resonance is high, continue current strategy",
            "base_priority": 5,
            "type": "report",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/generate_monitoring_report.ps1",
                "args": ["-Hours", "6"],
                "timeout": 300
            }
        },
        "high_entropy": {
            "title": "Improve Clarity and Structure",
            "description": "Reduce entropy through better organization",
            "base_priority": 7,
            "type": "analysis",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/summarize_realtime_pipeline.ps1",
                "args": ["-Lookback", "24", "-SparkLen", "60"],
                "timeout": 300
            }
        },
        "low_entropy": {
            "title": "Explore New Approaches",
            "description": "System may be too rigid, try experimental features",
            "base_priority": 6,
            "type": "experiment",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/generate_monitoring_report.ps1",
                "args": ["-Hours", "12"],
                "timeout": 300
            }
        },
        "unstable_dynamics": {
            "title": "Stabilize System Dynamics",
            "description": "Too many horizon crossings, need stabilization",
            "base_priority": 8,
            "type": "analysis",
            "executable": {
                "type": "python",
                "script": "${workspaceFolder}/scripts/bohm_implicate_explicate_analyzer.py",
                "args": ["--hours", "24"],
                "timeout": 300
            }
        },
        "stable_dynamics": {
            "title": "Incremental Improvements",
            "description": "System is stable, focus on gradual enhancements",
            "base_priority": 5,
            "type": "maintenance",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/system_health_check.ps1",
                "timeout": 180
            }
        },
        "normal_operation": {
            "title": "Monitor and Maintain",
            "description": "No issues detected, continue monitoring",
            "base_priority": 4,
            "type": "metric",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/quick_status.ps1",
                "timeout": 120
            }
        },
        "selfcare_high_stagnation": {
            "title": "Stabilize Self-Care Loop",
            "description": "Reduce stagnation levels by tuning Self-Care thresholds and routines",
            "base_priority": 9,
            "type": "self_care",
            "source": "self_care",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/update_self_care_metrics.ps1",
                "args": ["-Hours", "24", "-Json", "-OpenSummary"],
                "timeout": 420
            }
        },
        "selfcare_stagnation_spikes": {
            "title": "Investigate Self-Care Spikes",
            "description": "Analyze recent Self-Care spikes and implement mitigation actions",
            "base_priority": 8,
            "type": "self_care",
            "source": "self_care",
            "executable": {
                "type": "python",
                "script": "${workspaceFolder}/scripts/render_self_care_report.py",
                "timeout": 180
            }
        },
        "selfcare_low_circulation": {
            "title": "Restore Circulation Health",
            "description": "Increase circulation_ok_rate by addressing bottlenecks in care actions",
            "base_priority": 8,
            "type": "self_care",
            "source": "self_care",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/update_self_care_metrics.ps1",
                "args": ["-Hours", "24"],
                "timeout": 420
            }
        },
        "selfcare_queue_pressure": {
            "title": "Reduce Self-Care Queue Pressure",
            "description": "Lower queue usage ratio by clearing backlog and optimizing cadence",
            "base_priority": 7,
            "type": "self_care",
            "source": "self_care",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/quick_status.ps1",
                "timeout": 180
            }
        },
        "selfcare_stable": {
            "title": "Monitor Self-Care Baseline",
            "description": "Self-care metrics are stable; continue monitoring and logging",
            "base_priority": 5,
            "type": "self_care",
            "source": "self_care",
            "executable": {
                "type": "python",
                "script": "${workspaceFolder}/scripts/render_self_care_report.py",
                "timeout": 180
            }
        },
        # 🌊 Quantum Flow 기반 목표
        "quantum_flow_superconducting": {
            "title": "📊 Generate Performance Dashboard",
            "description": "Quantum Flow 초전도 상태! 완벽한 조건에서 포괄적인 성능 대시보드를 생성하세요",
            "base_priority": 10,
            "type": "monitoring",
            "source": "quantum_flow",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/generate_enhanced_dashboard.ps1",
                "args": ["-OpenBrowser"],
                "timeout": 600
            }
        },
        "quantum_flow_coherent": {
            "title": "⚡ Generate New Goals",
            "description": "Quantum Flow 코히런트 상태 - Goal 생성에 좋은 시점입니다",
            "base_priority": 8,
            "type": "goal_generation",
            "source": "quantum_flow",
            "executable": {
                # Python 스크립트이므로 PowerShell -File이 아닌 Python으로 실행
                "type": "python",
                "script": "${workspaceFolder}/scripts/autonomous_goal_generator.py",
                "args": ["--hours", "24"],
                "timeout": 600
            }
        },
        "quantum_flow_resistive": {
            "title": "🔧 Run Self-Care Maintenance",
            "description": "Quantum Flow 저항 상태 감지 - Self-care를 통해 시스템 개선 필요",
            "base_priority": 9,
            "type": "self_care",
            "source": "quantum_flow",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/update_self_care_metrics.ps1",
                "args": ["-Hours", "6"],
                "timeout": 420
            }
        },
        "quantum_flow_chaotic": {
            "title": "😴 System Rest Required",
            "description": "Quantum Flow 혼돈 상태 - 새로운 Goal 생성을 중단하고 휴식 권장",
            "base_priority": 3,
            "type": "rest",
            "source": "quantum_flow",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/quick_status.ps1",
                "timeout": 60
            }
        }
    }
    
    # 시스템 상태 기반 목표 생성
    for state in states:
        if state in GOAL_RULES:
            goal = GOAL_RULES[state].copy()
            goal["source"] = "resonance"
            goal.setdefault("metadata", {})
            
            # base_priority를 severity로 변환하여 metadata에 저장
            base_priority = goal.get("base_priority", 5)
            if base_priority >= 8:
                goal["metadata"]["severity"] = "critical"
            elif base_priority >= 6:
                goal["metadata"]["severity"] = "high"
            else:
                goal["metadata"]["severity"] = "medium"
            
            if state.startswith("selfcare_"):
                goal["source"] = goal.get("source", "self_care")
                goal.setdefault("metadata", {})
                goal["metadata"]["self_care"] = summary
                if summary:
                    stagnation_avg = summary.get("stagnation_avg")
                    circulation = summary.get("circulation_ok_rate")
                    if stagnation_avg is not None:
                        goal["description"] += f" (current stagnation_avg={stagnation_avg:.2f})"
                    if circulation is not None and state == "selfcare_low_circulation":
                        goal["description"] += f" (circulation_ok_rate={circulation*100:.1f}%)"
            
            # 완료된 목표인지 확인 (단, severity가 critical이면 variant로 재생성)
            title_normalized = goal["title"].lower().strip()
            severity = goal.get("metadata", {}).get("severity", "")
            
            if title_normalized in completed_goals:
                if severity == "critical":
                    # 심각한 상황이면 variant 생성
                    goal["title"] += " (재시도)"
                    logger.info(f"Critical state detected! Regenerating goal variant: {goal['title']}")
                else:
                    logger.info(f"Skipping completed goal: {goal['title']}")
                    continue
            
            goals.append(goal)
            logger.info(f"Generated goal from state ({state}): {goal['title']}")
    
    # Trinity 피드백 기반 목표 생성
    for rec in trinity_feedback.get("core_recommendations", []):
        if rec["priority"] == "HIGH":
            title = f"Address: {rec['category']}"
            title_normalized = title.lower().strip()
            
            # 완료된 목표인지 확인
            if title_normalized in completed_goals:
                logger.info(f"Skipping completed goal: {title}")
                continue
            
            goals.append({
                "title": title,
                "description": rec["description"],
                "base_priority": 8,
                "source": "trinity"
            })
            logger.info(f"Generated goal from trinity (HIGH): {rec['category']}")
        elif rec["priority"] == "MEDIUM":
            title = f"Improve: {rec['category']}"
            title_normalized = title.lower().strip()
            
            # 완료된 목표인지 확인
            if title_normalized in completed_goals:
                logger.info(f"Skipping completed goal: {title}")
                continue
            
            goals.append({
                "title": title,
                "description": rec["description"],
                "base_priority": 6,
                "source": "trinity"
            })
            logger.info(f"Generated goal from trinity (MEDIUM): {rec['category']}")
        elif rec["priority"] == "MEDIUM":
            goals.append({
                "title": f"Improve: {rec['category']}",
                "description": rec["description"],
                "base_priority": 6,
                "source": "trinity"
            })
            logger.info(f"Generated goal from trinity (MEDIUM): {rec['category']}")
    
    # 중복 제거
    goals = deduplicate_goals(goals)
    
    logger.info(f"Generated {len(goals)} unique goals")
    return goals, hippocampus_boost  # 🧠 장기 기억 부스트도 반환


def deduplicate_goals(goals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    중복 목표를 제거한다 (제목 기준).
    
    Args:
        goals: 목표 리스트
        
    Returns:
        중복 제거된 목표 리스트
    """
    seen_titles = set()
    unique_goals = []
    
    for goal in goals:
        title_lower = goal["title"].lower()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_goals.append(goal)
    
    if len(goals) > len(unique_goals):
        logger.info(f"Removed {len(goals) - len(unique_goals)} duplicate goals")
    
    return unique_goals


# =============================================================================
# 5. 우선순위 계산 (Goal Prioritization)
# =============================================================================

def calculate_urgency(goal: Dict[str, Any]) -> float:
    """
    긴급도를 계산한다 (0-10.0점).
    
    Trinity 통합:
    - HIGH 우선순위 → +3.0
    - MEDIUM 우선순위 → +1.5
    - 키워드 매칭 시 Trinity 부스트 적용
    
    Args:
        goal: 목표 딕셔너리
        
    Returns:
        긴급도 점수 (0.0-10.0)
    """
    urgency = 0.0
    desc_lower = goal["description"].lower()
    title = goal.get("title", "")
    
    # 키워드 기반 긴급도
    if "critical" in desc_lower or "urgent" in desc_lower:
        urgency += 3.0
    elif "warning" in desc_lower or "issue" in desc_lower:
        urgency += 2.0
    elif "notice" in desc_lower or "improve" in desc_lower:
        urgency += 1.0
    
    # Trinity HIGH 권장사항은 긴급도 +1
    if goal.get("source") == "trinity" and "Address" in title:
        urgency += 1.0

    if goal.get("source") == "self_care":
        metrics = goal.get("metadata", {}).get("self_care", {})
        stagnation_avg = float(metrics.get("stagnation_avg", 0.0)) if metrics else 0.0
        circulation_ok = float(metrics.get("circulation_ok_rate", 1.0)) if metrics else 1.0
        if stagnation_avg >= 0.4:
            urgency += min(3.0, stagnation_avg * 4)
        if circulation_ok < 0.75:
            urgency += min(2.0, (0.75 - circulation_ok) * 4)
    
    # ⭐ NEW: Trinity 피드백 기반 긴급도 부스트
    if TRINITY_AVAILABLE:
        trinity_boost = get_trinity_urgency_boost(title, max_age_hours=48)
        if trinity_boost > 0:
            urgency += trinity_boost
            logger.info(f"  Trinity boost applied to '{title}': +{trinity_boost}")
    
    return min(urgency, 10.0)


def estimate_impact(goal: Dict[str, Any]) -> float:
    """
    예상 영향도를 계산한다 (0-10.0점).
    
    Trinity 통합:
    - Session Resonance Score가 높으면 임팩트 가중치 증가
    - 0.8 이상: 1.3x, 0.6~0.8: 1.1x, 0.6 미만: 1.0x
    
    Args:
        goal: 목표 딕셔너리
        
    Returns:
        영향도 점수 (0.0-10.0)
    """
    impact = 0.0
    desc_lower = goal["description"].lower()
    title_lower = goal["title"].lower()
    
    # 고영향 키워드
    HIGH_IMPACT = ["core", "architecture", "refactor", "system-wide", "stabilize"]
    MEDIUM_IMPACT = ["module", "component", "feature", "improve"]
    
    combined = desc_lower + " " + title_lower
    
    if any(kw in combined for kw in HIGH_IMPACT):
        impact = 8.0
    elif any(kw in combined for kw in MEDIUM_IMPACT):
        impact = 5.0
    else:
        impact = 3.0
    
    # ⭐ NEW: Session Resonance 기반 임팩트 가중치
    if TRINITY_AVAILABLE:
        session_resonance = get_session_resonance(max_age_hours=24)
        if session_resonance is not None:
            if session_resonance >= 0.8:
                multiplier = 1.3
            elif session_resonance >= 0.6:
                multiplier = 1.1
            else:
                multiplier = 1.0
            
            if multiplier > 1.0:
                impact *= multiplier
                logger.info(
                    f"  Session resonance boost applied: {session_resonance:.2f} → {multiplier}x impact"
                )
    
    return min(impact, 10.0)


def estimate_effort(priority: int) -> str:
    """
    예상 소요 시간을 추정한다.
    
    Args:
        priority: 최종 우선순위
        
    Returns:
        소요 시간 문자열 (예: "1 day", "3 days")
    """
    if priority >= 10:
        return "3 days"
    elif priority >= 7:
        return "2 days"
    else:
        return "1 day"


def prioritize_goals(
    goals: List[Dict[str, Any]],
    feedback_insights: Optional[Dict[str, Any]] = None,
    hippocampus_boost: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    목표에 우선순위를 할당하고 정렬한다.
    피드백 인사이트를 반영하여 타입별 성공률에 따라 우선순위 조정
    
    Args:
        goals: 목표 리스트
        feedback_insights: 피드백 인사이트 (타입별 성공률 등)
        hippocampus_boost: 장기 기억 기반 타입별 우선순위 부스트
        
    Returns:
        우선순위가 할당되고 정렬된 목표 리스트
    """
    insights = feedback_insights or {}
    type_stats = insights.get("type_performance", {}).get("type_stats", {})
    hippocampus_boost = hippocampus_boost or {}
    
    # 🧠 보상 추적기 초기화
    workspace_root = get_workspace_root()
    reward_tracker = None
    try:
        reward_tracker = RewardTracker(workspace_root)
    except Exception as e:
        logger.warning(f"Reward tracker unavailable: {e}")
    
    for i, goal in enumerate(goals, start=1):
        # 기본 정보 추가
        goal["id"] = i
        
        # 긴급도 및 영향도 계산
        urgency = calculate_urgency(goal)
        impact = estimate_impact(goal)
        
        # 피드백 인사이트 기반 부스트
        feedback_boost = 0.0
        goal_type = goal.get("type", "unknown")
        
        if goal_type in type_stats:
            success_rate = type_stats[goal_type].get("success_rate", 50.0)
            # 성공률이 높을수록 +0.5~+2.0 부스트
            if success_rate >= 80:
                feedback_boost = 2.0
                logger.info(f"   🎯 High success type '{goal_type}' ({success_rate}%): +{feedback_boost}")
            elif success_rate >= 60:
                feedback_boost = 1.0
            elif success_rate < 40:
                feedback_boost = -1.0  # 실패가 많은 타입은 감점
                logger.info(f"   ⚠️ Low success type '{goal_type}' ({success_rate}%): {feedback_boost}")
        
        # 🧠 보상 기반 습관 강화 부스트 (기저핵적 기능)
        habit_boost = 0.0
        if reward_tracker:
            habit_boost = reward_tracker.calculate_goal_boost(goal["title"])
            if habit_boost > 0:
                logger.info(f"   💰 Habit boost for '{goal['title']}': +{habit_boost:.2f}")
        
        # 🧠 Hippocampus 장기 기억 부스트
        memory_boost = 0.0
        if goal["type"] in hippocampus_boost:
            memory_boost = hippocampus_boost[goal["type"]] * 2.0  # 성공 패턴에 가중치
            logger.info(f"   🧠 Memory boost for type '{goal['type']}': +{memory_boost:.2f}")
        
        # 최종 우선순위
        final_priority = goal["base_priority"] + urgency + impact + feedback_boost + habit_boost + memory_boost
        
        goal["urgency_boost"] = urgency
        goal["impact_boost"] = impact
        goal["feedback_boost"] = feedback_boost
        goal["habit_boost"] = habit_boost  # 🧠 습관 강화 필드 추가
        goal["memory_boost"] = memory_boost  # 🧠 장기 기억 필드 추가
        goal["final_priority"] = final_priority
        goal["estimated_effort"] = estimate_effort(final_priority)
        goal["dependencies"] = []  # 현재는 빈 리스트, 나중에 확장 가능
        
        logger.info(
            f"Goal #{i}: {goal['title']} "
            f"(base={goal['base_priority']}, "
            f"urgency=+{urgency}, impact=+{impact}, feedback=+{feedback_boost}, "
            f"habit=+{habit_boost:.2f}, memory=+{memory_boost:.2f}, "
            f"final={final_priority})"
        )
    
    # 우선순위 내림차순 정렬
    goals_sorted = sorted(goals, key=lambda g: g["final_priority"], reverse=True)
    
    # ID 재할당
    for i, goal in enumerate(goals_sorted, start=1):
        goal["id"] = i
    
    return goals_sorted


# =============================================================================
# 6. 출력 생성 (Output Generation)
# =============================================================================

def generate_json_output(
    goals: List[Dict[str, Any]],
    resonance_states: List[str],
    trinity_feedback: Dict[str, Any],
    self_care_states: List[str],
    self_care_summary: Dict[str, Any],
    window_hours: int,
    input_sources: Dict[str, str]
) -> Dict[str, Any]:
    """
    JSON 출력을 생성한다.
    
    Returns:
        JSON 딕셔너리
    """
    # 우선순위 카운트
    high_priority = sum(1 for g in goals if g["final_priority"] >= 10)
    medium_priority = sum(1 for g in goals if 7 <= g["final_priority"] < 10)
    low_priority = sum(1 for g in goals if g["final_priority"] < 7)
    
    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "window_hours": window_hours,
        "input_sources": input_sources,
        "resonance_states": resonance_states,
        "trinity_summary": {
            "lua_issues": trinity_feedback.get("lua_issues", []),
            "elo_status": trinity_feedback.get("elo_status", "unknown"),
            "core_recommendations": trinity_feedback.get("core_recommendations", [])
        },
        "self_care": {
            "states": self_care_states,
            "summary": self_care_summary or {}
        },
        "goals": goals,
        "summary": {
            "total_goals": len(goals),
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority
        }
    }
    
    return output


def generate_markdown_output(
    goals: List[Dict[str, Any]],
    resonance_states: List[str],
    trinity_feedback: Dict[str, Any],
    self_care_states: List[str],
    self_care_summary: Dict[str, Any],
    window_hours: int,
    summary: Dict[str, int]
) -> str:
    """
    Markdown 출력을 생성한다.
    
    Returns:
        Markdown 문자열
    """
    lines: List[str] = []
    
    # 헤더
    lines.append("# Autonomous Goals Report")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Window: Last {window_hours} hours")
    lines.append("")
    
    # 요약
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total Goals**: {summary['total_goals']}")
    lines.append(f"- **High Priority (≥10)**: {summary['high_priority']}")
    lines.append(f"- **Medium Priority (7-9)**: {summary['medium_priority']}")
    lines.append(f"- **Low Priority (<7)**: {summary['low_priority']}")
    lines.append("")
    
    # 시스템 신호
    lines.append("## System Signals")
    lines.append("")
    lines.append(f"- Resonance States: {', '.join(resonance_states) if resonance_states else 'None'}")
    lines.append(f"- Trinity Lua Issues: {len(trinity_feedback.get('lua_issues', []))}")
    lines.append(f"- Trinity Elo Status: {trinity_feedback.get('elo_status', 'unknown')}")
    lines.append(f"- Trinity Core Recommendations: {len(trinity_feedback.get('core_recommendations', []))}")
    lines.append(f"- Self-Care States: {', '.join(self_care_states) if self_care_states else 'None'}")
    lines.append("")
    
    if self_care_summary:
        lines.append("## Self-Care Snapshot")
        lines.append("")
        lines.append(f"- Stagnation Avg: {self_care_summary.get('stagnation_avg', 0.0):.3f}")
        lines.append(f"- Stagnation P95: {self_care_summary.get('stagnation_p95', 0.0):.3f}")
        lines.append(f"- Stagnation Std: {self_care_summary.get('stagnation_std', 0.0):.3f}")
        lines.append(f"- Stagnation >0.5 Count: {self_care_summary.get('stagnation_over_05', 0)}")
        lines.append(f"- Circulation OK Rate: {self_care_summary.get('circulation_ok_rate', 0.0)*100:.1f}%")
        lines.append(f"- Queue Ratio Avg: {self_care_summary.get('queue_ratio_avg', 0.0):.2f}")
        lines.append(f"- Memory Growth Avg: {self_care_summary.get('memory_growth_avg', 0.0):.3f}")
        lines.append("")
    
    # Resonance 상태 상세
    lines.append("## Resonance State Analysis")
    lines.append("")
    if resonance_states:
        for state in resonance_states:
            state_emoji = "⚠️" if "low" in state or "high" in state else "✅"
            lines.append(f"- {state_emoji} {state.replace('_', ' ').title()}")
    else:
        lines.append("- None")
    lines.append("")
    
    # Trinity 피드백
    lines.append("## Trinity Feedback")
    lines.append("")
    lua_issues = trinity_feedback.get("lua_issues", [])
    lines.append(f"- **Lua Issues**: {', '.join(lua_issues) if lua_issues else 'None'}")
    lines.append(f"- **Elo Status**: {trinity_feedback.get('elo_status', 'Unknown')}")
    lines.append(f"- **Core Recommendations**: {len(trinity_feedback.get('core_recommendations', []))}")
    lines.append("")
    
    # 목표 리스트
    lines.append("## Goals (Prioritized)")
    lines.append("")
    
    for goal in goals:
        lines.append(f"### {goal['id']}. {goal['title']} (Priority: {goal['final_priority']})")
        lines.append("")
        lines.append(f"**Description**: {goal['description']}")
        lines.append(f"**Source**: {goal['source'].title()}")
        lines.append(f"**Effort**: {goal['estimated_effort']}")
        
        deps = goal.get("dependencies", [])
        deps_str = ", ".join(f"#{d}" for d in deps if d) if deps else "None"
        lines.append(f"**Dependencies**: {deps_str}")
        lines.append("")
        
        # 액션 아이템 (예시)
        lines.append("**Actions**:")
        if "Refactor" in goal["title"]:
            lines.append("- Review module architecture")
            lines.append("- Identify refactoring candidates")
            lines.append("- Plan incremental migration")
        elif "Improve" in goal["title"] or "Restore" in goal["title"]:
            lines.append("- Analyze current metrics")
            lines.append("- Implement monitoring enhancements")
            lines.append("- Validate improvements")
        else:
            lines.append("- Assess current state")
            lines.append("- Plan implementation")
            lines.append("- Execute and monitor")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# 7. 메인 실행 로직 (Main Execution)
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Goal Generator - Generate prioritized goals from Resonance + Trinity"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Analysis window in hours (default: 24)"
    )
    parser.add_argument(
        "--resonance-path",
        type=str,
        default="outputs/resonance_simulation_latest.json",
        help="Path to resonance metrics JSON"
    )
    parser.add_argument(
        "--trinity-path",
        type=str,
        default="outputs/core_enhanced_synthesis_latest.md",
        help="Path to trinity report Markdown"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="outputs/autonomous_goals_latest.json",
        help="Output JSON path"
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="outputs/autonomous_goals_latest.md",
        help="Output Markdown path"
    )
    parser.add_argument(
        "--goal-tracker",
        type=str,
        default="fdo_agi_repo/memory/goal_tracker.json",
        help="Goal tracker JSON (for completed goals)"
    )
    parser.add_argument(
        "--self-care-summary",
        type=str,
        default="outputs/self_care_metrics_summary.json",
        help="Self-care metrics summary JSON path"
    )
    parser.add_argument(
        "--feedback-insights",
        type=str,
        default="fdo_agi_repo/memory/goal_feedback_insights.json",
        help="Goal feedback insights JSON path"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("Autonomous Goal Generator - Phase 1")
    logger.info("=" * 70)
    logger.info(f"Analysis window: {args.hours} hours")
    logger.info(f"Resonance input: {args.resonance_path}")
    logger.info(f"Trinity input: {args.trinity_path}")
    logger.info(f"Goal tracker: {args.goal_tracker}")
    logger.info(f"Self-care summary: {args.self_care_summary}")
    logger.info(f"Feedback insights: {args.feedback_insights}")
    logger.info("")
    
    # 1. 입력 로딩
    logger.info("[1/7] Loading inputs...")
    resonance_metrics = load_resonance_metrics(args.resonance_path)
    trinity_report = load_trinity_report(args.trinity_path)
    completed_goals = load_completed_goals(args.goal_tracker)
    self_care_summary = load_self_care_summary(args.self_care_summary)
    feedback_insights = load_feedback_insights(args.feedback_insights)
    logger.info("")
    
    # 2. Resonance 상태 분석
    logger.info("[2/7] Analyzing resonance state...")
    resonance_states = analyze_resonance_state(resonance_metrics)
    logger.info("")
    
    # 3. Trinity 피드백 추출
    logger.info("[3/7] Extracting trinity feedback...")
    trinity_feedback = extract_trinity_feedback(trinity_report)
    logger.info("")
    
    # Self-care 상태 분석
    logger.info("[4/7] Assessing self-care metrics...")
    self_care_states = analyze_self_care_states(self_care_summary)
    logger.info("")
    
    # 4. 목표 생성 및 우선순위 (완료된 목표 제외, 피드백 인사이트 반영)
    logger.info("[5/7] Generating and prioritizing goals (with feedback insights + hippocampus)...")
    combined_states = resonance_states + self_care_states
    goals, hippocampus_boost = generate_goals(combined_states, trinity_feedback, completed_goals, self_care_summary, feedback_insights)
    goals = prioritize_goals(goals, feedback_insights, hippocampus_boost)
    logger.info("")
    
    # 5. 출력 생성
    logger.info("[6/7] Generating outputs...")
    
    input_sources = {
        "resonance_metrics": args.resonance_path,
        "trinity_report": args.trinity_path,
        "self_care_summary": args.self_care_summary
    }
    
    json_output = generate_json_output(
        goals,
        resonance_states,
        trinity_feedback,
        self_care_states,
        self_care_summary,
        args.hours,
        input_sources
    )
    
    md_output = generate_markdown_output(
        goals,
        resonance_states,
        trinity_feedback,
        self_care_states,
        self_care_summary,
        args.hours,
        json_output["summary"]
    )
    
    # JSON 저장
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, 'w', encoding='utf-8') as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)
    logger.info(f"✅ JSON saved: {args.output_json}")
    
    # Markdown 저장
    os.makedirs(os.path.dirname(args.output_md), exist_ok=True)
    with open(args.output_md, 'w', encoding='utf-8') as f:
        f.write(md_output)
    logger.info(f"✅ Markdown saved: {args.output_md}")
    
    logger.info("")
    logger.info("Summary...")
    logger.info(f"Completed goals excluded: {len(completed_goals)}")
    logger.info(f"New goals generated: {len(goals)}")
    logger.info("")
    logger.info("=" * 70)
    logger.info("✅ Autonomous Goal Generator completed successfully!")
    logger.info("=" * 70)
    logger.info(f"Generated {len(goals)} goals:")
    for goal in goals[:5]:  # 상위 5개만 출력
        logger.info(f"  • [{goal['final_priority']}] {goal['title']}")
    if len(goals) > 5:
        logger.info(f"  ... and {len(goals) - 5} more")
    logger.info("")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
