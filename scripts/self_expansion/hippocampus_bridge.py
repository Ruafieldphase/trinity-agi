#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hippocampus Bridge (Experience → Episodic Memory)

목표:
- '여행/탐색(when/where/who + boundary)'과 '윈도우 사용(OBS recode)'을
  해마(Hippocampus)의 사건 기억(episodic)으로 최소 단위로 고정한다.
- 무거운 분석/모델 호출 없이, 이미 생성된 outputs 요약 파일들만 사용한다.

입력:
- outputs/exploration_intake_latest.json
- outputs/boundary_map_latest.json
- outputs/obs_recode_intake_latest.json

출력:
- outputs/hippocampus_bridge_latest.json
- outputs/hippocampus_bridge_history.jsonl (append)
"""

from __future__ import annotations

import argparse
import json
import time
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from workspace_root import get_workspace_root
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))



def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _safe_excerpt(text: Any, max_len: int = 240) -> str:
    s = str(text or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


def run_hippocampus_bridge(workspace_root: Path) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    outputs = workspace_root / "outputs"

    # Ensure repo root is importable (for fdo_agi_repo, etc.)
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))

    exploration = safe_load_json(outputs / "exploration_intake_latest.json") or {}
    boundary_map = safe_load_json(outputs / "boundary_map_latest.json") or {}
    obs_idx = safe_load_json(outputs / "obs_recode_intake_latest.json") or {}
    Core_intake = safe_load_json(outputs / "core_conversation_intake_latest.json") or {}

    stored = []
    errors = []

    try:
        from fdo_agi_repo.copilot.hippocampus import CopilotHippocampus

        hippo = CopilotHippocampus(workspace_root)

        # 1) Travel/Exploration 최신 세션(있으면) → episodic
        latest_session = exploration.get("latest_session")
        if isinstance(latest_session, dict):
            item = {
                "type": "experience_exploration",
                "source": latest_session.get("source"),
                "title": latest_session.get("title"),
                "tags": latest_session.get("tags", []),
                "where": latest_session.get("where", {}),
                "who": latest_session.get("who", {}),
                "session_timestamp": latest_session.get("timestamp"),
                "notes_excerpt": _safe_excerpt(latest_session.get("notes", "")),
                "boundary_count": len(latest_session.get("boundaries", []) or []),
                "comparison_count": len(latest_session.get("comparisons", []) or []),
                "origin": "hippocampus_bridge",
            }
            hippo.long_term.store_episodic(item)
            stored.append({"stored": "experience_exploration", "title": item.get("title")})

        # 2) Boundary map newest rule (있으면) → episodic
        newest = boundary_map.get("newest_rule")
        stats = boundary_map.get("stats") if isinstance(boundary_map.get("stats"), dict) else {}
        total_rules = stats.get("total_rules") if isinstance(stats, dict) else None
        if isinstance(newest, dict):
            item = {
                "type": "experience_boundary",
                "polarity": newest.get("polarity"),
                "text": _safe_excerpt(newest.get("text", "")),
                "session_title": newest.get("session_title"),
                "session_source": newest.get("session_source"),
                "where": newest.get("where", {}),
                "who": newest.get("who", {}),
                "total_rules": total_rules,
                "origin": "hippocampus_bridge",
            }
            hippo.long_term.store_episodic(item)
            stored.append({"stored": "experience_boundary", "polarity": item.get("polarity")})

        # 3) OBS recode newest (있으면) → episodic
        newest_video = obs_idx.get("newest") if isinstance(obs_idx.get("newest"), dict) else None
        if isinstance(newest_video, dict):
            item = {
                "type": "experience_obs_recode",
                "newest_relpath": newest_video.get("relpath"),
                "newest_size": newest_video.get("size"),
                "newest_mtime_iso": newest_video.get("mtime_iso"),
                "total_videos": obs_idx.get("total"),
                "roots": obs_idx.get("roots"),
                "origin": "hippocampus_bridge",
            }
            hippo.long_term.store_episodic(item)
            stored.append({"stored": "experience_obs_recode", "newest": item.get("newest_relpath")})

        # 4) Core conversation newest (있으면) → episodic
        newest_doc = Core_intake.get("newest") if isinstance(Core_intake.get("newest"), dict) else None
        if isinstance(newest_doc, dict):
            item = {
                "type": "experience_core_conversation",
                "title": newest_doc.get("title"),
                "relpath": newest_doc.get("relpath"),
                "mtime_iso": newest_doc.get("mtime_iso"),
                "excerpt": newest_doc.get("excerpt"),
                "keyword_counts": newest_doc.get("keyword_counts"),
                "boundary_candidates": newest_doc.get("boundaries"),
                "origin": "hippocampus_bridge",
            }
            hippo.long_term.store_episodic(item)
            stored.append({"stored": "experience_core_conversation", "title": item.get("title")})

        # 5) Digital Twin Drift (있으면) → episodic
        twin_path = outputs / "sync_cache/digital_twin_state.json"
        if twin_path.exists():
            try:
                dt = json.loads(twin_path.read_text(encoding="utf-8"))
                mismatch = float(dt.get("mismatch_0_1", 0.0))
                if mismatch >= 0.35: # 관찰 가능한 수준의 불일치
                    item = {
                        "type": "system_drift",
                        "title": f"Digital Twin Drift detected (score: {mismatch:.2f})",
                        "mismatch": mismatch,
                        "route_hint": dt.get("route_hint"),
                        "action_phase": dt.get("observed", {}).get("action_phase"),
                        "recommended_phase": dt.get("observed", {}).get("recommended_phase"),
                        "timestamp": dt.get("generated_at_utc"),
                        "origin": "hippocampus_bridge"
                    }
                    hippo.long_term.store_episodic(item)
                    stored.append({"stored": "system_drift", "score": mismatch})
            except Exception as e:
                errors.append(f"Digital Twin Bridge Error: {e}")

    except Exception as e:
        errors.append(str(e))

    now = time.time()
    return {
        "ok": len(errors) == 0,
        "timestamp": utc_iso(now),
        "stored": stored,
        "errors": errors,
        "inputs": {
            "exploration_intake_latest.json": {"exists": (outputs / "exploration_intake_latest.json").exists()},
            "boundary_map_latest.json": {"exists": (outputs / "boundary_map_latest.json").exists()},
            "obs_recode_intake_latest.json": {"exists": (outputs / "obs_recode_intake_latest.json").exists()},
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(get_workspace_root()))
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    result = run_hippocampus_bridge(ws)

    out = ws / "outputs" / "hippocampus_bridge_latest.json"
    hist = ws / "outputs" / "hippocampus_bridge_history.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        with hist.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    except Exception:
        pass

    print(json.dumps({"ok": result.get("ok"), "stored": len(result.get("stored") or [])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
