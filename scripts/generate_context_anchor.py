"""
Generate a single context anchor markdown for all agents/frontends.

This file is intended to be the first thing any new session reads:
- Summarises current context/mode
- Surfaces latest hippocampus handover (if present)
- Points to key maps/docs (AGI_CONTEXT_MAP, PROJECT_MAP_LUBIT, AGENT_HANDOFF)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Paths:
    workspace_root: Path
    agi_root: Path
    outputs: Path
    docs: Path


def _discover_paths() -> Paths:
    """Infer workspace / agi / outputs paths from this script location."""
    script_path = Path(__file__).resolve()
    agi_root = script_path.parent.parent
    workspace_root = agi_root.parent
    outputs = agi_root / "outputs"
    docs = agi_root / "docs"
    outputs.mkdir(parents=True, exist_ok=True)
    return Paths(
        workspace_root=workspace_root,
        agi_root=agi_root,
        outputs=outputs,
        docs=docs,
    )


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        # Use utf-8-sig to tolerate BOM from various writers
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _summarize_active_context(active_path: Path) -> List[str]:
    ctx = _load_json(active_path) or {}
    if not ctx:
        return ["- 현재 활성 맥락 정보를 찾을 수 없습니다."]

    current = ctx.get("current", "Unknown")
    previous = ctx.get("previous", "Unknown")
    active_since = ctx.get("active_since")
    tuning = ctx.get("tuning_parameters", {})

    lines: List[str] = []
    lines.append(f"- 현재 맥락: **{current}** (이전: {previous})")
    if active_since:
        lines.append(f"- 활성화 시각: `{active_since}`")
    if tuning:
        phase = tuning.get("phase", "Unknown")
        reaction = tuning.get("reaction_level", "Unknown")
        speed = tuning.get("rotation_speed", "Unknown")
        lines.append(f"- Tuning: phase={phase}, reaction_level={reaction}, rotation_speed={speed}")

    return lines


def _summarize_handover(handover_path: Path) -> List[str]:
    handover = _load_json(handover_path) or {}
    if not handover:
        return ["- 해마 Handover 파일이 아직 생성되지 않았습니다."]

    lines: List[str] = []
    session_id = handover.get("session_id", "Unknown")
    timestamp = handover.get("timestamp", "Unknown")
    pending = handover.get("pending_tasks") or []
    suggested = handover.get("suggested_next_actions") or []

    lines.append(f"- 세션 ID: `{session_id}`")
    lines.append(f"- 생성 시각: `{timestamp}`")
    lines.append(f"- 미완료 작업 수: {len(pending)}")

    if suggested:
        lines.append("")
        lines.append("**제안된 다음 행동 (해마 기준):**")
        for idx, item in enumerate(suggested[:3], start=1):
            if isinstance(item, dict):
                title = item.get("title") or item.get("description") or str(item)
                lines.append(f"{idx}. {title}")
            else:
                lines.append(f"{idx}. {item}")
    return lines


def _summarize_agent_handoff(agent_handoff_path: Path) -> List[str]:
    info = _load_json(agent_handoff_path) or {}
    if not info:
        return []

    lines: List[str] = []
    next_actions = info.get("NextActions") or []
    if next_actions:
        lines.append("**AGENT_HANDOFF 기준 추천 다음 행동:**")
        for idx, item in enumerate(next_actions[:3], start=1):
            lines.append(f"{idx}. {item}")
    return lines


def generate_anchor() -> Path:
    """Generate context_anchor_latest.md under agi/outputs and return its path."""
    paths = _discover_paths()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    anchor_path = paths.outputs / "context_anchor_latest.md"

    active_ctx_path = paths.outputs / "active_context.json"
    handover_path = paths.outputs / "copilot_handover_latest.json"
    agent_handoff_path = paths.outputs / "agent_handoff.json"

    lines: List[str] = []
    lines.append("# AGI Context Anchor (루빛 · Trinity · Koa)")
    lines.append("")
    lines.append(f"**생성 시각**: {now}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. 시스템 한 줄 요약
    lines.append("## 1. 시스템 한 줄 요약")
    lines.append("")
    lines.append(
        "- 이 워크스페이스는 Trinity/AGI 다층 의식 실험의 메인 루트입니다."
    )
    lines.append(
        "- `agi/`는 실제 AGI 시스템 본체, `trinity_public/`는 공개용 축소판, "
        "`original_data/`는 과거 D 드라이브 작업의 백업/레퍼런스입니다."
    )
    lines.append("")

    # 2. 현재 활성 맥락 요약
    lines.append("## 2. 현재 활성 맥락 (AGI_CONTEXT_MAP 기준)")
    lines.append("")
    lines.extend(_summarize_active_context(active_ctx_path))
    lines.append("")

    # 3. 해마(Hippocampus) Handover 요약
    lines.append("## 3. 해마 Handover (세션 간 연속성)")
    lines.append("")
    lines.extend(_summarize_handover(handover_path))
    lines.append("")

    # 4. 에이전트 핸드오프 기반 다음 행동
    agent_handoff_summary = _summarize_agent_handoff(agent_handoff_path)
    if agent_handoff_summary:
        lines.append("## 4. 에이전트 핸드오프 기반 다음 행동")
        lines.append("")
        lines.extend(agent_handoff_summary)
        lines.append("")

    # 5. 중요한 지도/맥락 문서
    lines.append("## 5. 중요한 지도/맥락 문서")
    lines.append("")
    # Paths are shown workspace-relative for humans/agents.
    lines.append("- `agi/docs/AGI_CONTEXT_MAP.md`  (맥락 시스템 정의)")
    lines.append("- `PROJECT_MAP_LUBIT.md`         (C:\\workspace 전체 지형도)")
    lines.append("- `agi/docs/AGENT_HANDOFF.md`    (최근 변경 내역과 다음 우선순위)")
    lines.append("- `agi/docs/AGENT_HANDOFF_SUMMARY.md` (요약 핸드오프)")
    lines.append("")

    # 6. 참고 파일 위치
    lines.append("## 6. 참고 파일 위치")
    lines.append("")
    lines.append(f"- 활성 맥락 상태: `agi/outputs/active_context.json`")
    lines.append(f"- 해마 Handover: `agi/outputs/copilot_handover_latest.json`")
    lines.append(f"- 에이전트 핸드오프 스냅샷: `agi/outputs/agent_handoff.json`")
    lines.append("")

    anchor_path.write_text("\n".join(lines), encoding="utf-8")
    return anchor_path


def main() -> None:
    path = generate_anchor()
    print(f"Context anchor generated at: {path}")


if __name__ == "__main__":
    main()
