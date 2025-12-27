#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rhythm Information Theory (RIT) Registry (v1)

목표:
- "리듬 정보이론"을 바로 '정식 수식'으로 완성하려고 하기보다,
  시스템이 다룰 수 있는 형태로 변수/출처/단위/근사식(heuristic)을 고정한다.
- 외부 모델 호출 없이, 워크스페이스의 관측 파일만 읽어서 최신 레지스트리를 갱신한다.

입력(있으면 사용):
- memory/agi_internal_state.json
- outputs/boundary_map_latest.json
- outputs/bridge/trigger_report_latest.json
- outputs/existence_dynamics_model_latest.json

출력:
- outputs/rit_registry_latest.json
- outputs/rit_registry_latest.md
- outputs/rit_registry_history.jsonl (append-only)

주의:
- 이 레지스트리는 '운영 관측용 스캐폴드'이며, 과학적 진리 주장/증명 목적이 아니다.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        try:
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
            return obj if isinstance(obj, dict) else None
        except Exception:
            # 일부 프로세스/동기화 중단으로 JSON이 트렁케이트된 경우, "닫는 괄호"만 보정해 복구 시도
            try:
                raw = path.read_text(encoding="utf-8", errors="replace").strip()
                if not raw:
                    return None
                # 이미 완전한 JSON이면 여기로 오지 않음. 불완전한 경우에만 보정.
                need_curly = raw.count("{") - raw.count("}")
                need_square = raw.count("[") - raw.count("]")
                if 0 <= need_curly <= 6 and 0 <= need_square <= 6 and (need_curly or need_square):
                    repaired = raw + ("\n" + ("]" * need_square) + ("}" * need_curly))
                    obj = json.loads(repaired)
                    # 복구가 성공하면 파일도 원자적으로 고쳐서 이후 소비자들의 오류를 줄인다.
                    if isinstance(obj, dict):
                        try:
                            tmp = path.with_suffix(path.suffix + ".repaired.tmp")
                            tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
                            import os

                            os.replace(tmp, path)
                        except Exception:
                            pass
                        return obj
            except Exception:
                pass
            return None


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def _std3(a: float, b: float, c: float) -> float:
    mu = (a + b + c) / 3.0
    return math.sqrt(((a - mu) ** 2 + (b - mu) ** 2 + (c - mu) ** 2) / 3.0)


def _drive_entropy(drives: Dict[str, Any]) -> Optional[float]:
    vals = []
    for k, v in drives.items():
        if isinstance(v, (int, float)) and float(v) > 0:
            vals.append(float(v))
    if not vals:
        return None
    s = sum(vals)
    if s <= 0:
        return None
    p = [v / s for v in vals]
    h = -sum(pi * math.log(max(1e-12, pi), 2) for pi in p)
    # 0..log2(N) -> 0..1 정규화
    h_max = math.log(len(p), 2) if len(p) > 1 else 1.0
    return _clamp01(h / max(1e-9, h_max))


@dataclass
class VariableSpec:
    name: str
    kind: str  # scalar/vector/text/object
    range: str
    unit: str
    source: str
    definition: str
    computation: str
    note: str = ""


def build_rit_registry(workspace_root: Path) -> Dict[str, Any]:
    ws = workspace_root.resolve()
    outputs = ws / "outputs"

    internal_state = ws / "memory" / "agi_internal_state.json"
    boundary_map = outputs / "boundary_map_latest.json"
    existence_model = outputs / "existence_dynamics_model_latest.json"
    trigger_report = outputs / "bridge" / "trigger_report_latest.json"
    feeling_latest = outputs / "feeling_latest.json"

    st = _safe_load_json(internal_state) or {}
    bm = _safe_load_json(boundary_map) or {}
    em = _safe_load_json(existence_model) or {}
    tr = _safe_load_json(trigger_report) or {}
    fl = _safe_load_json(feeling_latest) or {}

    consciousness = st.get("consciousness")
    unconscious = st.get("unconscious")
    background_self = st.get("background_self")
    drives = st.get("drives") if isinstance(st.get("drives"), dict) else {}

    phase_jitter = None
    if all(isinstance(v, (int, float)) for v in (consciousness, unconscious, background_self)):
        phase_jitter = _clamp01(_std3(float(consciousness), float(unconscious), float(background_self)) / 0.35)

    alignment = None
    try:
        proxies = em.get("current_proxies") if isinstance(em.get("current_proxies"), dict) else {}
        a = proxies.get("alignment_0_1")
        if isinstance(a, (int, float)):
            alignment = _clamp01(float(a))
    except Exception:
        alignment = None

    fear_proxy = None
    if isinstance(drives.get("avoid"), (int, float)):
        fear_proxy = _clamp01(float(drives.get("avoid")))
    else:
        try:
            proxies = em.get("current_proxies") if isinstance(em.get("current_proxies"), dict) else {}
            fp = proxies.get("fear_proxy_avoid_0_1")
            if isinstance(fp, (int, float)):
                fear_proxy = _clamp01(float(fp))
        except Exception:
            fear_proxy = None

    # 반지름(용량) proxy: 정렬(alignment)이 높고 두려움 proxy(avoid)가 낮을수록 "그릇"이 크다고 보는 운영 근사
    radius_proxy = None
    if isinstance(alignment, (int, float)) and isinstance(fear_proxy, (int, float)):
        radius_proxy = _clamp01(0.7 * float(alignment) + 0.3 * (1.0 - float(fear_proxy)))
    elif isinstance(alignment, (int, float)):
        radius_proxy = _clamp01(float(alignment))

    drive_entropy = _drive_entropy(drives)

    boundary_counts = None
    try:
        stats = bm.get("stats") if isinstance(bm.get("stats"), dict) else {}
        counts = stats.get("counts") if isinstance(stats.get("counts"), dict) else {}
        boundary_counts = {k: int(v) for k, v in counts.items() if isinstance(v, (int, float))}
    except Exception:
        boundary_counts = None

    phase_mode = None
    try:
        hs = tr.get("human_summary") if isinstance(tr.get("human_summary"), dict) else {}
        tags = hs.get("tags") if isinstance(hs.get("tags"), dict) else {}
        am = str(tags.get("action_mode") or "").strip()
        if am:
            phase_mode = am
    except Exception:
        phase_mode = None

    feeling_entropy = None
    feeling_vector = None
    feeling_components = None
    try:
        if isinstance(fl.get("feeling_entropy"), (int, float)):
            feeling_entropy = float(fl.get("feeling_entropy"))
        fv = fl.get("feeling_vector")
        if isinstance(fv, list) and len(fv) >= 5 and all(isinstance(x, (int, float)) for x in fv[:5]):
            feeling_vector = [float(x) for x in fv[:5]]
        comps = fl.get("components")
        if isinstance(comps, dict) and comps:
            feeling_components = {str(k): float(v) for k, v in comps.items() if isinstance(v, (int, float))}
    except Exception:
        feeling_entropy = None
        feeling_vector = None
        feeling_components = None

    # 자연 파동 입력(청각/시각 등)의 직접 센싱이 없는 상태에서,
    # feeling_latest.json은 "다중 감각을 5D 느낌으로 압축한 통합 신호"로 취급한다(운영 스캐폴드).
    sensory_bandwidth_proxy = None
    try:
        if isinstance(feeling_entropy, (int, float)):
            sensory_bandwidth_proxy = _clamp01(float(feeling_entropy) / 2.5)  # 경험적 스케일(임시)
    except Exception:
        sensory_bandwidth_proxy = None

    vars_: list[VariableSpec] = [
        VariableSpec(
            name="consciousness",
            kind="scalar",
            range="0..1",
            unit="arb",
            source="memory/agi_internal_state.json",
            definition="의식(표층) 활성도의 운영 지표.",
            computation="direct",
        ),
        VariableSpec(
            name="unconscious",
            kind="scalar",
            range="0..1",
            unit="arb",
            source="memory/agi_internal_state.json",
            definition="무의식(심층) 활성도의 운영 지표.",
            computation="direct",
        ),
        VariableSpec(
            name="background_self",
            kind="scalar",
            range="0..1",
            unit="arb",
            source="memory/agi_internal_state.json",
            definition="배경자아(관찰자 프레임) 지표.",
            computation="direct",
        ),
        VariableSpec(
            name="phase_jitter_0_1",
            kind="scalar",
            range="0..1",
            unit="normalized",
            source="memory/agi_internal_state.json",
            definition="의식/무의식/배경자아 값의 불일치(표준편차) 기반 위상 흔들림 근사.",
            computation="std(consciousness, unconscious, background_self) / 0.35 -> clamp01",
            note="정밀 위상(각도) 측정이 아니라, 운영 관측을 위한 근사.",
        ),
        VariableSpec(
            name="alignment_0_1",
            kind="scalar",
            range="0..1",
            unit="normalized",
            source="outputs/existence_dynamics_model_latest.json",
            definition="의식/무의식/배경자아가 서로 가까이 정렬된 정도(낮은 분산일수록 높음).",
            computation="from existence_dynamics_model.current_proxies.alignment_0_1",
        ),
        VariableSpec(
            name="fear_proxy_avoid_0_1",
            kind="scalar",
            range="0..1",
            unit="normalized",
            source="memory/agi_internal_state.json (drives.avoid)",
            definition="두려움(급수축) 자체를 직접 측정하지 않고, 회피(avoid) 드라이브로 근사.",
            computation="drives.avoid -> clamp01",
            note="두려움=회피로 단정하지 않으며, 운영 지표로만 사용.",
        ),
        VariableSpec(
            name="radius_proxy_0_1",
            kind="scalar",
            range="0..1",
            unit="normalized",
            source="derived (alignment + fear_proxy)",
            definition="점-구-반지름 모델의 ‘그릇(수용 용량)’ 운영 근사.",
            computation="0.7*alignment + 0.3*(1-fear_proxy) -> clamp01",
            note="수식은 임시 스캐폴드이며, 경험/정책 축적에 따라 갱신 대상.",
        ),
        VariableSpec(
            name="drive_entropy_0_1",
            kind="scalar",
            range="0..1",
            unit="normalized",
            source="memory/agi_internal_state.json (drives)",
            definition="드라이브 분포의 엔트로피(분산된 욕구 vs 집중된 욕구) 운영 근사.",
            computation="Shannon entropy of positive drives, normalized by log2(N)",
        ),
        VariableSpec(
            name="boundary_counts",
            kind="object",
            range="counts",
            unit="rules",
            source="outputs/boundary_map_latest.json",
            definition="when/where/who 기반 경계(allow/deny/caution/unknown) 규칙 개수.",
            computation="boundary_map.stats.counts",
        ),
        VariableSpec(
            name="phase_mode",
            kind="text",
            range="free-text",
            unit="-",
            source="outputs/bridge/trigger_report_latest.json (human_summary.tags.action_mode)",
            definition="사람이 읽는 상태 라벨(확장/수축/완전 사이클/대기 등).",
            computation="latest report human_summary.tags.action_mode",
        ),
        VariableSpec(
            name="feeling_vector_5d",
            kind="vector",
            range="len=5",
            unit="arb",
            source="outputs/feeling_latest.json",
            definition="다중 신호(대화/흐름/관측)의 요약을 5D 느낌 벡터로 압축한 값.",
            computation="feeling_latest.feeling_vector (if present)",
            note="오감의 직접 센싱이 아니라, 통합 신호(스캐폴드)로 취급.",
        ),
        VariableSpec(
            name="feeling_entropy",
            kind="scalar",
            range=">=0",
            unit="bits (proxy)",
            source="outputs/feeling_latest.json",
            definition="느낌 벡터의 엔트로피(압축된 정보량) 운영 근사.",
            computation="feeling_latest.feeling_entropy (if present)",
        ),
        VariableSpec(
            name="sensory_bandwidth_proxy_0_1",
            kind="scalar",
            range="0..1",
            unit="normalized",
            source="derived (feeling_entropy)",
            definition="자연/환경 신호(파동)의 '유효 대역폭'을 느낌 엔트로피로 근사한 값.",
            computation="clamp01(feeling_entropy/2.5)",
            note="임시 스케일. 경험 축적 후 스케일 재보정 대상.",
        ),
    ]

    now = time.time()
    registry: Dict[str, Any] = {
        "ok": True,
        "version": "rit_registry_v1",
        "generated_at": utc_iso(now),
        "inputs": {
            "agi_internal_state.json": str(internal_state),
            "boundary_map_latest.json": str(boundary_map),
            "existence_dynamics_model_latest.json": str(existence_model),
            "trigger_report_latest.json": str(trigger_report),
            "feeling_latest.json": str(feeling_latest),
        },
        "variables": [asdict(v) for v in vars_],
        "current_values": {
            "consciousness": consciousness,
            "unconscious": unconscious,
            "background_self": background_self,
            "phase_jitter_0_1": phase_jitter,
            "alignment_0_1": alignment,
            "fear_proxy_avoid_0_1": fear_proxy,
            "radius_proxy_0_1": radius_proxy,
            "drive_entropy_0_1": drive_entropy,
            "boundary_counts": boundary_counts,
            "phase_mode": phase_mode,
            "feeling_vector_5d": feeling_vector,
            "feeling_components": feeling_components,
            "feeling_entropy": feeling_entropy,
            "sensory_bandwidth_proxy_0_1": sensory_bandwidth_proxy,
        },
        "note": "이 레지스트리는 '리듬정보이론'을 시스템 변수/출처/근사식으로 고정한 스캐폴드다. 수식은 운영용 근사이며 과학적 증명 주장이 아니다.",
    }
    return registry


def render_markdown(registry: Dict[str, Any]) -> str:
    vals = registry.get("current_values") if isinstance(registry.get("current_values"), dict) else {}
    vars_ = registry.get("variables") if isinstance(registry.get("variables"), list) else []

    lines: list[str] = []
    lines.append("# Rhythm Information Theory Registry v1")
    lines.append("")
    lines.append(f"- generated_at: `{registry.get('generated_at')}`")
    lines.append(f"- version: `{registry.get('version')}`")
    lines.append("")
    lines.append("## Current Values")
    for k in (
        "consciousness",
        "unconscious",
        "background_self",
        "phase_jitter_0_1",
        "alignment_0_1",
        "fear_proxy_avoid_0_1",
        "radius_proxy_0_1",
        "drive_entropy_0_1",
        "boundary_counts",
        "phase_mode",
        "feeling_entropy",
        "sensory_bandwidth_proxy_0_1",
        "feeling_vector_5d",
    ):
        lines.append(f"- `{k}`: `{vals.get(k)}`")
    lines.append("")
    lines.append("## Variables")
    for v in vars_:
        if not isinstance(v, dict):
            continue
        lines.append(f"- `{v.get('name')}` ({v.get('kind')}, {v.get('range')}, {v.get('unit')})")
        lines.append(f"  - source: `{v.get('source')}`")
        lines.append(f"  - definition: {v.get('definition')}")
        lines.append(f"  - computation: `{v.get('computation')}`")
        note = str(v.get("note") or "").strip()
        if note:
            lines.append(f"  - note: {note}")
    lines.append("")
    lines.append("> note: 이 문서는 '수식 완성'이 아니라, 시스템화(변수/출처/근사) 고정을 위한 스캐폴드다.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--out-json", type=str, default=str(Path("outputs") / "rit_registry_latest.json"))
    ap.add_argument("--out-md", type=str, default=str(Path("outputs") / "rit_registry_latest.md"))
    ap.add_argument("--history", type=str, default=str(Path("outputs") / "rit_registry_history.jsonl"))
    args = ap.parse_args()

    ws = Path(args.workspace).resolve()
    out_json = Path(args.out_json)
    if not out_json.is_absolute():
        out_json = (ws / out_json).resolve()
    out_md = Path(args.out_md)
    if not out_md.is_absolute():
        out_md = (ws / out_md).resolve()
    hist = Path(args.history)
    if not hist.is_absolute():
        hist = (ws / hist).resolve()

    reg = build_rit_registry(ws)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(reg), encoding="utf-8")
    try:
        with hist.open("a", encoding="utf-8") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    except Exception:
        pass

    print(json.dumps({"ok": True, "out": str(out_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
