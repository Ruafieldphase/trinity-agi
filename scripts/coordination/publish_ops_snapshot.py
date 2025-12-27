#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publish Ops Snapshot (local-only, best-effort)

목표:
- 비노체 개입 없이도, "현재 AGI가 무엇을 했는지/어디까지 왔는지"를
  외부 협업자(시안/세나)도 같은 기준으로 볼 수 있게 스냅샷을 고정한다.

원칙:
- 네트워크 사용 없음
- 비밀/PII 저장 금지(기존 요약/리포트 파일만 참조)
- 실패해도 조용히 종료(best-effort)
- 과도한 쓰기 방지: rate-limit + 내용 동일 시 skip
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INBOX = ROOT / "inputs" / "agent_inbox"
OUT_STATE = ROOT / "outputs" / "sync_cache" / "publish_ops_snapshot_state.json"

HUMAN_OPS = ROOT / "outputs" / "bridge" / "human_ops_summary_latest.txt"
TRIGGER_LATEST = ROOT / "outputs" / "bridge" / "trigger_report_latest.txt"
SAFETY_TXT = ROOT / "outputs" / "bridge" / "constitution_review_latest.txt"
SAFETY_JSON = ROOT / "outputs" / "bridge" / "constitution_review_latest.json"
AURA_JSON = ROOT / "outputs" / "aura_pixel_state.json"
ALLOW_BROWSER = ROOT / "signals" / "body_allow_browser.json"


def _read_text(path: Path, limit: int = 6000) -> str:
    try:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8", errors="replace") or "{}")
    except Exception:
        return {}


def _atomic_write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def _load_state() -> dict[str, Any]:
    return _read_json(OUT_STATE)


def _save_state(state: dict[str, Any]) -> None:
    try:
        OUT_STATE.parent.mkdir(parents=True, exist_ok=True)
        OUT_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def build_snapshot() -> str:
    aura = _read_json(AURA_JSON)
    allow = _read_json(ALLOW_BROWSER)

    lines: list[str] = []
    lines.append("# AGI Ops Snapshot (local)")
    lines.append(f"- generated_at_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    lines.append("")

    # Aura (한 줄)
    try:
        d = aura.get("decision", {}) if isinstance(aura, dict) else {}
        color = str(d.get("color") or "")
        state = str(d.get("state") or "")
        reason = str(d.get("reason") or "")
        lines.append("## Aura")
        lines.append(f"- state: {state}")
        if color:
            lines.append(f"- color: {color}")
        if reason:
            lines.append(f"- reason: {reason}")
        lines.append("")
    except Exception:
        pass

    # Browser roam (간단)
    try:
        if isinstance(allow, dict) and allow:
            lines.append("## Browser Roam")
            lines.append(f"- allow: {bool(allow.get('allow'))}")
            m = allow.get("max_tasks_per_hour")
            c = allow.get("min_cooldown_sec")
            if m is not None:
                lines.append(f"- max_tasks_per_hour: {m}")
            if c is not None:
                lines.append(f"- min_cooldown_sec: {c}")
            lines.append("")
    except Exception:
        pass

    # Human ops summary (원문 그대로 붙이지 않고, 파일 기준으로)
    lines.append("## Latest Human Ops Summary (file)")
    lines.append(f"- path: outputs/bridge/human_ops_summary_latest.txt")
    # 일부만 포함(이미 사람용 요약이라도 과도한 붙여넣기 방지)
    summary = _read_text(HUMAN_OPS, limit=1200).strip()
    if summary:
        lines.append("")
        lines.append("```")
        lines.append(summary)
        lines.append("```")
    lines.append("")

    # Trigger latest
    trig = _read_text(TRIGGER_LATEST, limit=900).strip()
    if trig:
        lines.append("## Latest Trigger Report (excerpt)")
        lines.append(f"- path: outputs/bridge/trigger_report_latest.txt")
        lines.append("")
        lines.append("```")
        lines.append(trig)
        lines.append("```")
        lines.append("")

    # Safety (첫 줄 요약만)
    sj = _read_json(SAFETY_JSON)
    if isinstance(sj, dict) and sj:
        lines.append("## Safety Review (summary)")
        lines.append("- path: outputs/bridge/constitution_review_latest.json")
        st = str(sj.get("status") or "").upper() or "UNKNOWN"
        flags = sj.get("flags")
        nr = str(sj.get("next_recommendation") or "")
        lines.append(f"- status: {st}")
        if isinstance(flags, list) and flags:
            lines.append(f"- flags: {', '.join(str(x) for x in flags[:8])}")
        else:
            lines.append("- flags: none")
        if nr:
            lines.append(f"- next: {nr}")
        lines.append("")
    else:
        safety = _read_text(SAFETY_TXT, limit=1200).strip()
        if safety:
            lines.append("## Safety Review (excerpt)")
            lines.append(f"- path: outputs/bridge/constitution_review_latest.txt")
            lines.append("")
            lines.append("```")
            # best-effort: find first non-empty line
            first = next((ln for ln in safety.splitlines() if ln.strip()), "")
            lines.append(first)
            lines.append("```")
            lines.append("")

    # Canonical links
    lines.append("## Canonical Files")
    for rel in [
        "outputs/bridge/human_ops_summary_latest.txt",
        "outputs/bridge/trigger_report_latest.json",
        "outputs/bridge/constitution_review_latest.txt",
        "outputs/self_compression_human_summary_latest.json",
        "outputs/exploration_intake_latest.json",
        "outputs/body_supervised_latest.json",
        "outputs/aura_pixel_state.json",
    ]:
        lines.append(f"- {rel}")
    lines.append("")

    return "\n".join(lines)


def should_publish(now_ts: float, content_digest: str, min_interval_s: int = 300) -> bool:
    st = _load_state()
    try:
        last_ts = float(st.get("last_published_ts") or 0.0)
    except Exception:
        last_ts = 0.0
    last_digest = str(st.get("last_digest") or "")
    # 내용이 바뀌면 즉시 갱신(동일 내용일 때만 rate-limit 강하게 적용).
    if last_digest and last_digest != content_digest:
        return True
    if last_digest == content_digest and (now_ts - last_ts) < (min_interval_s * 4):
        return False
    if last_ts and (now_ts - last_ts) < float(min_interval_s):
        return False
    return True


def publish() -> dict[str, Any]:
    now = time.time()
    content = build_snapshot()
    digest = _sha256(content)
    if not should_publish(now, digest):
        return {"ok": True, "published": False}

    targets = [
        INBOX / "claude_sena" / "OPS_SNAPSHOT.md",
        INBOX / "antigravity_sian" / "OPS_SNAPSHOT.md",
    ]
    for t in targets:
        _atomic_write_text(t, content)

    _save_state(
        {
            "last_published_ts": now,
            "last_digest": digest,
            "targets": [str(t) for t in targets],
        }
    )
    return {"ok": True, "published": True, "targets": [str(t) for t in targets]}


def main() -> int:
    try:
        res = publish()
        print(json.dumps(res, ensure_ascii=False))
        return 0
    except Exception:
        # best-effort: never fail the caller
        print(json.dumps({"ok": False, "published": False}, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
