#!/usr/bin/env python3
"""
Adaptive Rhythm Orchestrator

Core의 시선 → 비노체 프리즘 → 구조 → 리듬
상태에 따라 실행 주기를 동적으로 조정하는 적응형 리듬 시스템

입력:
- outputs/autonomous_goals_latest.json (현재 목표 및 상태)
- outputs/resonance_simulation_latest.json (공명 메트릭)
- fdo_agi_repo/memory/goal_tracker.json (실행 이력)

출력:
- outputs/adaptive_rhythm_schedule.json (다음 실행 일정)
- outputs/adaptive_rhythm_latest.md (리듬 분석 보고서)

작성일: 2025-11-05
"""

import argparse
import json
import logging
import os
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
# 리듬 상태 정의
# =============================================================================

class RhythmState:
    """시스템 상태에 따른 리듬 정의"""
    
    # 긴급 상태 (즉시 실행)
    CRITICAL = {
        "name": "Critical",
        "interval_hours": 0.25,  # 15분
        "max_executions_per_day": 96,
        "description": "긴급 상황, 즉시 대응 필요"
    }
    
    # 정보 기아 상태 (자주 실행)
    INFO_STARVATION = {
        "name": "Info Starvation",
        "interval_hours": 2,  # 2시간
        "max_executions_per_day": 12,
        "description": "정보 밀도 낮음, 데이터 수집 필요"
    }
    
    # 낮은 공명 상태 (보통 실행)
    LOW_RESONANCE = {
        "name": "Low Resonance",
        "interval_hours": 6,  # 6시간
        "max_executions_per_day": 4,
        "description": "공명도 낮음, 모니터링 강화"
    }
    
    # 높은 엔트로피 상태 (보통 실행)
    HIGH_ENTROPY = {
        "name": "High Entropy",
        "interval_hours": 4,  # 4시간
        "max_executions_per_day": 6,
        "description": "엔트로피 높음, 구조화 필요"
    }
    
    # 안정 상태 (덜 자주 실행)
    STABLE = {
        "name": "Stable",
        "interval_hours": 24,  # 24시간 (1일)
        "max_executions_per_day": 1,
        "description": "안정 상태, 정상 운영"
    }
    
    # 유휴 상태 (가장 드물게 실행)
    IDLE = {
        "name": "Idle",
        "interval_hours": 72,  # 72시간 (3일)
        "max_executions_per_day": 0.33,
        "description": "유휴 상태, 최소 모니터링"
    }


# =============================================================================
# 상태 분석
# =============================================================================

def analyze_system_state(goals_path: str, resonance_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    시스템 상태를 분석하여 적절한 리듬을 결정한다.
    
    Returns:
        (rhythm_state_name, state_details)
    """
    logger.info("=== Analyzing System State for Rhythm ===")
    
    # Goal 데이터 로드
    goals_data = {}
    if os.path.exists(goals_path):
        with open(goals_path, 'r', encoding='utf-8') as f:
            goals_data = json.load(f)
    else:
        logger.warning(f"Goals file not found: {goals_path}")
    
    # Resonance 데이터 로드
    resonance_data = {}
    if os.path.exists(resonance_path):
        with open(resonance_path, 'r', encoding='utf-8') as f:
            resonance_data = json.load(f)
    else:
        logger.warning(f"Resonance file not found: {resonance_path}")
    
    # 상태 추출
    resonance_states = goals_data.get('resonance_states', [])
    goals = goals_data.get('goals', [])
    max_priority = max([g.get('final_priority', 0) for g in goals], default=0)
    
    # Resonance 메트릭
    metrics = resonance_data.get('metrics', {})
    info_density = metrics.get('info_density', 0.5)
    resonance = metrics.get('resonance', 0.5)
    entropy = metrics.get('entropy', 0.5)
    horizon_crossings = metrics.get('horizon_crossings', 0)
    
    logger.info(f"Resonance states: {resonance_states}")
    logger.info(f"Max goal priority: {max_priority}")
    logger.info(f"Info density: {info_density:.3f}")
    logger.info(f"Resonance: {resonance:.3f}")
    logger.info(f"Entropy: {entropy:.3f}")
    logger.info(f"Horizon crossings: {horizon_crossings}")
    
    # 상태 결정 로직
    state_details = {
        "resonance_states": resonance_states,
        "max_priority": max_priority,
        "info_density": info_density,
        "resonance": resonance,
        "entropy": entropy,
        "horizon_crossings": horizon_crossings,
        "goals_count": len(goals)
    }
    
    # 1. 긴급 상태 체크
    if horizon_crossings > 2 or max_priority >= 15:
        logger.info("→ Detected: CRITICAL state")
        return "CRITICAL", state_details
    
    # 2. 정보 기아 체크
    if "info_starvation" in resonance_states or info_density < -0.3:
        logger.info("→ Detected: INFO_STARVATION state")
        return "INFO_STARVATION", state_details
    
    # 3. 높은 엔트로피 체크
    if "high_entropy" in resonance_states or entropy > 0.8:
        logger.info("→ Detected: HIGH_ENTROPY state")
        return "HIGH_ENTROPY", state_details
    
    # 4. 낮은 공명 체크
    if "low_resonance" in resonance_states or resonance < 0.3:
        logger.info("→ Detected: LOW_RESONANCE state")
        return "LOW_RESONANCE", state_details
    
    # 5. 안정 상태
    if len(goals) > 0 and max_priority < 10:
        logger.info("→ Detected: STABLE state")
        return "STABLE", state_details
    
    # 6. 유휴 상태
    if len(goals) == 0 and resonance > 0.7:
        logger.info("→ Detected: IDLE state")
        return "IDLE", state_details
    
    # 기본값: 안정
    logger.info("→ Detected: STABLE state (default)")
    return "STABLE", state_details


# =============================================================================
# 스케줄 생성
# =============================================================================

def generate_schedule(
    rhythm_state_name: str,
    state_details: Dict[str, Any],
    base_time: datetime
) -> List[datetime]:
    """
    리듬 상태에 따라 다음 실행 일정을 생성한다.
    """
    rhythm = getattr(RhythmState, rhythm_state_name)
    interval_hours = rhythm["interval_hours"]
    max_executions = rhythm["max_executions_per_day"]
    
    logger.info(f"Generating schedule for {rhythm['name']}")
    logger.info(f"  Interval: {interval_hours} hours")
    logger.info(f"  Max executions/day: {max_executions}")
    
    schedule = []
    next_time = base_time
    
    # 다음 24시간 동안의 스케줄 생성
    end_time = base_time + timedelta(days=1)
    count = 0
    
    while next_time < end_time and count < max_executions:
        schedule.append(next_time)
        next_time += timedelta(hours=interval_hours)
        count += 1
    
    logger.info(f"Generated {len(schedule)} execution times")
    
    return schedule


# =============================================================================
# 출력 생성
# =============================================================================

def generate_outputs(
    rhythm_state_name: str,
    state_details: Dict[str, Any],
    schedule: List[datetime],
    output_json: str,
    output_md: str
):
    """JSON과 Markdown 출력을 생성한다."""
    rhythm = getattr(RhythmState, rhythm_state_name)
    
    # JSON 출력
    output_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "rhythm_state": rhythm["name"],
        "description": rhythm["description"],
        "interval_hours": rhythm["interval_hours"],
        "max_executions_per_day": rhythm["max_executions_per_day"],
        "state_details": state_details,
        "schedule": [t.isoformat() for t in schedule],
        "next_execution": schedule[0].isoformat() if schedule else None
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ JSON saved: {output_json}")
    
    # Markdown 출력
    md_lines = [
        "# 🎵 Adaptive Rhythm Schedule",
        "",
        f"**생성 시각**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 현재 리듬 상태",
        "",
        f"**상태**: {rhythm['name']}  ",
        f"**설명**: {rhythm['description']}  ",
        f"**실행 간격**: {rhythm['interval_hours']} 시간  ",
        f"**하루 최대 실행**: {rhythm['max_executions_per_day']}회",
        "",
        "## 시스템 메트릭",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Resonance States | {', '.join(state_details['resonance_states'])} |",
        f"| Max Priority | {state_details['max_priority']} |",
        f"| Info Density | {state_details['info_density']:.3f} |",
        f"| Resonance | {state_details['resonance']:.3f} |",
        f"| Entropy | {state_details['entropy']:.3f} |",
        f"| Horizon Crossings | {state_details['horizon_crossings']} |",
        f"| Goals Count | {state_details['goals_count']} |",
        "",
        "## 실행 스케줄 (다음 24시간)",
        ""
    ]
    
    if schedule:
        md_lines.append("| # | 실행 시각 |")
        md_lines.append("|---|----------|")
        for i, t in enumerate(schedule, 1):
            md_lines.append(f"| {i} | {t.strftime('%Y-%m-%d %H:%M:%S')} |")
        md_lines.append("")
        md_lines.append(f"**다음 실행**: {schedule[0].strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        md_lines.append("실행 예정 없음 (유휴 상태)")
    
    md_lines.extend([
        "",
        "## 리듬 상태 설명",
        "",
        "### Critical (긴급)",
        "- 실행 간격: 15분",
        "- horizon_crossings > 2 또는 max_priority >= 15",
        "- 즉각적인 대응 필요",
        "",
        "### Info Starvation (정보 기아)",
        "- 실행 간격: 2시간",
        "- info_density < -0.3",
        "- 데이터 수집 강화 필요",
        "",
        "### High Entropy (높은 엔트로피)",
        "- 실행 간격: 4시간",
        "- entropy > 0.8",
        "- 구조화 작업 필요",
        "",
        "### Low Resonance (낮은 공명)",
        "- 실행 간격: 6시간",
        "- resonance < 0.3",
        "- 모니터링 강화 필요",
        "",
        "### Stable (안정)",
        "- 실행 간격: 24시간 (1일)",
        "- 정상 운영 상태",
        "",
        "### Idle (유휴)",
        "- 실행 간격: 72시간 (3일)",
        "- 최소 모니터링만 수행",
        "",
        "---",
        "",
        f"**생성자**: Adaptive Rhythm Orchestrator  ",
        f"**버전**: 1.0  ",
        f"**날짜**: {datetime.now().strftime('%Y-%m-%d')}"
    ])
    
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    logger.info(f"✅ Markdown saved: {output_md}")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Adaptive Rhythm Orchestrator - 상태 기반 동적 스케줄링"
    )
    parser.add_argument(
        '--goals-path',
        default='outputs/autonomous_goals_latest.json',
        help='Path to goals JSON'
    )
    parser.add_argument(
        '--resonance-path',
        default='outputs/resonance_simulation_latest.json',
        help='Path to resonance metrics JSON'
    )
    parser.add_argument(
        '--output-json',
        default='outputs/adaptive_rhythm_schedule.json',
        help='Output JSON path'
    )
    parser.add_argument(
        '--output-md',
        default='outputs/adaptive_rhythm_latest.md',
        help='Output Markdown path'
    )
    parser.add_argument(
        '--base-time',
        help='Base time for schedule (ISO format, default: now)'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("Adaptive Rhythm Orchestrator")
    logger.info("=" * 70)
    
    # Base time 설정
    if args.base_time:
        base_time = datetime.fromisoformat(args.base_time)
    else:
        base_time = datetime.now()
    
    logger.info(f"Base time: {base_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    # 1. 상태 분석
    logger.info("[1/3] Analyzing system state...")
    rhythm_state_name, state_details = analyze_system_state(
        args.goals_path,
        args.resonance_path
    )
    logger.info("")
    
    # 2. 스케줄 생성
    logger.info("[2/3] Generating schedule...")
    schedule = generate_schedule(rhythm_state_name, state_details, base_time)
    logger.info("")
    
    # 3. 출력 생성
    logger.info("[3/3] Generating outputs...")
    generate_outputs(
        rhythm_state_name,
        state_details,
        schedule,
        args.output_json,
        args.output_md
    )
    logger.info("")
    
    logger.info("=" * 70)
    logger.info("✅ Adaptive Rhythm Orchestrator completed!")
    logger.info("=" * 70)
    logger.info(f"Rhythm state: {rhythm_state_name}")
    if schedule:
        logger.info(f"Next execution: {schedule[0].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total scheduled: {len(schedule)} executions")
    else:
        logger.info("No executions scheduled (IDLE state)")
    logger.info("")


if __name__ == "__main__":
    main()
