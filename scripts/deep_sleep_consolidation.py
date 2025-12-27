#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Sleep Consolidation (compat/orchestrator)

의도:
- docs에서 언급되는 `scripts/deep_sleep_consolidation.py`가 누락되어 있어
  현재 워크스페이스에 존재하는 "수면/정리" 루틴을 안전하게 엮는 래퍼를 제공한다.
- 외부 네트워크 호출 없이, 로컬 파일/레저 기반만 수행한다.

기본 동작(안전):
1) auto_dream_pipeline (Resonance→Dream→Glymphatic→Memory) 실행
2) 결과를 outputs/deep_sleep_consolidation_latest.json/md 로 고정

주의:
- 이 스크립트는 '딥슬립'을 실제로 구현한다기보다, 이미 존재하는 파이프라인을
  "한 이름"으로 호출 가능하게 만드는 연결 고리다.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _safe_load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    outputs = root / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    pipeline = root / "scripts" / "auto_dream_pipeline.py"
    out_pipeline = outputs / "deep_sleep_dream_pipeline_latest.json"
    out_latest = outputs / "deep_sleep_consolidation_latest.json"
    out_md = outputs / "deep_sleep_consolidation_latest.md"

    start = time.time()
    now = utc_iso(start)

    if not pipeline.exists():
        out = {
            "ok": False,
            "timestamp": now,
            "error": f"missing auto_dream_pipeline.py: {pipeline}",
        }
        out_latest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        out_md.write_text(f"# Deep Sleep Consolidation\n\n- timestamp: `{now}`\n- status: `failed`\n- error: missing `{pipeline}`\n", encoding="utf-8")
        return 1

    cmd = [sys.executable, str(pipeline), "--output", str(out_pipeline)]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.verbose:
        cmd.append("--verbose")

    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=180, check=False)
    duration = time.time() - start

    pipeline_obj = _safe_load_json(out_pipeline) or {}
    ok = bool(pipeline_obj.get("success")) if isinstance(pipeline_obj, dict) else (proc.returncode == 0)

    result = {
        "ok": ok,
        "timestamp": now,
        "duration_sec": duration,
        "runner": {
            "cmd": cmd,
            "rc": proc.returncode,
            "stderr_tail": (proc.stderr or "")[-1500:],
        },
        "dream_pipeline": pipeline_obj,
    }
    out_latest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Deep Sleep Consolidation",
        "",
        f"- timestamp: `{now}`",
        f"- ok: `{ok}`",
        f"- duration_sec: `{duration:.2f}`",
        f"- rc: `{proc.returncode}`",
        "",
    ]
    try:
        md_lines.append("## Dream Pipeline Summary")
        md_lines.append(f"- resonance_events_processed: `{pipeline_obj.get('resonance_events_processed')}`")
        md_lines.append(f"- memories_consolidated: `{pipeline_obj.get('memories_consolidated')}`")
        md_lines.append(f"- dreams_generated: `{pipeline_obj.get('dreams_generated')}`")
        md_lines.append(f"- glymphatic_cycles: `{pipeline_obj.get('glymphatic_cycles')}`")
        md_lines.append(f"- total_cleanup_mb: `{pipeline_obj.get('total_cleanup_mb')}`")
        md_lines.append(f"- errors: `{len(pipeline_obj.get('errors') or [])}`")
    except Exception:
        pass
    md_lines.append("")
    out_md.write_text("\n".join(md_lines), encoding="utf-8")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

