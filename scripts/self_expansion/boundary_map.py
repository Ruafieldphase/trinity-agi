#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boundary Map (when/where/who 기반 '입자 경계' 요약)

목표:
- "여행/탐색을 통해 경계(허용/금지/주의)를 학습한다"는 관점을
  시스템이 관측 가능한 출력 파일로 고정한다.
- 외부 모델 호출 없이, 탐색 세션(JSON/MD/TXT)에서 제공된 boundaries를
  집계/정리한다.

입력(간접):
- outputs/exploration_intake_latest.json

출력:
- outputs/boundary_map_latest.json
- outputs/boundary_map_history.jsonl (append)
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _norm_polarity(raw: Any) -> str:
    v = str(raw or "").strip().lower()
    if v in ("deny", "forbid", "no", "ban", "금지", "불가"):
        return "deny"
    if v in ("allow", "yes", "ok", "허용", "가능"):
        return "allow"
    if v in ("caution", "warn", "주의", "조심"):
        return "caution"
    return "unknown"


def _load_system_constraints(workspace_root: Path) -> dict[str, Any]:
    """
    시스템의 '경계/제약' 신호를 한 번에 모은다.
    - 행동을 정하지 않고(=policy 아님) 관측 가능한 상태만 가져온다.
    """
    outputs = workspace_root / "outputs"
    signals = workspace_root / "signals"

    def ld(p: Path) -> dict[str, Any]:
        return _safe_load_json(p) or {}

    return {
        "constitution": ld(outputs / "bridge" / "constitution_review_latest.json"),
        "rest_gate": ld(outputs / "safety" / "rest_gate_latest.json"),
        "natural_drift": ld(outputs / "natural_rhythm_drift_latest.json"),
        "life_state": ld(outputs / "sync_cache" / "life_state.json"),
        "body_allow_browser": ld(signals / "body_allow_browser.json"),
        "body_stop_exists": bool((signals / "body_stop.json").exists()),
    }


def _file_mtime_ts(path: Path, fallback: float) -> float:
    try:
        return float(path.stat().st_mtime)
    except Exception:
        return float(fallback)


def _add_system_rule(
    *,
    rules: list["BoundaryRule"],
    polarity: str,
    text: str,
    when_ts: float,
    source: str,
    filename: str,
) -> None:
    text = str(text or "").strip()
    if not text:
        return
    rules.append(
        BoundaryRule(
            polarity=_norm_polarity(polarity),
            text=text,
            session_title="SYSTEM_CONSTRAINT",
            session_source=str(source),
            session_filename=str(filename),
            session_timestamp=float(when_ts),
            where={"platform": "windows", "layer": "constraints"},
            who={"origin": "system"},
        )
    )


@dataclass
class BoundaryRule:
    polarity: str  # allow/deny/caution/unknown
    text: str
    session_title: str
    session_source: str
    session_filename: str
    session_timestamp: float
    where: Dict[str, Any]
    who: Dict[str, Any]


def build_boundary_map(workspace_root: Path, max_rules: int = 200) -> Dict[str, Any]:
    workspace_root = workspace_root.resolve()
    exploration_latest = workspace_root / "outputs" / "exploration_intake_latest.json"
    data = _safe_load_json(exploration_latest) or {}

    sessions = data.get("sessions", [])
    if not isinstance(sessions, list):
        sessions = []

    rules: List[BoundaryRule] = []
    for s in sessions:
        if not isinstance(s, dict):
            continue
        b = s.get("boundaries", [])
        if not isinstance(b, list):
            b = []
        where = s.get("where", {}) if isinstance(s.get("where"), dict) else {}
        who = s.get("who", {}) if isinstance(s.get("who"), dict) else {}
        for item in b:
            if not isinstance(item, dict):
                continue
            text = item.get("text") or item.get("rule") or item.get("note") or ""
            if not isinstance(text, str) or not text.strip():
                continue
            rules.append(
                BoundaryRule(
                    polarity=_norm_polarity(item.get("polarity")),
                    text=text.strip(),
                    session_title=str(s.get("title") or ""),
                    session_source=str(s.get("source") or ""),
                    session_filename=str(s.get("filename") or ""),
                    session_timestamp=float(s.get("timestamp") or 0.0),
                    where=where,
                    who=who,
                )
            )
            if len(rules) >= max_rules:
                break
        if len(rules) >= max_rules:
            break

    # --- System constraints (4 forces 유사: safety/rest/rhythm/guard) ---
    # "아이디어"가 아니라 관측 가능한 경계만 BoundaryRule로 고정한다.
    now = time.time()
    constraints = _load_system_constraints(workspace_root)

    # 1) Safety / Ethics (Constitution)
    c = constraints.get("constitution") if isinstance(constraints.get("constitution"), dict) else {}
    cst = str((c.get("status") or "")).upper().strip()
    flags = c.get("flags") if isinstance(c.get("flags"), list) else []
    if cst and cst not in {"PROCEED", "OK"}:
        _add_system_rule(
            rules=rules,
            polarity=("deny" if cst in {"BLOCK", "REVIEW"} else "caution"),
            text=f"safety={cst} (flags={len(flags)})",
            when_ts=_file_mtime_ts(workspace_root / "outputs" / "bridge" / "constitution_review_latest.json", now),
            source="outputs/bridge/constitution_review_latest.json",
            filename=str(workspace_root / "outputs" / "bridge" / "constitution_review_latest.json"),
        )
    elif flags:
        _add_system_rule(
            rules=rules,
            polarity="caution",
            text=f"safety=PROCEED but flags={len(flags)}",
            when_ts=_file_mtime_ts(workspace_root / "outputs" / "bridge" / "constitution_review_latest.json", now),
            source="outputs/bridge/constitution_review_latest.json",
            filename=str(workspace_root / "outputs" / "bridge" / "constitution_review_latest.json"),
        )

    # 2) Homeostasis (RestGate)
    rg = constraints.get("rest_gate") if isinstance(constraints.get("rest_gate"), dict) else {}
    rgst = str((rg.get("status") or "")).upper().strip()
    if rgst == "REST":
        _add_system_rule(
            rules=rules,
            polarity="caution",
            text="rest_gate=REST (execution should settle)",
            when_ts=_file_mtime_ts(workspace_root / "outputs" / "safety" / "rest_gate_latest.json", now),
            source="outputs/safety/rest_gate_latest.json",
            filename=str(workspace_root / "outputs" / "safety" / "rest_gate_latest.json"),
        )

    # 3) Natural rhythm drift (Drift)
    dr = constraints.get("natural_drift") if isinstance(constraints.get("natural_drift"), dict) else {}
    if dr and (dr.get("ok") is False):
        _add_system_rule(
            rules=rules,
            polarity="caution",
            text="natural_rhythm_drift=detected (reduce churn)",
            when_ts=_file_mtime_ts(workspace_root / "outputs" / "natural_rhythm_drift_latest.json", now),
            source="outputs/natural_rhythm_drift_latest.json",
            filename=str(workspace_root / "outputs" / "natural_rhythm_drift_latest.json"),
        )

    # 4) Input guard / Kill-switch (Body stop)
    if bool(constraints.get("body_stop_exists")):
        _add_system_rule(
            rules=rules,
            polarity="deny",
            text="body_stop.json present (supervised body must abort)",
            when_ts=now,
            source="signals/body_stop.json",
            filename=str(workspace_root / "signals" / "body_stop.json"),
        )

    # 5) Allowlist boundary (Browser)
    ab = constraints.get("body_allow_browser") if isinstance(constraints.get("body_allow_browser"), dict) else {}
    if bool(ab.get("allow")):
        _add_system_rule(
            rules=rules,
            polarity="allow",
            text="browser_roam_allow=true (domain allowlist enforced in controller)",
            when_ts=_file_mtime_ts(workspace_root / "signals" / "body_allow_browser.json", now),
            source="signals/body_allow_browser.json",
            filename=str(workspace_root / "signals" / "body_allow_browser.json"),
        )

    # 6) Idle as normal survival state (관측)
    life = constraints.get("life_state") if isinstance(constraints.get("life_state"), dict) else {}
    ls = str(life.get("state") or "").strip().upper()
    if ls.startswith("ALIVE"):
        _add_system_rule(
            rules=rules,
            polarity="allow",
            text=f"life_state={ls} (idle is allowed)",
            when_ts=_file_mtime_ts(workspace_root / "outputs" / "sync_cache" / "life_state.json", now),
            source="outputs/sync_cache/life_state.json",
            filename=str(workspace_root / "outputs" / "sync_cache" / "life_state.json"),
        )

    # cap again (system rules may add more)
    rules = rules[:max_rules]

    rules.sort(key=lambda r: r.session_timestamp, reverse=True)

    counts = {"allow": 0, "deny": 0, "caution": 0, "unknown": 0}
    for r in rules:
        counts[r.polarity] = counts.get(r.polarity, 0) + 1

    newest = asdict(rules[0]) if rules else None
    now = time.time()
    out: Dict[str, Any] = {
        "ok": True,
        "scanned_at": utc_iso(now),
        "sources": {
            "exploration_intake_latest.json": str(exploration_latest),
            "constitution_review_latest.json": str(workspace_root / "outputs" / "bridge" / "constitution_review_latest.json"),
            "rest_gate_latest.json": str(workspace_root / "outputs" / "safety" / "rest_gate_latest.json"),
            "natural_rhythm_drift_latest.json": str(workspace_root / "outputs" / "natural_rhythm_drift_latest.json"),
            "life_state.json": str(workspace_root / "outputs" / "sync_cache" / "life_state.json"),
            "body_allow_browser.json": str(workspace_root / "signals" / "body_allow_browser.json"),
        },
        "stats": {
            "total_rules": len(rules),
            "counts": counts,
        },
        "newest_rule": newest,
        "rules": [asdict(r) for r in rules[: min(len(rules), 80)]],
        "note": "rules에는 최근 80개만 포함(요약). 원본은 exploration sessions 파일/outputs를 참조.",
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--out", type=str, default=str(Path("outputs") / "boundary_map_latest.json"))
    ap.add_argument("--history", type=str, default=str(Path("outputs") / "boundary_map_history.jsonl"))
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (ws / out_path).resolve()
    hist_path = Path(args.history)
    if not hist_path.is_absolute():
        hist_path = (ws / hist_path).resolve()

    result = build_boundary_map(ws)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        with hist_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    except Exception:
        pass

    print(json.dumps({"ok": True, "out": str(out_path), "rules": (result.get("stats") or {}).get("total_rules", 0)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
