#!/usr/bin/env python3
"""
Autonomous Goal Generator

자율 목표 생성 시스템 - Phase 1 구현
Resonance Simulator + Autopoietic Trinity → 우선순위 목표 생성

입력:
- outputs/resonance_simulation_latest.json (Resonance 메트릭)
- outputs/lumen_enhanced_synthesis_latest.md (Trinity 피드백)

출력:
- outputs/autonomous_goals_latest.json (목표 리스트 JSON)
- outputs/autonomous_goals_latest.md (목표 리스트 Markdown)

작성일: 2025-11-05
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
from typing import Any, Dict, List, Optional, Tuple

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# 1. 입력 로딩 (Input Loading)
# =============================================================================

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
        path: lumen_enhanced_synthesis_latest.md 경로
        
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
            "lumen_recommendations": list[dict]
        }
    """
    feedback = {
        "lua_issues": [],
        "elo_status": "unknown",
        "lumen_recommendations": []
    }
    
    if not report_content:
        logger.warning("Empty trinity report, returning empty feedback")
        return feedback
    
    # Lua 관찰 추출 (정/正)
    lua_section = re.search(
        r'## 📊 정\(正\) - 루아의 관찰 요약(.*?)(?=##|$)',
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
    
    # Lumen 통합 권장사항 추출 (합/合)
    lumen_section = re.search(
        r'## 💡 합\(合\) - 통합 통찰(.*?)(?=##|$)',
        report_content,
        re.DOTALL
    )
    if lumen_section:
        lumen_text = lumen_section.group(1)
        
        # HIGH/MEDIUM/INFO 권장사항 추출
        recommendations = re.findall(
            r'### (🔴|🟡|✅) (\w+) - (\w+)\s+\*\*(.+?)\*\*',
            lumen_text
        )
        
        for emoji, priority, category, description in recommendations:
            priority_map = {"🔴": "HIGH", "🟡": "MEDIUM", "✅": "INFO"}
            feedback["lumen_recommendations"].append({
                "priority": priority_map.get(emoji, "UNKNOWN"),
                "category": category,
                "description": description
            })
    
    logger.info(f"Extracted trinity feedback:")
    logger.info(f"  lua_issues: {len(feedback['lua_issues'])} issues")
    logger.info(f"  elo_status: {feedback['elo_status']}")
    logger.info(f"  lumen_recommendations: {len(feedback['lumen_recommendations'])} items")
    
    return feedback


# =============================================================================
# 4. 목표 생성 (Goal Generation)
# =============================================================================

def generate_goals(
    resonance_states: List[str],
    trinity_feedback: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Resonance 상태와 Trinity 피드백을 결합하여 목표를 생성한다.
    
    Args:
        resonance_states: Resonance 상태 표시자 리스트
        trinity_feedback: Trinity 피드백 딕셔너리
        
    Returns:
        목표 딕셔너리 리스트 (title, description, base_priority, source)
    """
    goals = []
    
    # Resonance 기반 목표 생성 규칙
    GOAL_RULES = {
        "info_overload": {
            "title": "Simplify System Architecture",
            "description": "Reduce information density by refactoring complex modules",
            "base_priority": 8
        },
        "info_starvation": {
            "title": "Increase Data Collection",
            "description": "Improve information density by collecting more metrics",
            "base_priority": 7
        },
        "low_resonance": {
            "title": "Refactor Core Components",
            "description": "Improve resonance by restructuring core logic",
            "base_priority": 9
        },
        "high_resonance": {
            "title": "Maintain Current Approach",
            "description": "System resonance is high, continue current strategy",
            "base_priority": 5
        },
        "high_entropy": {
            "title": "Improve Clarity and Structure",
            "description": "Reduce entropy through better organization",
            "base_priority": 7
        },
        "low_entropy": {
            "title": "Explore New Approaches",
            "description": "System may be too rigid, try experimental features",
            "base_priority": 6
        },
        "unstable_dynamics": {
            "title": "Stabilize System Dynamics",
            "description": "Too many horizon crossings, need stabilization",
            "base_priority": 8
        },
        "stable_dynamics": {
            "title": "Incremental Improvements",
            "description": "System is stable, focus on gradual enhancements",
            "base_priority": 5
        },
        "normal_operation": {
            "title": "Monitor and Maintain",
            "description": "No issues detected, continue monitoring",
            "base_priority": 4
        }
    }
    
    # Resonance 상태 기반 목표 생성
    for state in resonance_states:
        if state in GOAL_RULES:
            goal = GOAL_RULES[state].copy()
            goal["source"] = "resonance"
            goals.append(goal)
            logger.info(f"Generated goal from resonance: {goal['title']}")
    
    # Trinity 피드백 기반 목표 생성
    for rec in trinity_feedback.get("lumen_recommendations", []):
        if rec["priority"] == "HIGH":
            goals.append({
                "title": f"Address: {rec['category']}",
                "description": rec["description"],
                "base_priority": 8,
                "source": "trinity"
            })
            logger.info(f"Generated goal from trinity (HIGH): {rec['category']}")
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
    return goals


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

def calculate_urgency(goal: Dict[str, Any]) -> int:
    """
    긴급도를 계산한다 (0-3점).
    
    Args:
        goal: 목표 딕셔너리
        
    Returns:
        긴급도 점수 (0-3)
    """
    urgency = 0
    desc_lower = goal["description"].lower()
    
    # 키워드 기반 긴급도
    if "critical" in desc_lower or "urgent" in desc_lower:
        urgency += 3
    elif "warning" in desc_lower or "issue" in desc_lower:
        urgency += 2
    elif "notice" in desc_lower or "improve" in desc_lower:
        urgency += 1
    
    # Trinity HIGH 권장사항은 긴급도 +1
    if goal.get("source") == "trinity" and "Address" in goal.get("title", ""):
        urgency += 1
    
    return min(urgency, 3)


def estimate_impact(goal: Dict[str, Any]) -> int:
    """
    예상 영향도를 계산한다 (0-3점).
    
    Args:
        goal: 목표 딕셔너리
        
    Returns:
        영향도 점수 (0-3)
    """
    impact = 0
    desc_lower = goal["description"].lower()
    title_lower = goal["title"].lower()
    
    # 고영향 키워드
    HIGH_IMPACT = ["core", "architecture", "refactor", "system-wide", "stabilize"]
    MEDIUM_IMPACT = ["module", "component", "feature", "improve"]
    
    combined = desc_lower + " " + title_lower
    
    if any(kw in combined for kw in HIGH_IMPACT):
        impact = 3
    elif any(kw in combined for kw in MEDIUM_IMPACT):
        impact = 2
    else:
        impact = 1
    
    return impact


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


def prioritize_goals(goals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    목표에 우선순위를 할당하고 정렬한다.
    
    Args:
        goals: 목표 리스트
        
    Returns:
        우선순위가 할당되고 정렬된 목표 리스트
    """
    for i, goal in enumerate(goals, start=1):
        # 기본 정보 추가
        goal["id"] = i
        
        # 긴급도 및 영향도 계산
        urgency = calculate_urgency(goal)
        impact = estimate_impact(goal)
        
        # 최종 우선순위
        final_priority = goal["base_priority"] + urgency + impact
        
        goal["urgency_boost"] = urgency
        goal["impact_boost"] = impact
        goal["final_priority"] = final_priority
        goal["estimated_effort"] = estimate_effort(final_priority)
        goal["dependencies"] = []  # 현재는 빈 리스트, 나중에 확장 가능
        
        logger.info(
            f"Goal #{i}: {goal['title']} "
            f"(base={goal['base_priority']}, "
            f"urgency=+{urgency}, impact=+{impact}, "
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
            "lumen_recommendations": trinity_feedback.get("lumen_recommendations", [])
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
    window_hours: int,
    summary: Dict[str, int]
) -> str:
    """
    Markdown 출력을 생성한다.
    
    Returns:
        Markdown 문자열
    """
    lines = []
    
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
    
    # Resonance 상태
    lines.append("## Resonance State Analysis")
    lines.append("")
    for state in resonance_states:
        state_emoji = "⚠️" if "low" in state or "high" in state else "✅"
        lines.append(f"- {state_emoji} {state.replace('_', ' ').title()}")
    lines.append("")
    
    # Trinity 피드백
    lines.append("## Trinity Feedback")
    lines.append("")
    lines.append(f"- **Lua**: {', '.join(trinity_feedback.get('lua_issues', ['None']))}")
    lines.append(f"- **Elo**: {trinity_feedback.get('elo_status', 'Unknown')}")
    lines.append(f"- **Lumen**: {len(trinity_feedback.get('lumen_recommendations', []))} recommendations")
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
        deps_str = ", ".join(f"#{d}" for d in deps) if deps else "None"
        lines.append(f"**Dependencies**: {deps_str}")
        lines.append("")
        
        # 액션 아이템 (예시)
        lines.append("**Actions**:")
        if "Refactor" in goal["title"]:
            lines.append("- Review module architecture")
            lines.append("- Identify refactoring candidates")
            lines.append("- Plan incremental migration")
        elif "Improve" in goal["title"]:
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
        default="outputs/lumen_enhanced_synthesis_latest.md",
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
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("Autonomous Goal Generator - Phase 1")
    logger.info("=" * 70)
    logger.info(f"Analysis window: {args.hours} hours")
    logger.info(f"Resonance input: {args.resonance_path}")
    logger.info(f"Trinity input: {args.trinity_path}")
    logger.info("")
    
    # 1. 입력 로딩
    logger.info("[1/5] Loading inputs...")
    resonance_metrics = load_resonance_metrics(args.resonance_path)
    trinity_report = load_trinity_report(args.trinity_path)
    logger.info("")
    
    # 2. Resonance 상태 분석
    logger.info("[2/5] Analyzing resonance state...")
    resonance_states = analyze_resonance_state(resonance_metrics)
    logger.info("")
    
    # 3. Trinity 피드백 추출
    logger.info("[3/5] Extracting trinity feedback...")
    trinity_feedback = extract_trinity_feedback(trinity_report)
    logger.info("")
    
    # 4. 목표 생성 및 우선순위
    logger.info("[4/5] Generating and prioritizing goals...")
    goals = generate_goals(resonance_states, trinity_feedback)
    goals = prioritize_goals(goals)
    logger.info("")
    
    # 5. 출력 생성
    logger.info("[5/5] Generating outputs...")
    
    input_sources = {
        "resonance_metrics": args.resonance_path,
        "trinity_report": args.trinity_path
    }
    
    json_output = generate_json_output(
        goals, resonance_states, trinity_feedback, args.hours, input_sources
    )
    
    md_output = generate_markdown_output(
        goals, resonance_states, trinity_feedback, args.hours, json_output["summary"]
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
