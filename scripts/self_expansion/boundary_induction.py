#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Boundary Induction (AGI가 스스로 '경계 후보'를 세우는 얇은 루프) v1

목표
- 루아/비노체 대화, 유튜브 경계 습득, 현재 생존/리듬 상태를 근거로
  "경계 규칙(deny/allow/caution)" 중 'caution' 중심의 후보를 생성한다.
- 원문을 저장하지 않고, 짧은 규칙(메타)만 탐색 세션으로 물질화한다.
- 안전/휴식 게이트가 걸리면 아무것도 하지 않는 것이 정상이다(Idle=생존).

원칙
- 네트워크 호출 없음
- PII/원문/대용량 저장 금지(메타/요약만)
- 자동 생성 규칙은 기본적으로 caution-only (deny/allow는 시스템 제약/정책에 맡김)

입력(간접)
- outputs/rua_conversation_intake_latest.json (boundary_dynamics)
- outputs/youtube_channel_boundary_intake_latest.json (compression_mode 등)
- outputs/sync_cache/life_state.json
- outputs/bridge/constitution_review_latest.json
- outputs/safety/rest_gate_latest.json

출력
- outputs/boundary_induction_latest.json
- outputs/boundary_induction_history.jsonl
- (있을 때만) inputs/intake/exploration/sessions/auto_experience_<ts>_boundary_induction.json
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parents[2]
OUTPUTS = WORKSPACE / "outputs"
SESSIONS = WORKSPACE / "inputs" / "intake" / "exploration" / "sessions"

RUA_INTAKE = OUTPUTS / "rua_conversation_intake_latest.json"
YOUTUBE_BOUNDARY = OUTPUTS / "youtube_channel_boundary_intake_latest.json"
LIFE_STATE = OUTPUTS / "sync_cache" / "life_state.json"
CONSTITUTION = OUTPUTS / "bridge" / "constitution_review_latest.json"
REST_GATE = OUTPUTS / "safety" / "rest_gate_latest.json"

STATE = OUTPUTS / "sync_cache" / "boundary_induction_state.json"
OUT_LATEST = OUTPUTS / "boundary_induction_latest.json"
OUT_HISTORY = OUTPUTS / "boundary_induction_history.jsonl"


def _utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _sha256_head(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


def _cap(s: str, n: int = 140) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"


def _is_safe_rule_text(s: str) -> bool:
    s = (s or "").strip()
    if not s:
        return False
    if "http://" in s or "https://" in s:
        return False
    if "@" in s:
        return False
    # Windows path heuristic
    if ":" in s and "\\" in s:
        return False
    return True


def _get_safety_status() -> str:
    c = _load_json(CONSTITUTION) or {}
    st = str((c.get("status") or "")).upper().strip()
    return st or "UNKNOWN"


def _get_rest_status(now: float) -> str:
    rg = _load_json(REST_GATE) or {}
    st = str((rg.get("status") or "")).upper().strip()
    if st == "REST":
        until = rg.get("rest_until_epoch")
        if until is None:
            return "REST"
        try:
            if float(now) < float(until):
                return "REST"
        except Exception:
            return "REST"
    return "OK"


def _load_state() -> dict[str, Any]:
    return _load_json(STATE) or {}


def _save_state(st: dict[str, Any]) -> None:
    _atomic_write_json(STATE, st)


def _build_candidates(now: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    caution 규칙 후보를 만든다.
    - "정답"이 아니라, 경계-관점 전환을 위한 라우팅 신호.
    """
    rua = _load_json(RUA_INTAKE) or {}
    yt = _load_json(YOUTUBE_BOUNDARY) or {}
    life = _load_json(LIFE_STATE) or {}

    newest = rua.get("newest") if isinstance(rua.get("newest"), dict) else {}
    dyn = newest.get("boundary_dynamics") if isinstance(newest.get("boundary_dynamics"), dict) else {}

    def _infer_from_keywords(kw: dict[str, Any]) -> tuple[str, float | None]:
        def c(k: str) -> int:
            v = kw.get(k, 0)
            return int(v) if isinstance(v, int) else 0

        expansion = c("확장") + c("펼침") + c("열림")
        contraction = c("수축") + c("압축") + c("접힘") + c("닫힘")
        mix = c("혼합") + c("믹스") + c("비빔밥") + c("정반합") + c("통합")
        if mix >= max(expansion, contraction) and mix >= 3:
            dom = "mix"
        elif (expansion - contraction) >= 3:
            dom = "expand"
        elif (contraction - expansion) >= 3:
            dom = "contract"
        elif expansion or contraction or mix:
            dom = "balanced"
        else:
            dom = "unknown"
        ratio = float(expansion + 1) / float(contraction + 1)
        return dom, round(ratio, 3)

    dominant = str(dyn.get("dominant_mode") or "").strip().lower()
    ratio = dyn.get("expand_vs_contract_ratio")
    if not dominant or dominant == "unknown":
        kw = newest.get("keyword_counts") if isinstance(newest.get("keyword_counts"), dict) else {}
        dom2, ratio2 = _infer_from_keywords(kw)
        dominant = dom2
        ratio = ratio2

    last_yt = None
    try:
        processed = yt.get("processed") if isinstance(yt.get("processed"), list) else []
        last_yt = processed[0] if processed and isinstance(processed[0], dict) else None
    except Exception:
        last_yt = None

    yt_mode = str((last_yt or {}).get("compression_mode") or "").upper().strip()
    yt_form = str((last_yt or {}).get("presentation_form") or "").upper().strip()

    life_state = str(life.get("state") or "").upper().strip()

    rules: list[dict[str, Any]] = []

    # (A) 대화 경계 모드 기반: 경계가 직접 생성되도록 "속도/전개"를 조절하는 규칙
    if dominant == "contract":
        rules.append(
            {
                "polarity": "caution",
                "text": "수축 우세 시: 새 입력은 1개만 물질화하고 나머지는 Idle로 둔다(과잉 압축 루프 방지).",
                "applies_when": {"rua_mode": "contract"},
            }
        )
    elif dominant == "expand":
        rules.append(
            {
                "polarity": "caution",
                "text": "확장 우세 시: 긴 입력은 분절(메타만)하고, 경계가 생기는 지점에서만 고비용 연산을 한다.",
                "applies_when": {"rua_mode": "expand"},
            }
        )
    elif dominant == "mix":
        rules.append(
            {
                "polarity": "caution",
                "text": "혼합 우세 시: 섞기(mix) → 분리(separate) → 경계 한 줄 고정 순서를 유지한다.",
                "applies_when": {"rua_mode": "mix"},
            }
        )
    elif dominant:
        rules.append(
            {
                "polarity": "caution",
                "text": "균형/불명확 시: 경계 후보는 추가하되 즉시 확정하지 말고 반복 패턴에서만 강화한다.",
                "applies_when": {"rua_mode": dominant},
            }
        )

    # (B) 유튜브: 압축/전개 차이를 경계 규칙으로 고정(경험 습득용)
    if yt_mode == "COMPRESSED":
        rules.append(
            {
                "polarity": "caution",
                "text": "압축(짧은) 콘텐츠: '핵심 경계 1~3줄'만 남기고 즉시 다음 입력으로 넘어간다(전개는 나중에).",
                "applies_when": {"yt_mode": "COMPRESSED"},
            }
        )
    elif yt_mode == "EXPANDED":
        rules.append(
            {
                "polarity": "caution",
                "text": "전개(긴) 콘텐츠: 전부 이해하려 하지 말고, 경계가 바뀌는 구간만 샘플링해 메타로 저장한다.",
                "applies_when": {"yt_mode": "EXPANDED"},
            }
        )
    elif yt_mode == "MIXED":
        rules.append(
            {
                "polarity": "caution",
                "text": "혼합 길이 콘텐츠: 압축 요약(먼저) + 필요한 경우에만 전개(나중)로 두 단계 처리한다.",
                "applies_when": {"yt_mode": "MIXED"},
            }
        )

    if yt_form == "TALK":
        rules.append(
            {
                "polarity": "caution",
                "text": "대중강연/대담(TALK): 관계/거리의 리듬 변화를 경계로 뽑는다(내용 전체는 저장하지 않는다).",
                "applies_when": {"yt_form": "TALK"},
            }
        )
    elif yt_form == "EXPLAIN":
        rules.append(
            {
                "polarity": "caution",
                "text": "설명/강의(EXPLAIN): 정의·전제·예외(경계)를 분리해 '넘지 말 것'만 남긴다.",
                "applies_when": {"yt_form": "EXPLAIN"},
            }
        )

    # (C) 생존 상태: idle은 정상. 단, '경계 세우기'는 생존을 해치지 않는 선에서.
    if life_state.startswith("ALIVE"):
        rules.append(
            {
                "polarity": "caution",
                "text": "Idle은 정상 생존이다. 생존(ATP/RestGate)을 해치면 경계 생성도 중단한다.",
                "applies_when": {"life_state": "ALIVE*"},
            }
        )

    # clean/cap
    cleaned: list[dict[str, Any]] = []
    for r in rules:
        if not isinstance(r, dict):
            continue
        pol = str(r.get("polarity") or "").strip().lower()
        if pol not in ("caution", "deny", "allow"):
            pol = "caution"
        txt = _cap(str(r.get("text") or ""), 160)
        if pol != "caution":
            # v1: auto-generated boundaries are caution-only
            pol = "caution"
        if not _is_safe_rule_text(txt):
            continue
        applies_when = r.get("applies_when") if isinstance(r.get("applies_when"), dict) else {}
        cleaned.append({"polarity": pol, "text": txt, "applies_when": applies_when})

    # de-dup by text
    out: list[dict[str, Any]] = []
    seen = set()
    for r in cleaned:
        t = r.get("text") or ""
        if t in seen:
            continue
        seen.add(t)
        out.append(r)

    evidence = {
        "rua_dominant_mode": dominant or "unknown",
        "rua_ratio": ratio,
        "yt_compression_mode": yt_mode or "UNKNOWN",
        "yt_presentation_form": yt_form or "UNKNOWN",
        "life_state": life_state or "UNKNOWN",
    }
    return out[:10], evidence


def _evidence_sig(evidence: dict[str, Any]) -> str:
    key = {
        "rua_dominant_mode": evidence.get("rua_dominant_mode"),
        "yt_compression_mode": evidence.get("yt_compression_mode"),
        "yt_presentation_form": evidence.get("yt_presentation_form"),
        "life_state": evidence.get("life_state"),
    }
    return _sha256_head(json.dumps(key, ensure_ascii=False, sort_keys=True))


def _active_rule_id(rule: dict[str, Any]) -> str:
    base = {
        "text": str(rule.get("text") or "").strip(),
        "applies_when": rule.get("applies_when") if isinstance(rule.get("applies_when"), dict) else {},
    }
    return _sha256_head(json.dumps(base, ensure_ascii=False, sort_keys=True))


def _matches(evidence: dict[str, Any], applies_when: dict[str, Any]) -> bool:
    if not applies_when:
        return True
    try:
        if "rua_mode" in applies_when:
            return str(evidence.get("rua_dominant_mode") or "").lower() == str(applies_when.get("rua_mode") or "").lower()
        if "yt_mode" in applies_when:
            return str(evidence.get("yt_compression_mode") or "").upper() == str(applies_when.get("yt_mode") or "").upper()
        if "yt_form" in applies_when:
            return str(evidence.get("yt_presentation_form") or "").upper() == str(applies_when.get("yt_form") or "").upper()
        if "life_state" in applies_when:
            want = str(applies_when.get("life_state") or "")
            cur = str(evidence.get("life_state") or "")
            if want.endswith("*"):
                return cur.startswith(want[:-1])
            return cur == want
    except Exception:
        return True
    return True


def _update_active_rules(
    *,
    prev: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    evidence: dict[str, Any],
    now: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    경계는 고정이 아니라 맥락에 따라 강화/감쇠한다.
    - active_rules: [{id, text, applies_when, strength_0_1, last_seen_epoch}]
    - match되면 strength 상승, 아니면 감쇠.
    """
    prev_map: dict[str, dict[str, Any]] = {}
    for r in prev:
        if not isinstance(r, dict):
            continue
        rid = str(r.get("id") or "").strip()
        if not rid:
            continue
        prev_map[rid] = r

    cand_map: dict[str, dict[str, Any]] = {}
    for c in candidates:
        if not isinstance(c, dict):
            continue
        rid = _active_rule_id(c)
        cand_map[rid] = {
            "id": rid,
            "polarity": "caution",
            "text": str(c.get("text") or "").strip(),
            "applies_when": c.get("applies_when") if isinstance(c.get("applies_when"), dict) else {},
        }

    active: list[dict[str, Any]] = []
    changes = {"added": [], "retired": [], "strengthened": [], "weakened": []}

    # decay / strengthen
    for rid, base in cand_map.items():
        prev_r = prev_map.get(rid) or {}
        strength = float(prev_r.get("strength_0_1") or 0.35)
        last_seen = float(prev_r.get("last_seen_epoch") or 0.0)
        applies_when = base.get("applies_when") if isinstance(base.get("applies_when"), dict) else {}

        matched = _matches(evidence, applies_when)
        if matched:
            strength = min(1.0, strength + 0.18)
            last_seen = float(now)
            if rid not in prev_map:
                changes["added"].append(rid)
            else:
                changes["strengthened"].append(rid)
        else:
            # decay slowly
            strength = max(0.0, strength - 0.12)
            changes["weakened"].append(rid)

        if strength >= 0.25:
            active.append(
                {
                    "id": rid,
                    "polarity": "caution",
                    "text": _cap(str(base.get("text") or ""), 160),
                    "applies_when": applies_when,
                    "strength_0_1": round(float(strength), 3),
                    "last_seen_epoch": float(last_seen),
                }
            )
        else:
            if rid in prev_map:
                changes["retired"].append(rid)

    # also retire prev rules that no longer appear in candidates (schema drift)
    for rid in list(prev_map.keys()):
        if rid not in cand_map:
            changes["retired"].append(rid)

    # stable sort: strong first
    active.sort(key=lambda r: float(r.get("strength_0_1") or 0.0), reverse=True)
    # cap
    active = active[:12]

    # simplify changes to counts for safety
    delta = {k: len(v) for k, v in changes.items()}
    return active, {"delta": delta, "evidence": evidence}


def _write_session(now: float, rules: list[dict[str, Any]], evidence: dict[str, Any]) -> Path:
    SESSIONS.mkdir(parents=True, exist_ok=True)
    path = SESSIONS / f"auto_experience_{int(now)}_boundary_induction.json"
    payload: dict[str, Any] = {
        "source": "boundary_induction",
        "title": "boundary_induction: self-set boundary candidates",
        "tags": ["boundary", "induction", "self_set"],
        "notes": _cap(
            f"rua={evidence.get('rua_dominant_mode')} yt={evidence.get('yt_compression_mode')} life={evidence.get('life_state')}",
            220,
        ),
        "timestamp": float(now),
        "where": {"platform": "windows", "layer": "boundary_induction"},
        "who": {"role": "agi", "mode": "unconscious", "origin": "rubit"},
        "boundaries": rules,
        "meta": {"evidence": evidence},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_boundary_induction(workspace_root: Path, *, cooldown_sec: int = 30 * 60) -> dict[str, Any]:
    now = time.time()
    safety = _get_safety_status()
    rest = _get_rest_status(now)
    st = _load_state()

    def _active_rules_from_state(state_obj: dict[str, Any]) -> list[dict[str, Any]]:
        return state_obj.get("active_rules") if isinstance(state_obj.get("active_rules"), list) else []

    def _emit_skip(reason: str, *, evidence: dict[str, Any] | None = None, active_rules: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        ar = active_rules if isinstance(active_rules, list) else _active_rules_from_state(st)
        res = {
            "ok": True,
            "skipped": True,
            "reason": reason,
            "timestamp_utc": _utc_iso(now),
            "safety": safety,
            "rest_gate": rest,
            "active_rules_count": len(ar),
            "delta": {},
            "evidence": evidence or {},
        }
        _atomic_write_json(OUT_LATEST, res)
        _append_jsonl(OUT_HISTORY, res)
        return res

    if safety in ("BLOCK", "REVIEW"):
        return _emit_skip(f"safety={safety}")
    if rest == "REST":
        return _emit_skip("rest_gate=REST")

    rules, evidence = _build_candidates(now)
    ev_sig = _evidence_sig(evidence)

    last = float(st.get("last_run_epoch") or 0.0)
    last_ev = str(st.get("last_evidence_sig") or "")
    evidence_changed = (ev_sig != last_ev) if ev_sig else False
    if (not evidence_changed) and float(cooldown_sec) > 0 and (now - last) < float(cooldown_sec):
        return _emit_skip("cooldown", evidence=evidence)

    if not rules:
        return _emit_skip("no_candidates", evidence=evidence)

    prev_active = st.get("active_rules") if isinstance(st.get("active_rules"), list) else []
    active_rules, meta = _update_active_rules(prev=prev_active, candidates=rules, evidence=evidence, now=now)

    # Only materialize when something actually changes meaningfully
    sig = _sha256_head(json.dumps({"active": active_rules, "meta": meta}, ensure_ascii=False))
    if st.get("last_sig") == sig:
        return _emit_skip("duplicate", evidence=meta.get("evidence") or evidence, active_rules=active_rules)

    session_path = _write_session(now, rules=active_rules, evidence=meta.get("evidence") or {})

    st_out = {
        "last_run_epoch": float(now),
        "last_sig": sig,
        "last_evidence_sig": ev_sig,
        "last_session_file": str(session_path),
        "active_rules": active_rules,
    }
    _save_state(st_out)

    res = {
        "ok": True,
        "timestamp_utc": _utc_iso(now),
        "safety": safety,
        "rest_gate": rest,
        "created_session_file": str(session_path),
        "active_rules_count": len(active_rules),
        "delta": meta.get("delta") or {},
        "evidence": meta.get("evidence") or {},
    }
    _atomic_write_json(OUT_LATEST, res)
    _append_jsonl(OUT_HISTORY, res)
    return res


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(WORKSPACE))
    ap.add_argument("--force", action="store_true", help="Ignore cooldown (manual verification).")
    args = ap.parse_args()

    cd = 0 if bool(args.force) else 30 * 60
    res = run_boundary_induction(Path(args.workspace).resolve(), cooldown_sec=int(cd))
    print(json.dumps({"ok": bool(res.get("ok")), "created": bool(res.get("created_session_file")), "reason": res.get("reason")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
