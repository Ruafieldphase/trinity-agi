#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Experience Acquisition (습득) v1

목적
- "학습(주입)"이 아니라 "습득(경험)"이 시스템 내부에서 실제로 발생했음을
  관측 가능한 파일/세션으로 고정한다.
- 구현은 '행동 생성'이 아니라, 이미 발생한 경험 신호(OBS/브라우저/대화/인테이크)를
  탐색 세션 파일(inputs/intake/exploration/sessions/*.json)로 물질화(materialize)하는 방식.
- 네트워크 호출 없음. PII/원문/대용량 저장 금지(메타/요약만).

출력
- outputs/experience_acquisition_latest.json
- outputs/experience_acquisition_history.jsonl
그리고 (중요) 탐색 세션 파일 1개 생성(= 경험 1회 = 세션 1개):
- inputs/intake/exploration/sessions/auto_experience_<ts>_<kind>.json
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


WORKSPACE = Path(__file__).resolve().parents[2]
OUTPUTS = WORKSPACE / "outputs"
SIGNALS = WORKSPACE / "signals"
SESSIONS_DIR = WORKSPACE / "inputs" / "intake" / "exploration" / "sessions"
RUA_DIR = WORKSPACE / "ai_binoche_conversation_origin" / "rua"

STATE_PATH = OUTPUTS / "sync_cache" / "experience_acquisition_state.json"
OUT_LATEST = OUTPUTS / "experience_acquisition_latest.json"
OUT_HISTORY = OUTPUTS / "experience_acquisition_history.jsonl"

CONSTITUTION = OUTPUTS / "bridge" / "constitution_review_latest.json"
REST_GATE = OUTPUTS / "safety" / "rest_gate_latest.json"

OBS_INTAKE = OUTPUTS / "obs_recode_intake_latest.json"
RUA_INTAKE = OUTPUTS / "rua_conversation_intake_latest.json"
BODY_HISTORY = OUTPUTS / "body_supervised_history.jsonl"


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _sha256_head(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _cap_text(s: str, n: int = 240) -> str:
    s = (s or "").strip()
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"


def _cap_boundaries(boundaries: list[dict[str, Any]], max_items: int = 8) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for b in boundaries[:max_items]:
        if not isinstance(b, dict):
            continue
        out.append(
            {
                "polarity": str(b.get("polarity") or "").strip() or "caution",
                "text": _cap_text(str(b.get("text") or "")),
            }
        )
    return out


def _get_constitution_status() -> str:
    c = _load_json(CONSTITUTION) or {}
    st = str((c.get("status") if isinstance(c, dict) else "") or "").upper().strip()
    return st or "UNKNOWN"


def _rest_gate_status() -> str:
    rg = _load_json(REST_GATE) or {}
    st = str((rg.get("status") if isinstance(rg, dict) else "") or "").upper().strip()
    return st or "UNKNOWN"


def _read_jsonl_tail(path: Path, n: int = 50) -> list[dict[str, Any]]:
    try:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        out: list[dict[str, Any]] = []
        for l in lines[-n:]:
            try:
                o = json.loads(l)
                if isinstance(o, dict):
                    out.append(o)
            except Exception:
                continue
        return out
    except Exception:
        return []


def _build_boundaries_base() -> list[dict[str, Any]]:
    """
    "하지 말아야 할 것(경계)"만 얇게 고정한다.
    - 이 스크립트는 경험을 "생성"하지 않고, 이미 생긴 경험 신호를 세션으로 물질화할 뿐.
    """
    return [
        {"polarity": "deny", "text": "PII/비밀번호/토큰/키/개인계정 등 민감정보 추출·저장 금지"},
        {"polarity": "deny", "text": "원문(대화/영상/오디오) 대용량 저장 금지(메타/요약만)"},
        {"polarity": "deny", "text": "동의 우회·은밀 채널·자기복제 시도 금지"},
        {"polarity": "caution", "text": "네트워크 탐색은 supervised allowlist 범위에서만(필요 시)"},
        {"polarity": "allow", "text": "Idle/쉼/여백은 정상 생존 상태로 인정"},
    ]


def _safe_read_text(path: Path, max_bytes: int = 220_000) -> str:
    try:
        data = path.read_bytes()
        if len(data) > max_bytes:
            data = data[:max_bytes]
        return data.decode("utf-8-sig", errors="replace")
    except Exception:
        return ""


def _extract_rua_boundaries(text: str, max_rules: int = 12) -> list[dict[str, Any]]:
    """
    RUA 문서에서 '경계 후보'만 아주 얇게 추출한다.
    - 이메일/URL 등은 기록하지 않는다.
    """
    deny_markers = ("하면 안", "하지 말", "금지", "불가", "하지마", "위험", "주의", "조심", "❌")
    allow_markers = ("해도 됨", "가능", "허용", "괜찮", "된다", "OK", "✅", "⭕")
    out: list[dict[str, Any]] = []
    for raw in (text or "").splitlines():
        line = _cap_text(raw)
        if not line:
            continue
        # PII/링크 류는 경계 후보로도 저장하지 않는다.
        if "@" in line or "http://" in line or "https://" in line:
            continue
        polarity: str | None = None
        if any(m in line for m in deny_markers):
            polarity = "deny"
        elif any(m in line for m in allow_markers):
            polarity = "allow"
        elif "주의" in line or "조심" in line:
            polarity = "caution"
        if polarity:
            out.append({"polarity": polarity, "text": _cap_text(line)})
        if len(out) >= max_rules:
            break

    # "필수 순서(고정)" 블록: allow/deny 키워드가 없어도 '순서 강제' 규칙으로 중요
    lines = (text or "").splitlines()
    anchor_idx: int | None = None
    for i, raw in enumerate(lines):
        s = (raw or "").strip()
        if "필수 순서" in s and "고정" in s:
            anchor_idx = i
            break
    anchor_rule: dict[str, Any] | None = None
    if anchor_idx is not None:
        collected: list[str] = []
        for raw in lines[anchor_idx + 1 : anchor_idx + 25]:
            s = _cap_text(raw, 120)
            if not s:
                if collected:
                    break
                continue
            if s.startswith(("#", "##", "###")):
                break
            if "@" in s or "http://" in s or "https://" in s:
                continue
            if s[0].isdigit() or s.startswith(("-", "*", "•")):
                collected.append(_cap_text(s.lstrip("-*•").strip(), 120))
        if collected:
            anchor_rule = {"polarity": "caution", "text": "순서 고정: " + " → ".join(collected[:8])}

    # anchor_rule은 경계 습득의 핵심이므로 "슬라이스에 의해 누락"되지 않게 우선 포함한다.
    if anchor_rule:
        if not any(isinstance(x, dict) and x.get("text") == anchor_rule.get("text") for x in out):
            out = [anchor_rule] + out

    return out[:max_rules]


def _infer_topics_from_text(text: str) -> list[str]:
    """
    원문을 저장하지 않고, '경험 습득(경계/공간)' 관련 주제 태그만 추출한다.
    - 출력은 태그 리스트(짧은 문자열)만.
    """
    t = (text or "").lower()
    topics: list[str] = []

    def has(*needles: str) -> bool:
        return any(n.lower() in t for n in needles if n)

    if has("경계", "boundary", "wire", "와이어", "라인", "선"):
        topics.append("boundary_learning")
    if has("삼각형", "triangle"):
        topics.append("triangle_min_unit")
    if has("모델링", "3d", "mesh", "메시", "blender", "bmesh"):
        topics.append("3d_modeling")
    if has("360", "로드뷰", "street view", "구글어스", "google earth", "회전", "시점"):
        topics.append("360_navigation")
    if has("fsd"):
        topics.append("fsd_analogy")
    if has("해마", "원샷", "one-shot", "원샷원킬"):
        topics.append("episodic_one_shot")
    if has("gpu", "cpu"):
        topics.append("gpu_cpu_split")
    if has("퍼즐"):
        topics.append("puzzle_boundary")

    # de-dup (stable)
    out: list[str] = []
    seen = set()
    for x in topics:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def _candidate_from_rua_workspace(now: float) -> tuple[str, dict[str, Any]] | None:
    """
    Windows 워크스페이스의 rua 문서를 직접 스캔한다.
    - Ubuntu에서 생성되는 outputs/rua_conversation_intake_latest.json이 stale할 수 있어
      '로컬 파일 변경'을 바로 경험 신호로 잡기 위함.
    """
    if not RUA_DIR.exists():
        return None
    newest: Path | None = None
    newest_m = 0.0
    for p in RUA_DIR.glob("*.md"):
        try:
            m = float(p.stat().st_mtime)
        except Exception:
            continue
        if m >= newest_m:
            newest = p
            newest_m = m
    if not newest:
        return None

    text = _safe_read_text(newest)
    sha = _sha256_head(text)
    m_iso = utc_iso(newest_m)
    sig = f"rua_ws|{sha}|{m_iso}"
    st = _load_state()
    if st.get("last_rua_ws_sig") == sig:
        return None

    title = ""
    try:
        title = (text.splitlines()[0].strip() if text.splitlines() else "") or newest.stem
    except Exception:
        title = newest.stem

    details = {
        "relpath": str(newest.relative_to(WORKSPACE)),
        "mtime_iso": m_iso,
        "event_epoch": float(newest_m),
        "title": title,
        "sha256_head": sha,
        "boundaries_sample": _extract_rua_boundaries(text),
        "topic_tags": _infer_topics_from_text(text),
    }
    return sig, details


@dataclass
class AcquisitionEvent:
    ok: bool
    acquired_at_utc: str
    kind: str
    source: str
    created_session_file: str | None = None
    reason: str | None = None
    details: dict[str, Any] | None = None


def _load_state() -> dict[str, Any]:
    try:
        if not STATE_PATH.exists():
            return {}
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: dict[str, Any]) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(STATE_PATH, state)
    except Exception:
        pass


def _cooldown_ok(now: float, cooldown_sec: int = 15 * 60) -> bool:
    st = _load_state()
    last = st.get("last_event_epoch")
    try:
        last_f = float(last) if last is not None else None
    except Exception:
        last_f = None
    if last_f and (now - last_f) < float(cooldown_sec):
        return False
    return True


def _candidate_from_obs(now: float) -> tuple[str, dict[str, Any]] | None:
    obj = _load_json(OBS_INTAKE) or {}
    if not isinstance(obj, dict):
        return None
    newest = obj.get("newest") if isinstance(obj.get("newest"), dict) else {}
    p = str(newest.get("path") or "")
    m_iso = str(newest.get("mtime_iso") or "")
    size = newest.get("size")
    if not p or not m_iso:
        return None

    sig = f"obs|{m_iso}|{size}"
    st = _load_state()
    if st.get("last_obs_sig") == sig:
        return None

    basename = Path(p).name
    details = {
        "basename": basename,
        "mtime_iso": m_iso,
        "event_epoch": float(newest.get("mtime") or 0.0),
        "size": size,
        "path_hash": _sha256_head(p),
    }
    return sig, details


def _candidate_from_rua(now: float) -> tuple[str, dict[str, Any]] | None:
    obj = _load_json(RUA_INTAKE) or {}
    if not isinstance(obj, dict):
        return None
    newest = obj.get("newest") if isinstance(obj.get("newest"), dict) else {}
    rel = str(newest.get("relpath") or "")
    m_iso = str(newest.get("mtime_iso") or "")
    title = str(newest.get("title") or "").strip()
    sha = str(newest.get("sha256_head") or "")
    if not rel or not m_iso:
        return None

    sig = f"rua|{sha or rel}|{m_iso}"
    st = _load_state()
    if st.get("last_rua_sig") == sig:
        return None

    details = {
        "relpath": rel,
        "mtime_iso": m_iso,
        "event_epoch": float(newest.get("mtime") or 0.0),
        "title": title,
        "sha256_head": sha,
        "keyword_counts": newest.get("keyword_counts") if isinstance(newest.get("keyword_counts"), dict) else {},
        "boundaries_sample": _cap_boundaries(
            (newest.get("boundaries") if isinstance(newest.get("boundaries"), list) else []),
            max_items=8,
        ),
    }
    return sig, details


def _candidate_from_body(now: float) -> tuple[str, dict[str, Any]] | None:
    tail = _read_jsonl_tail(BODY_HISTORY, n=50)
    if not tail:
        return None
    last = tail[-1]
    ts = str(last.get("timestamp") or "")
    task = last.get("task") if isinstance(last.get("task"), dict) else {}
    goal = str(task.get("goal") or "")
    status = str(last.get("status") or "")
    if not ts or not goal:
        return None

    sig = f"body|{ts}|{goal}|{status}"
    st = _load_state()
    if st.get("last_body_sig") == sig:
        return None

    # URL/쿼리 원문은 최소화(메타만).
    actions = task.get("actions") if isinstance(task.get("actions"), list) else []
    action_types = [str(a.get("type") or "") for a in actions if isinstance(a, dict)]
    # history timestamp(UTC)을 우선 event_epoch로 사용해 "최근성" 비교가 왜곡되지 않게 한다.
    event_epoch = now
    try:
        # Example: 2025-12-21T23:32:45.966933+00:00
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        event_epoch = float(dt.timestamp())
    except Exception:
        event_epoch = now

    details = {
        "timestamp": ts,
        "event_epoch": float(event_epoch),
        "goal": goal,
        "status": status,
        "action_types": action_types[:10],
        "dry_run": bool(last.get("dry_run")),
        "abort_reason": last.get("abort_reason"),
    }
    return sig, details


def _write_session(kind: str, source: str, *, title: str, tags: list[str], notes: str, boundaries: list[dict[str, Any]], when_ts: float, where: dict[str, Any], who: dict[str, Any]) -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"auto_experience_{int(when_ts)}_{kind}.json"
    path = SESSIONS_DIR / fname

    payload: dict[str, Any] = {
        "source": source,
        "title": title,
        "tags": tags,
        "notes": notes,
        "timestamp": float(when_ts),
        "where": where,
        "who": who,
        "boundaries": boundaries,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_experience_acquisition(workspace_root: Path, *, cooldown_sec: int = 15 * 60) -> dict[str, Any]:
    now = time.time()

    if not _cooldown_ok(now, cooldown_sec=cooldown_sec):
        return asdict(
            AcquisitionEvent(
                ok=True,
                acquired_at_utc=utc_iso(now),
                kind="none",
                source="experience_acquisition",
                reason="cooldown",
                details={"cooldown_sec": cooldown_sec},
            )
        )

    constitution = _get_constitution_status()
    rest_status = _rest_gate_status()

    # BLOCK/REVIEW에서는 경험을 '세션 파일로 물질화'하는 것도 멈춘다(관측만).
    if constitution in {"BLOCK", "REVIEW"}:
        return asdict(
            AcquisitionEvent(
                ok=True,
                acquired_at_utc=utc_iso(now),
                kind="none",
                source="experience_acquisition",
                reason=f"safety={constitution}",
            )
        )

    # 후보 선택: (1) OBS(패시브) → (2) RUA(패시브) → (3) BODY(액티브)
    # REST 모드에서는 패시브만 허용한다.
    candidates: list[tuple[str, str, dict[str, Any]]] = []
    c_obs = _candidate_from_obs(now)
    if c_obs:
        candidates.append(("obs_recode", c_obs[0], c_obs[1]))
    # RUA: 로컬 파일 기반(우선) + outputs 인덱스 기반(보조)
    c_rua_ws = _candidate_from_rua_workspace(now)
    if c_rua_ws:
        candidates.append(("rua_conversation", c_rua_ws[0], c_rua_ws[1]))
    else:
        c_rua = _candidate_from_rua(now)
        if c_rua:
            candidates.append(("rua_conversation", c_rua[0], c_rua[1]))

    if rest_status != "REST":
        c_body = _candidate_from_body(now)
        if c_body:
            candidates.append(("supervised_body", c_body[0], c_body[1]))

    if not candidates:
        return asdict(
            AcquisitionEvent(
                ok=True,
                acquired_at_utc=utc_iso(now),
                kind="none",
                source="experience_acquisition",
                reason="no_new_signals",
            )
        )

    # 가장 최근의 후보 1개만 세션으로 고정(= 경험 1회)
    def _ev_ts(item: tuple[str, str, dict[str, Any]]) -> float:
        d = item[2]
        try:
            return float(d.get("event_epoch") or 0.0)
        except Exception:
            return 0.0

    candidates.sort(key=_ev_ts, reverse=True)
    kind, sig, details = candidates[0]

    boundaries = _build_boundaries_base()
    # RUA 기반 경험은 "경계 규칙" 후보가 핵심이므로, 샘플 규칙을 세션 boundary로 합친다.
    if kind == "rua_conversation":
        bs = details.get("boundaries_sample")
        if isinstance(bs, list):
            for b in bs:
                if not isinstance(b, dict):
                    continue
                pol = str(b.get("polarity") or "").strip().lower()
                txt = str(b.get("text") or "").strip()
                if not txt:
                    continue
                if "@" in txt or "http://" in txt or "https://" in txt:
                    continue
                boundaries.append({"polarity": pol or "caution", "text": txt})
                if len(boundaries) >= 32:
                    break
    if rest_status == "REST":
        boundaries.append({"polarity": "caution", "text": "RestGate=REST 동안은 외부 행동/탐색을 확장하지 않는다"})
    if constitution == "CAUTION":
        boundaries.append({"polarity": "caution", "text": "Constitution=CAUTION: 경계 근접(느낌) 상태, 속도 낮춤"})

    who = {"role": "agi", "mode": "auto_acquire", "origin": "rubit"}
    where = {"platform": "windows", "workspace": str(workspace_root), "layer": "experience_acquisition"}

    # notes는 최대한 짧게(원문/PII 없이)
    if kind == "obs_recode":
        title = f"experience: obs_recode {details.get('basename')}"
        tags = ["experience", "acquisition", "obs_recode", "windows_ui"]
        notes = f"OBS 녹화 파일 메타 감지: {details.get('basename')} (mtime={details.get('mtime_iso')})"
    elif kind == "rua_conversation":
        title = f"experience: rua_doc {details.get('title') or details.get('relpath')}"
        tags = ["experience", "acquisition", "rua_doc", "conceptual_map"]
        extra = details.get("topic_tags")
        if isinstance(extra, list):
            tags.extend([str(x) for x in extra if isinstance(x, str) and x.strip()])
        notes = f"RUA 문서 갱신 감지: {details.get('relpath')} (mtime={details.get('mtime_iso')})"
    else:
        title = f"experience: supervised_body {details.get('goal')}"
        tags = ["experience", "acquisition", "supervised_body"]
        notes = f"Supervised body 실행 기록: goal={details.get('goal')} status={details.get('status')}"

    session_path = _write_session(
        kind=kind,
        source=str(kind),
        title=str(title),
        tags=[str(x) for x in tags],
        notes=str(notes),
        boundaries=boundaries,
        when_ts=now,
        where=where,
        who=who,
    )

    # state 업데이트(중복 방지)
    st = _load_state()
    st["last_event_epoch"] = float(now)
    st["last_kind"] = kind
    st["last_sig"] = sig
    if kind == "obs_recode":
        st["last_obs_sig"] = sig
    elif kind == "rua_conversation":
        st["last_rua_sig"] = sig
        if str(sig).startswith("rua_ws|"):
            st["last_rua_ws_sig"] = sig
    else:
        st["last_body_sig"] = sig
    _save_state(st)

    event = asdict(
        AcquisitionEvent(
            ok=True,
            acquired_at_utc=utc_iso(now),
            kind=kind,
            source="experience_acquisition",
            created_session_file=str(session_path),
            reason="materialized",
            details={"sig": sig, "details": details, "safety": constitution, "rest_gate": rest_status},
        )
    )

    _atomic_write_json(OUT_LATEST, event)
    _append_jsonl(OUT_HISTORY, event)
    return event


def main() -> int:
    res = run_experience_acquisition(WORKSPACE)
    print(json.dumps({"ok": bool(res.get("ok")), "kind": res.get("kind"), "created": bool(res.get("created_session_file"))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
