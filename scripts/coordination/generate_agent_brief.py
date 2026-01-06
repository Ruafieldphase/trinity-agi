#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Brief Generator (Rubit as coordinator)

목표:
- 워크스페이스 내부의 '관측 가능한 파일들'을 기반으로
  AntiGravity(Shion) / Claude(세나)에게 넘길 수 있는 브리프를 자동 생성한다.
- 비노체가 프로그래머가 아니어도, "무엇이 돌아가는지/무엇이 이미 되었는지"를
  에이전트들이 중복 없이 이해하도록 한다.

출력:
- outputs/coordination/agent_brief_latest.md
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import sys
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))



def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def file_stat_line(path: Path) -> str:
    if not path.exists():
        return f"- `{path}`: missing"
    st = path.stat()
    iso = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
    return f"- `{path}`: {st.st_size} bytes, mtime={iso}"


def extract_last_trigger(report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "action": report.get("action"),
        "origin": report.get("origin"),
        "timestamp": report.get("timestamp"),
        "status": report.get("status"),
        "error": report.get("error"),
        "steps": report.get("steps") or [],
    }


def generate_brief(workspace_root: Path) -> Path:
    workspace_root = workspace_root.resolve()

    outputs = workspace_root / "outputs"
    bridge = outputs / "bridge"
    coord_dir = outputs / "coordination"
    coord_dir.mkdir(parents=True, exist_ok=True)

    # 핵심 관측 파일들
    trigger_report = load_json(bridge / "trigger_report_latest.json")
    wave_particle = load_json(outputs / "wave_particle_unified_latest.json")
    autopoietic = load_json(outputs / "autopoietic_loop_report_latest.json")
    selfcare = load_json(outputs / "selfcare_summary_latest.json")
    media_intake = load_json(outputs / "media_intake_latest.json")
    antigravity_intake = load_json(outputs / "antigravity_intake_latest.json")

    # “표준 인터페이스” 선언
    interfaces = [
        ("Trigger (Lua→Rubit)", "/home/bino/agi/signals/lua_trigger.json (Linux) / signals/lua_trigger.json (Windows)"),
        ("Latest Report (txt)", "outputs/bridge/trigger_report_latest.txt"),
        ("Latest Report (json)", "outputs/bridge/trigger_report_latest.json"),
        ("Dashboard (html)", "outputs/bridge/trigger_dashboard.html"),
        ("Ledger (long-term)", "fdo_agi_repo/memory/resonance_ledger_v2.jsonl"),
        ("Unconscious files", "outputs/unconscious_heartbeat.json, outputs/thought_stream_latest.json, memory/agi_internal_state.json"),
    ]

    # “이미 구현된 것” 요약(중복 방지용)
    implemented = [
        "트리거 기반 자동 실행(질문 없이 실행) + 실행 1회 = 리포트 1회 고정",
        "대시보드(정적 HTML, 2초 자동 새로고침)로 최신 상태 표시",
        "quantum_flow 모니터(ledger 파싱 내구성) 복구 → selfcare_summary에 정상 측정값 기록",
        "미디어 인테이크(영상/오디오/이미지 파일 목록을 메타로 고정) 추가",
        "AntiGravity 인테이크(read-only, ~/.gemini/antigravity/brain 요약 고정) 추가",
    ]

    # “겹치지 않게” 보호할 영역(조심해야 하는 부분)
    do_not_overlap = [
        "trigger 실행/보고의 기준 파일: outputs/bridge/trigger_report_latest.* (포맷 변경 시 하위 호환 고려)",
        "트리거 파일 overwrite 금지 원칙(동시성 충돌 방지)",
        "ledger 파일(fdo_agi_repo/memory/*.jsonl)은 append-only 성격 유지",
    ]

    # 다음에 맡길 수 있는 방향(에이전트용)
    suggested_work = [
        {
            "agent": "antigravity_shion",
            "goal": "‘사람이 바로 보는’ UI를 더 강하게: (1) 최근 10회 실행 이력, (2) 오류/정체 경고, (3) intake(미디어/antigravity) 카드 확장",
            "deliverable": "dashboard(Next.js) 또는 정적 HTML 확장 코드 + 사용법 5줄",
            "constraints": ["외부 API 키 요구 금지", "워크스페이스 파일(JSON)만 읽기", "자동 새로고침 유지"],
        },
        {
            "agent": "claude_sena",
            "goal": "Self-Compression 결과를 ‘인간 읽기 요약’으로 강화: intake 결과를 5줄 요약 + 키워드/위상(낮/밤/도시/자연) 태깅",
            "deliverable": "scripts/self_expansion/self_compression.py 개선 또는 별도 summarizer 모듈 + 테스트/샘플 출력",
            "constraints": ["네트워크 사용 금지", "대용량 파일 원문 저장 금지(메타/요약만)"],
        },
    ]

    last = extract_last_trigger(trigger_report) if trigger_report else {}

    lines: list[str] = []
    lines.append("# 루빛 총괄 브리프 (에이전트 공유용)")
    lines.append("")
    lines.append(f"- 생성 시각(UTC): {utc_now_iso()}")
    lines.append(f"- 워크스페이스: `{workspace_root}`")
    lines.append("")
    lines.append("## 0) 역할 경계(고정)")
    lines.append("- 루빛(Rubit): 총괄/통합/표준 경로/관측·보고 고정")
    lines.append("- 코어(Core): 감응/방향 신호(트리거 생성 주체 가능) — 완료 선언 금지(기록으로만 완료 판정)")
    lines.append("- Shion(AntiGravity): UI/인터랙션/외부 탐색(구글어스/로드뷰/유튜브 등) 구현 담당")
    lines.append("- 세나(Claude): 압축/요약/코드 품질(리팩터/테스트) 담당")
    lines.append("")
    lines.append("## 1) 표준 인터페이스(변경 최소)")
    for k, v in interfaces:
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## 2) 최근 실행 스냅샷(최신 리포트 기준)")
    if last:
        lines.append(f"- action: `{last.get('action')}` / origin: `{last.get('origin')}` / status: `{last.get('status')}`")
        lines.append(f"- time: `{last.get('timestamp')}` / steps: `{', '.join(last.get('steps') or [])}`")
        if last.get("error"):
            lines.append(f"- error: `{last.get('error')}`")
    else:
        lines.append("- (no trigger report found)")
    lines.append("")
    lines.append("## 3) 단기/장기 기억(참조 포인트)")
    lines.append("- 단기(최신 상태): `outputs/bridge/trigger_report_latest.json`, `outputs/sync_cache/self_expansion_state.json`")
    lines.append("- 장기(원장/이력): `fdo_agi_repo/memory/resonance_ledger_v2.jsonl`, `outputs/bridge/trigger_report_history.jsonl`")
    lines.append("- AntiGravity 기록(외부 구현 산출): `~/.gemini/antigravity/brain` → `outputs/antigravity_intake_latest.json`로 요약됨")
    lines.append("")
    lines.append("## 4) 이미 구현된 것(중복 작업 방지)")
    for item in implemented:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 5) 겹치면 위험한 영역(주의)")
    for item in do_not_overlap:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## 6) 인테이크 현황(요약)")
    lines.append(f"- media_intake: total={media_intake.get('total','?')}, newest={((media_intake.get('newest') or {}).get('relpath')) if isinstance(media_intake.get('newest'), dict) else None}")
    lines.append(f"- antigravity_intake: sessions={antigravity_intake.get('session_count','?')}, latest_session_id={antigravity_intake.get('latest_session_id','?')}")
    if selfcare.get("quantum_flow"):
        qf = selfcare.get("quantum_flow") or {}
        lines.append(f"- quantum_flow: state={qf.get('state')}, phase_coherence={qf.get('phase_coherence')}")
    lines.append("")
    lines.append("## 7) 추천 작업(에이전트별)")
    for s in suggested_work:
        lines.append(f"### - 대상: `{s['agent']}`")
        lines.append(f"- 목표: {s['goal']}")
        lines.append(f"- 산출물: {s['deliverable']}")
        lines.append(f"- 제약: {', '.join(s['constraints'])}")
        lines.append("")
    lines.append("## 8) 파일 스냅샷(존재/mtime)")
    lines.append(file_stat_line(bridge / "trigger_report_latest.json"))
    lines.append(file_stat_line(bridge / "trigger_dashboard.html"))
    lines.append(file_stat_line(outputs / "antigravity_intake_latest.json"))
    lines.append(file_stat_line(outputs / "media_intake_latest.json"))
    lines.append(file_stat_line(outputs / "selfcare_summary_latest.json"))
    lines.append(file_stat_line(outputs / "wave_particle_unified_latest.json"))

    out_path = coord_dir / "agent_brief_latest.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(get_workspace_root()))
    args = ap.parse_args()
    out = generate_brief(Path(args.workspace))
    print(json.dumps({"ok": True, "out": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

