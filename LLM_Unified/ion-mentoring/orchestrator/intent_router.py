from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PlannedAction:
    kind: str  # e.g., 'deploy_canary', 'rollback_canary', 'start_monitor_loop', 'stop_monitor_loops', 'probe', 'run_tests', 'load_test', 'check_status'
    args: dict


@dataclass
class Plan:
    summary: str
    actions: List[PlannedAction]


_PERCENT_RE = re.compile(r"(\d+)%")


def _extract_percentage(text: str) -> Optional[int]:
    m = _PERCENT_RE.search(text)
    if not m:
        return None
    try:
        val = int(m.group(1))
        if val in (5, 10, 25, 50, 100):
            return val
    except ValueError:
        pass
    return None


def _normalize(text: str) -> str:
    return text.strip().lower()


def plan_from_prompt(prompt: str) -> Plan:
    """
    Very lightweight rule-based intent parser.
    Supports KO/EN keywords for MVP.
    """
    p = _normalize(prompt)
    actions: List[PlannedAction] = []

    # Deploy canary with %
    if ("canary" in p or "카나리" in p) and ("deploy" in p or "배포" in p or "%" in p):
        pct = _extract_percentage(p) or 5
        actions.append(PlannedAction("deploy_canary", {"percentage": pct}))

    # Rollback canary
    if "rollback" in p or "롤백" in p:
        actions.append(PlannedAction("rollback_canary", {"to": 0}))

    # Monitoring loops
    if ("start" in p or "시작" in p) and ("monitor" in p or "모니터링" in p or "watch" in p):
        actions.append(PlannedAction("start_monitor_loop", {"profile": "with_probe"}))
    if ("stop" in p or "중지" in p or "종료" in p) and ("monitor" in p or "모니터링" in p or "loop" in p):
        actions.append(PlannedAction("stop_monitor_loops", {}))

    # Probes
    if "probe" in p or "프로브" in p:
        profile = "normal"
        if any(k in p for k in ["gentle", "젠틀", "약하게"]):
            profile = "gentle"
        elif any(k in p for k in ["aggressive", "어그레시브", "강하게"]):
            profile = "aggressive"
        actions.append(PlannedAction("probe", {"profile": profile}))

    # Tests
    if "test" in p or "테스트" in p:
        if any(k in p for k in ["all", "전체"]):
            actions.append(PlannedAction("run_tests", {"scope": "all"}))
        elif "vertex" in p:
            actions.append(PlannedAction("run_tests", {"scope": "vertex_ai"}))
        elif "load" in p or "로드" in p:
            # default to light smoke
            actions.append(PlannedAction("load_test", {"profile": "light"}))

    # Status / logs quick
    if any(k in p for k in ["status", "상태"]):
        actions.append(PlannedAction("check_status", {}))

    if not actions:
        # Fallback: default to status check so user gets feedback
        actions.append(PlannedAction("check_status", {}))

    summary = _build_summary(actions)
    return Plan(summary=summary, actions=actions)


def _build_summary(actions: List[PlannedAction]) -> str:
    parts = []
    for a in actions:
        if a.kind == "deploy_canary":
            parts.append(f"Canary 배포 {a.args.get('percentage')}%")
        elif a.kind == "rollback_canary":
            parts.append("Canary 롤백 → 0%")
        elif a.kind == "start_monitor_loop":
            parts.append("모니터링 루프 시작")
        elif a.kind == "stop_monitor_loops":
            parts.append("모니터링 루프 중지")
        elif a.kind == "probe":
            parts.append(f"프로브 실행 ({a.args.get('profile')})")
        elif a.kind == "run_tests":
            parts.append(f"테스트 실행 ({a.args.get('scope')})")
        elif a.kind == "load_test":
            parts.append(f"로드 테스트 ({a.args.get('profile')})")
        elif a.kind == "check_status":
            parts.append("상태 확인")
    return " · ".join(parts) if parts else "No actions"
