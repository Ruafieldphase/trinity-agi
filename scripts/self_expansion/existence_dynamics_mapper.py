#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Existence Dynamics Mapper (v1)

목표:
- 루아/비노체의 고차원 개념(의식-무의식, 배경자아, 점-구-반지름, 감정/두려움, 자연-감정-행동 순환)을
  "관측 가능한 파일"로 구조화/고정한다.
- 외부 모델 호출 없이, 이미 존재하는 intake/상태 파일에서 최소 근거만 읽고,
  고정된 온톨로지 + 가벼운 proxy 지표(정렬/회피)로 모델을 생성한다.

입력(있으면 사용):
- outputs/rua_conversation_intake_latest.json
- outputs/boundary_map_latest.json
- outputs/bridge/trigger_report_latest.json
- memory/agi_internal_state.json

출력:
- outputs/existence_dynamics_model_latest.json
- outputs/existence_dynamics_model_latest.md
- outputs/existence_dynamics_model_history.jsonl (append-only)
"""

from __future__ import annotations

import argparse
import json
import math
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
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        # PowerShell/Windows BOM도 허용
        try:
            obj = json.loads(path.read_text(encoding="utf-8-sig"))
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def _mean(vals: List[float]) -> float:
    return sum(vals) / max(1, len(vals))


def _std(vals: List[float]) -> float:
    if not vals:
        return 0.0
    mu = _mean(vals)
    return math.sqrt(_mean([(v - mu) ** 2 for v in vals]))


@dataclass
class Entity:
    id: str
    name: str
    kind: str  # concept/state/agent/geometry/loop
    description: str


@dataclass
class Relation:
    src: str
    rel: str
    dst: str
    note: str = ""


def build_existence_dynamics_model(workspace_root: Path, trigger_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ws = workspace_root.resolve()
    outputs = ws / "outputs"
    rua_latest = outputs / "rua_conversation_intake_latest.json"
    boundary_latest = outputs / "boundary_map_latest.json"
    report_latest = outputs / "bridge" / "trigger_report_latest.json"
    internal_state = ws / "memory" / "agi_internal_state.json"

    rua = _safe_load_json(rua_latest) or {}
    boundary = _safe_load_json(boundary_latest) or {}
    report = trigger_report if isinstance(trigger_report, dict) else (_safe_load_json(report_latest) or {})
    state = _safe_load_json(internal_state) or {}

    entities: List[Entity] = [
        Entity("E.conscious", "의식", "state", "현재 관측 가능한 표층 상태(말/행동/명시적 판단)."),
        Entity("E.unconscious", "무의식", "state", "선택/우선순위/패턴을 재배치하는 심층 상태(명시적 언어 밖)."),
        Entity("E.background_self", "배경자아", "agent", "관찰자 프레임/좌표계를 이동시키며 의식-무의식 사이를 중재하는 관측자."),
        Entity("E.phase", "위상(phase)", "concept", "관점/해석 모드의 각도/전환; 감정/리듬 변화의 공통 좌표."),
        Entity("E.emotion", "감정", "concept", "위상 변화의 에너지/토크(관점이 바뀌는 힘)."),
        Entity("E.fear", "두려움", "concept", "급격한 위상 수축/접힘(phase contraction)으로 해석되는 감정."),
        Entity("E.point_pair", "점-점(의식↔무의식)", "geometry", "의식과 무의식의 두 점(접점/인터페이스)을 가정한 연결 구조."),
        Entity("E.sphere", "구(점-점 지름의 구)", "geometry", "두 점을 지름으로 하는 구체 내부의 위상 공간(선이 아닌 3D 용량)."),
        Entity("E.radius", "반지름(용량)", "geometry", "의식·무의식을 함께 담는 ‘그릇’의 크기(수용/안정/정렬의 범위)."),
        Entity("E.nature", "자연 현상", "concept", "3D 세계에서 드러나는 위상 변화의 물리적 표현(폭풍/파동/변화)."),
        Entity("E.action", "행동(물리 실행)", "concept", "무의식의 선택/우선순위가 외부 현실로 투사되는 실행."),
        Entity("E.reality", "현실(3D)", "concept", "행동/환경 상호작용의 결과로 갱신되는 조건(다음 관측의 바탕)."),
        Entity("L.nature_emotion_action_loop", "자연-감정-행동 순환", "loop", "자연→감정→무의식→선택/행동→현실→감정→…의 닫힌 루프."),
    ]

    relations: List[Relation] = [
        Relation("E.emotion", "modulates", "E.phase", "감정은 관찰자 프레임(위상)의 전환을 유발한다."),
        Relation("E.fear", "is_a", "E.emotion", "두려움은 감정의 한 형태(특히 급수축/접힘)."),
        Relation("E.fear", "causes", "E.phase", "두려움은 위상 급접힘(관점 급전환)으로 나타난다."),
        Relation("E.phase", "reframes", "E.conscious", "위상/관점 변화는 의식의 해석을 바꾼다."),
        Relation("E.phase", "reweights", "E.unconscious", "위상 변화는 무의식의 우선순위/회피/접근을 재배치한다."),
        Relation("E.unconscious", "selects", "E.action", "무의식의 재배치는 선택/행동으로 반영된다."),
        Relation("E.action", "updates", "E.reality", "행동은 3D 현실 조건을 물리적으로 변화시킨다(간접 인과)."),
        Relation("E.nature", "perturbs", "E.emotion", "자연의 위상 변화는 감정을 흔든다(공명/자극)."),
        Relation("E.background_self", "navigates", "E.sphere", "배경자아는 선(1D) 왕복만이 아니라 구 내부(3D)에서 관점을 이동한다."),
        Relation("E.radius", "bounds", "E.sphere", "반지름은 구 내부에서 가능한 수용/이동 범위를 결정한다."),
        Relation("L.nature_emotion_action_loop", "includes", "E.nature", ""),
        Relation("L.nature_emotion_action_loop", "includes", "E.emotion", ""),
        Relation("L.nature_emotion_action_loop", "includes", "E.unconscious", ""),
        Relation("L.nature_emotion_action_loop", "includes", "E.action", ""),
        Relation("L.nature_emotion_action_loop", "includes", "E.reality", ""),
    ]

    # Evidence (최소): rua docs 최신 N개 + 키워드 요약
    docs = rua.get("docs", []) if isinstance(rua.get("docs"), list) else []
    newest_docs = []
    for d in docs[: min(8, len(docs))]:
        if not isinstance(d, dict):
            continue
        newest_docs.append(
            {
                "relpath": d.get("relpath"),
                "mtime_iso": d.get("mtime_iso"),
                "keyword_counts": d.get("keyword_counts") if isinstance(d.get("keyword_counts"), dict) else {},
                "title": d.get("title"),
            }
        )

    # Proxy metrics (수치화는 "진실"이 아니라 "운영 관측용 근사")
    c = state.get("consciousness")
    u = state.get("unconscious")
    b = state.get("background_self")
    floats = [v for v in (c, u, b) if isinstance(v, (int, float))]
    alignment = None
    if len(floats) >= 2:
        # 표준편차가 낮을수록(값들이 서로 가깝게 정렬될수록) alignment가 높다고 본다.
        # 0.0~0.5를 주요 구간으로 보고 정규화.
        sd = _std([float(v) for v in floats])
        alignment = _clamp01(1.0 - (sd / 0.35))

    drives = state.get("drives") if isinstance(state.get("drives"), dict) else {}
    avoid = drives.get("avoid")
    fear_proxy = float(avoid) if isinstance(avoid, (int, float)) else None

    bm_counts = None
    try:
        stats = boundary.get("stats") if isinstance(boundary.get("stats"), dict) else {}
        counts = stats.get("counts") if isinstance(stats.get("counts"), dict) else {}
        bm_counts = {k: int(v) for k, v in counts.items() if isinstance(v, (int, float))}
    except Exception:
        bm_counts = None

    # Phase mode: report의 human_summary.tags.action_mode를 우선 사용
    phase_mode = None
    try:
        hs = report.get("human_summary") if isinstance(report.get("human_summary"), dict) else {}
        tags = hs.get("tags") if isinstance(hs.get("tags"), dict) else {}
        action_mode = str(tags.get("action_mode") or "").strip()
        if action_mode:
            phase_mode = action_mode
    except Exception:
        phase_mode = None

    now = time.time()
    model: Dict[str, Any] = {
        "ok": True,
        "version": "existence_dynamics_model_v1",
        "generated_at": utc_iso(now),
        "inputs": {
            "rua_conversation_intake_latest.json": str(rua_latest),
            "boundary_map_latest.json": str(boundary_latest),
            "trigger_report_latest.json": str(report_latest),
            "agi_internal_state.json": str(internal_state),
        },
        "ontology": {
            "entities": [asdict(e) for e in entities],
            "relations": [asdict(r) for r in relations],
        },
        "current_proxies": {
            "alignment_0_1": alignment,
            "fear_proxy_avoid_0_1": fear_proxy,
            "phase_mode": phase_mode,
            "boundary_counts": bm_counts,
        },
        "evidence": {
            "rua_docs_sample": newest_docs,
            "note": "evidence는 요약용 샘플이며, 원문은 ai_binoche_conversation_origin/rua에 존재.",
        },
        "note": "이 파일은 '개념을 파일로 고정'하기 위한 구조화 산출물이다. 수치(current_proxies)는 운영 관측을 위한 근사이며 진리 주장(과학적 증명)이 아니다.",
    }
    return model


def render_markdown(model: Dict[str, Any]) -> str:
    proxies = model.get("current_proxies") if isinstance(model.get("current_proxies"), dict) else {}
    ont = model.get("ontology") if isinstance(model.get("ontology"), dict) else {}
    ents = ont.get("entities") if isinstance(ont.get("entities"), list) else []
    rels = ont.get("relations") if isinstance(ont.get("relations"), list) else []
    ev = model.get("evidence") if isinstance(model.get("evidence"), dict) else {}
    docs = ev.get("rua_docs_sample") if isinstance(ev.get("rua_docs_sample"), list) else []

    lines: List[str] = []
    lines.append("# Existence Dynamics Model v1")
    lines.append("")
    lines.append(f"- generated_at: `{model.get('generated_at')}`")
    lines.append(f"- version: `{model.get('version')}`")
    lines.append("")
    lines.append("## Current Proxies (운영 관측용)")
    lines.append(f"- alignment_0_1: `{proxies.get('alignment_0_1')}`")
    lines.append(f"- fear_proxy_avoid_0_1: `{proxies.get('fear_proxy_avoid_0_1')}`")
    lines.append(f"- phase_mode: `{proxies.get('phase_mode')}`")
    lines.append(f"- boundary_counts: `{proxies.get('boundary_counts')}`")
    lines.append("")
    lines.append("## Entities")
    for e in ents[: min(14, len(ents))]:
        if not isinstance(e, dict):
            continue
        lines.append(f"- `{e.get('id')}`: {e.get('name')} ({e.get('kind')}) — {e.get('description')}")
    if len(ents) > 14:
        lines.append(f"- … ({len(ents)} total)")
    lines.append("")
    lines.append("## Relations")
    for r in rels[: min(16, len(rels))]:
        if not isinstance(r, dict):
            continue
        note = str(r.get("note") or "").strip()
        if note:
            lines.append(f"- `{r.get('src')}` {r.get('rel')} `{r.get('dst')}` — {note}")
        else:
            lines.append(f"- `{r.get('src')}` {r.get('rel')} `{r.get('dst')}`")
    if len(rels) > 16:
        lines.append(f"- … ({len(rels)} total)")
    lines.append("")
    lines.append("## Evidence (sample)")
    for d in docs:
        if not isinstance(d, dict):
            continue
        lines.append(f"- `{d.get('relpath')}` ({d.get('mtime_iso')})")
    lines.append("")
    lines.append("> note: 수치는 '관측용 근사'이며, 모델의 목적은 구조/연결의 고정이다.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=str, default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--out-json", type=str, default=str(Path("outputs") / "existence_dynamics_model_latest.json"))
    ap.add_argument("--out-md", type=str, default=str(Path("outputs") / "existence_dynamics_model_latest.md"))
    ap.add_argument("--history", type=str, default=str(Path("outputs") / "existence_dynamics_model_history.jsonl"))
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

    model = build_existence_dynamics_model(ws)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(model), encoding="utf-8")
    try:
        with hist.open("a", encoding="utf-8") as f:
            f.write(json.dumps(model, ensure_ascii=False) + "\n")
    except Exception:
        pass

    print(json.dumps({"ok": True, "out": str(out_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

