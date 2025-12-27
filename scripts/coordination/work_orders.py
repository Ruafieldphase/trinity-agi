#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Work Order Packets

목표:
- 외부 에이전트(AntiGravity/Claude 등)에게 넘길 작업 지시를
  "파일 1개 = 작업 1개"로 고정한다.
- 작업 지시는 인간/에이전트가 쉽게 읽을 수 있게 Markdown + JSON 동시 생성.

출력:
- outputs/coordination/work_orders/<id>_<agent>_<slug>.md
- outputs/coordination/work_orders/<id>_<agent>_<slug>.json
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(text: str, max_len: int = 48) -> str:
    t = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-").lower()
    return (t[:max_len] or "task")


@dataclass
class WorkOrder:
    agent: str
    title: str
    goal: str
    deliverables: list[str]
    constraints: list[str] = field(default_factory=list)
    context_files: list[str] = field(default_factory=list)
    acceptance: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    created_at_utc: str = field(default_factory=utc_now_iso)


def write_work_order(workspace_root: Path, wo: WorkOrder) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    out_dir = workspace_root / "outputs" / "coordination" / "work_orders"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = int(time.time())
    filename = f"{ts}_{wo.agent}_{slugify(wo.title)}"
    md_path = out_dir / f"{filename}.md"
    json_path = out_dir / f"{filename}.json"

    md_lines: list[str] = []
    md_lines.append(f"# Work Order: {wo.title}")
    md_lines.append("")
    md_lines.append(f"- 대상 에이전트: `{wo.agent}`")
    md_lines.append(f"- 생성(UTC): `{wo.created_at_utc}`")
    md_lines.append("")
    md_lines.append("## 목표")
    md_lines.append(wo.goal)
    md_lines.append("")
    md_lines.append("## 산출물(Deliverables)")
    for d in wo.deliverables:
        md_lines.append(f"- {d}")
    md_lines.append("")
    if wo.acceptance:
        md_lines.append("## 완료 기준(Acceptance)")
        for a in wo.acceptance:
            md_lines.append(f"- {a}")
        md_lines.append("")
    if wo.constraints:
        md_lines.append("## 제약(Constraints)")
        for c in wo.constraints:
            md_lines.append(f"- {c}")
        md_lines.append("")
    if wo.context_files:
        md_lines.append("## 참고 파일(Context)")
        for c in wo.context_files:
            md_lines.append(f"- `{c}`")
        md_lines.append("")
    if wo.notes:
        md_lines.append("## 메모(Notes)")
        for n in wo.notes:
            md_lines.append(f"- {n}")
        md_lines.append("")

    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(asdict(wo), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"md": str(md_path), "json": str(json_path)}


def default_work_orders(workspace_root: Path) -> list[dict[str, Any]]:
    w = Path(workspace_root).resolve()
    context = [
        "outputs/bridge/trigger_report_latest.json",
        "outputs/bridge/trigger_dashboard.html",
        "outputs/antigravity_intake_latest.json",
        "outputs/media_intake_latest.json",
        "scripts/trigger_listener.py",
        "docs/AGENT_HANDOFF.md",
    ]

    orders = [
        WorkOrder(
            agent="antigravity_sian",
            title="Status Dashboard v2 (History + Alerts)",
            goal="현재는 최신 1회 리포트 위주라 '흐름'이 안 보인다. 최근 N회(예: 10회) 실행 이력, 오류/정체 경고, intake(미디어/antigravity) 확장 카드까지 포함한 v2 대시보드를 만든다.",
            deliverables=[
                "dashboard(Next.js) 안에 `/status` 같은 단일 화면 추가 또는 `outputs/bridge/trigger_dashboard.html` 개선 PR",
                "읽는 데이터: `outputs/bridge/trigger_report_history.jsonl`(최근 N줄), `outputs/*_intake_latest.json`",
                "사용법 5줄(로컬에서 어떻게 여는지)",
            ],
            acceptance=[
                "‘최근 10회’가 시간순으로 보임",
                "실패/에러가 있으면 화면에서 빨간색으로 즉시 표시",
                "외부 API 키/네트워크 없이 동작",
            ],
            constraints=[
                "외부 API/키 요구 금지",
                "워크스페이스 파일(JSON/JSONL)만 읽기",
                "자동 새로고침 또는 폴링 유지",
            ],
            context_files=context,
        ),
        WorkOrder(
            agent="claude_sena",
            title="Self-Compression: Human Summary Layer",
            goal="Self-Compression 결과를 ‘인간이 바로 읽는 요약(5~12줄)’로 강화한다. (예: 낮/밤, 도시/자연, 이동/정지, 감정/리듬 키워드) 같은 태그를 만들어서 리포트에 붙인다.",
            deliverables=[
                "`scripts/self_expansion/self_compression.py` 개선 또는 `scripts/self_expansion/human_summary.py` 신규",
                "출력: `outputs/self_compression_human_summary_latest.json` (+ history jsonl)",
                "샘플 실행 예시(명령 1줄) + 출력 예시(짧게)",
            ],
            acceptance=[
                "네트워크 없이 실행 가능",
                "대용량 원문 저장 금지(요약/메타 중심)",
                "full_cycle 리포트에 연결 가능(키/경로 명확)",
            ],
            constraints=[
                "네트워크 사용 금지",
                "큰 파일 원문을 outputs에 복사 금지",
            ],
            context_files=context,
        ),
    ]

    written = []
    for wo in orders:
        written.append(write_work_order(w, wo))
    return written

