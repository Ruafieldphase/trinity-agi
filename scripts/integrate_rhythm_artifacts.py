#!/usr/bin/env python3
"""
🔄 Rhythm Artifact Integrator

목적:
  - 최근 생성된 groove 프로파일 (`outputs/groove_profile_latest.json`)
  - Flow Observer 리포트 (`outputs/flow_observer_report_latest.json`)
  - Rhythm Audio Signature 메타데이터 (`outputs/rhythm_signature_metadata_*.json`)
를 통합 분석하여 작업 리듬 · 집중 세션 · 마이크로타이밍에 대한 권장 조정안을 산출한다.

출력:
  JSON: `outputs/rhythm_groove_flow_correlation.json`
  MD  : `outputs/rhythm_groove_flow_correlation.md`

설계 노트:
  - 외부 라이브러리 미사용 (순수 표준 라이브러리)
  - 결측 데이터가 많은 경우 안전한 기본값을 유지하고 "insufficient_data" 태그 부여
  - 향후 확장: 추가 생리/환경 센서(마이크, 시야 추적) 연계 가능
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = WORKSPACE_ROOT / "outputs"


# --------------------------- Data Classes ---------------------------
@dataclass
class IntegratedRhythmProfile:
    generated_at: str
    groove_source: Optional[Dict[str, Any]]
    flow_source: Optional[Dict[str, Any]]
    rhythm_metadata: Optional[Dict[str, Any]]
    focus_block_minutes: int
    break_block_minutes: int
    microtiming_adjust_ms: float
    swing_adjust: float
    energy_state: str
    confidence: float
    recommendations: List[str]
    notes: List[str]
    tags: List[str]
    # New fields
    recommended_presets: Dict[str, Any]
    flow_density: Optional[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------- Loaders ---------------------------
def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def find_latest_rhythm_metadata() -> Optional[Dict[str, Any]]:
    if not OUTPUT_DIR.exists():
        return None
    meta_files = sorted(OUTPUT_DIR.glob("rhythm_signature_metadata_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not meta_files:
        return None
    return load_json(meta_files[0])


# --------------------------- Core Computations ---------------------------
def derive_focus_blocks(flow: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not flow:
        return {
            "focus_block_minutes": 50,
            "break_block_minutes": 10,
            "confidence": 0.15,
            "energy_state": "unknown",
            "notes": ["flow_observer_report_latest.json 없음 → 기본 포커스/휴식 블록 사용"],
            "tags": ["insufficient_data", "default_blocks"],
        }
    summary = flow.get("activity_summary", {})
    flow_minutes = float(summary.get("total_flow_minutes", 0.0))
    sessions = int(summary.get("flow_sessions", 0)) or 1
    avg_session = flow_minutes / sessions
    interruptions = int(summary.get("interruptions", 0))
    hours = float(flow.get("analysis_period_hours", 24)) or 24

    # Heuristic focus block suggestion
    if avg_session >= 75:
        focus_block = 80
        break_block = 15
    elif avg_session >= 45:
        focus_block = 55
        break_block = 10
    elif avg_session >= 30:
        focus_block = 40
        break_block = 8
    else:
        focus_block = 30
        break_block = 6

    efficiency = flow_minutes / (hours * 60.0) if hours > 0 else 0.0
    if efficiency >= 0.25:
        energy_state = "high"
    elif efficiency >= 0.12:
        energy_state = "steady"
    elif efficiency > 0:
        energy_state = "low"
    else:
        energy_state = "unknown"

    confidence = min(0.95, 0.25 + efficiency * 2.0)  # scale up with efficiency
    notes = [
        f"평균 플로우 세션 길이: {avg_session:.1f}분",
        f"24h 효율(flow_density): {efficiency*100:.1f}%",
        f"중단(interruptions): {interruptions}회"
    ]
    tags = []
    if confidence < 0.4:
        tags.append("low_confidence")
    if efficiency < 0.05:
        tags.append("sparse_flow")
    return {
        "focus_block_minutes": int(round(focus_block)),
        "break_block_minutes": int(round(break_block)),
        "confidence": round(confidence, 3),
        "energy_state": energy_state,
        "notes": notes,
        "tags": tags,
    }


def derive_microtiming(groove: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not groove:
        return {
            "microtiming_adjust_ms": 0.0,
            "swing_adjust": 0.0,
            "notes": ["groove_profile_latest.json 없음 → 기본값 유지"],
            "tags": ["insufficient_data", "default_groove"],
        }
    push_pull_ms = float(groove.get("push_pull_ms", 0.0))
    swing_ratio = float(groove.get("swing_ratio", 0.0))
    variance = float(groove.get("microtiming_variance", 0.0))

    # Normalize heuristics
    desired_push_pull = max(-12.0, min(12.0, push_pull_ms * 0.8))  # soften extremes
    desired_swing = max(-0.25, min(0.25, swing_ratio * 1.1))
    if abs(desired_swing) < 0.02:
        desired_swing = 0.0  # snap very small swings to straight feel
    stability = 1.0 - min(1.0, variance / 1.2)  # variance -> stability score
    notes = [
        f"현재 push/pull: {push_pull_ms:.1f}ms → 권장 {desired_push_pull:.1f}ms",
        f"현재 swing: {swing_ratio:.3f} → 권장 {desired_swing:.3f}",
        f"마이크로타이밍 안정성(stability): {stability:.2f}",
    ]
    tags = []
    if stability < 0.5:
        tags.append("timing_unstable")
    return {
        "microtiming_adjust_ms": round(desired_push_pull, 2),
        "swing_adjust": round(desired_swing, 3),
        "notes": notes,
        "tags": tags,
    }


def compute_flow_density(flow: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not flow:
        return None
    summary = flow.get("activity_summary", {})
    flow_minutes = float(summary.get("total_flow_minutes", 0.0))
    hours = float(flow.get("analysis_period_hours", 24)) or 24
    interruptions = int(summary.get("interruptions", 0))
    sessions = int(summary.get("flow_sessions", 0)) or 1
    efficiency = flow_minutes / (hours * 60.0) if hours > 0 else 0.0
    avg_session = flow_minutes / sessions if sessions else 0.0
    interruption_rate = interruptions / hours if hours > 0 else 0.0
    if efficiency >= 0.2:
        classification = "dense"
    elif efficiency >= 0.1:
        classification = "moderate"
    elif efficiency > 0:
        classification = "sparse"
    else:
        classification = "none"
    return {
        "efficiency_ratio": round(efficiency, 4),
        "avg_session_minutes": round(avg_session, 2),
        "interruption_rate_per_hour": round(interruption_rate, 3),
        "classification": classification,
        "raw": {
            "flow_minutes": flow_minutes,
            "hours": hours,
            "sessions": sessions,
            "interruptions": interruptions,
        },
    }


def derive_recommended_presets(focus_info: Dict[str, Any], micro_info: Dict[str, Any]) -> Dict[str, Any]:
    energy = focus_info.get("energy_state", "unknown")
    swing = micro_info.get("swing_adjust", 0.0)
    push_pull = micro_info.get("microtiming_adjust_ms", 0.0)
    if energy == "high":
        binaural = 14.0  # beta
        focus_mode = "precision_low_swing" if abs(swing) < 0.05 else "precision_trim_swing"
        break_mode = "ambient_reset"
    elif energy == "steady":
        binaural = 12.0  # high alpha / low beta
        focus_mode = "steady_mid_swing" if abs(swing) >= 0.05 else "steady_straight"
        break_mode = "soft_ambient"
    elif energy == "low":
        binaural = 10.0  # alpha
        focus_mode = "activation_pattern" if abs(push_pull) < 4 else "activation_trim_pushpull"
        break_mode = "stim_reset"
    else:
        binaural = 11.0
        focus_mode = "baseline_straight"
        break_mode = "neutral"
    micro_profile = {
        "target_push_pull_ms": push_pull,
        "target_swing": swing,
        "suggest_quantize": abs(swing) < 0.02,
    }
    return {
        "focus_music_mode": focus_mode,
        "break_music_mode": break_mode,
        "binaural_target_hz": binaural,
        "microtiming_profile": micro_profile,
    }


def build_recommendations(focus_info: Dict[str, Any], micro_info: Dict[str, Any], flow_density: Optional[Dict[str, Any]], presets: Dict[str, Any]) -> List[str]:
    recs: List[str] = []
    recs.append(f"🕓 권장 집중/휴식 블록: {focus_info['focus_block_minutes']}분 집중 / {focus_info['break_block_minutes']}분 휴식")
    recs.append(f"🎵 권장 포커스 음악 모드: {presets['focus_music_mode']}")
    recs.append(f"🧘 휴식 음악 모드: {presets['break_music_mode']}")
    recs.append(f"🔊 바이노럴 주파수 목표: {presets['binaural_target_hz']:.1f} Hz")
    recs.extend(micro_info.get("notes", []))
    if flow_density:
        recs.append(f"📊 Flow Density: {flow_density['classification']} (효율 {flow_density['efficiency_ratio']*100:.1f}%)")
        if flow_density['classification'] in ("sparse", "none"):
            recs.append("⚠️ 플로우가 희박합니다. 짧은 워밍업 작업 또는 간단한 승리 과제를 먼저 수행하세요.")
    if focus_info.get("energy_state") == "low":
        recs.append("💡 에너지 저하 감지 → 더 짧은 블록으로 실험하거나 리듬 전환 음악 사용 추천")
    if "timing_unstable" in micro_info.get("tags", []):
        recs.append("🛠️ 마이크로타이밍 안정화 필요 → 스윙 최소화 후 30분 재측정")
    return recs


def integrate(hours: int = 24) -> IntegratedRhythmProfile:
    groove = load_json(OUTPUT_DIR / "groove_profile_latest.json")
    flow = load_json(OUTPUT_DIR / "flow_observer_report_latest.json")
    rhythm_meta = find_latest_rhythm_metadata()

    focus_info = derive_focus_blocks(flow)
    micro_info = derive_microtiming(groove)
    flow_density = compute_flow_density(flow)
    presets = derive_recommended_presets(focus_info, micro_info)
    recommendations = build_recommendations(focus_info, micro_info, flow_density, presets)

    combined_confidence = round(min(1.0, focus_info.get("confidence", 0.0) * 0.6 + (0.4 if groove else 0.15)), 3)
    tags = sorted(set(focus_info.get("tags", []) + micro_info.get("tags", [])))
    if not groove or not flow:
        tags.append("partial_sources")

    profile = IntegratedRhythmProfile(
        generated_at=datetime.utcnow().isoformat(timespec="seconds"),
        groove_source=groove,
        flow_source=flow,
        rhythm_metadata=rhythm_meta,
        focus_block_minutes=focus_info["focus_block_minutes"],
        break_block_minutes=focus_info["break_block_minutes"],
        microtiming_adjust_ms=micro_info["microtiming_adjust_ms"],
        swing_adjust=micro_info["swing_adjust"],
        energy_state=focus_info["energy_state"],
        confidence=combined_confidence,
        recommendations=recommendations,
        notes=focus_info.get("notes", []) + micro_info.get("notes", []),
        tags=tags,
        recommended_presets=presets,
        flow_density=flow_density,
    )
    return profile


def save_outputs(profile: IntegratedRhythmProfile) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "rhythm_groove_flow_correlation.json"
    md_path = OUTPUT_DIR / "rhythm_groove_flow_correlation.md"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
    # Markdown summary
    lines: List[str] = []
    lines.append("# Rhythm • Groove • Flow 통합 리포트")
    lines.append(f"생성 시각: {profile.generated_at}")
    lines.append("")
    lines.append("## 블록 추천")
    lines.append(f"- 집중 블록: **{profile.focus_block_minutes}분**")
    lines.append(f"- 휴식 블록: **{profile.break_block_minutes}분**")
    lines.append(f"- 에너지 상태: **{profile.energy_state}** (confidence {profile.confidence:.2f})")
    lines.append("")
    lines.append("## 마이크로타이밍")
    lines.append(f"- Push/Pull 조정: {profile.microtiming_adjust_ms} ms")
    lines.append(f"- Swing 조정: {profile.swing_adjust}")
    lines.append("")
    if profile.flow_density:
        fd = profile.flow_density
        lines.append("## Flow Density")
        lines.append(f"- 분류: **{fd['classification']}**")
        lines.append(f"- 효율: {fd['efficiency_ratio']*100:.2f}%")
        lines.append(f"- 평균 세션 길이: {fd['avg_session_minutes']:.1f}분")
        lines.append(f"- 시간당 중단율: {fd['interruption_rate_per_hour']:.2f}")
        lines.append("")
    lines.append("## 권장 프리셋")
    rp = profile.recommended_presets
    lines.append(f"- Focus Music Mode: `{rp['focus_music_mode']}`")
    lines.append(f"- Break Music Mode: `{rp['break_music_mode']}`")
    lines.append(f"- Binaural Target: {rp['binaural_target_hz']} Hz")
    lines.append(f"- Microtiming: push/pull {rp['microtiming_profile']['target_push_pull_ms']} ms | swing {rp['microtiming_profile']['target_swing']} | quantize={rp['microtiming_profile']['suggest_quantize']}")
    lines.append("")
    lines.append("## 추천(Actionable)")
    for r in profile.recommendations:
        lines.append(f"- {r}")
    lines.append("")
    if profile.tags:
        lines.append("## 태그")
        lines.append("`" + " ".join(profile.tags) + "`")
    lines.append("")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# --------------------------- CLI ---------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Integrate rhythm, groove and flow artifacts")
    p.add_argument("--hours", type=int, default=24, help="Integration lookback window (placeholder for future use)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    profile = integrate(hours=args.hours)
    save_outputs(profile)
    print(f"✅ 통합 리포트 생성 완료: rhythm_groove_flow_correlation.json (confidence={profile.confidence:.2f})")


if __name__ == "__main__":  # pragma: no cover
    main()


# --------------------------- Core Logic ---------------------------
def derive_focus_blocks(flow_report: Optional[Dict[str, Any]]) -> (int, int, float, str, List[str]):
    """Return (focus_block_minutes, break_block_minutes, confidence, energy_state, notes)."""
    notes: List[str] = []
    if not flow_report:
        notes.append("Flow report missing; using default Pomodoro cadence.")
        return 40, 10, 0.3, "unknown", notes

    activity = flow_report.get("activity_summary", {})
    flow_sessions = activity.get("flow_sessions", 0) or 0
    total_flow_min = activity.get("total_flow_minutes", 0.0) or 0.0
    interruptions = activity.get("interruptions", 0) or 0

    if flow_sessions <= 0 or total_flow_min <= 0:
        notes.append("Insufficient flow session data; fallback cadence.")
        return 35, 12, 0.35, "idle", notes

    avg_session = total_flow_min / max(flow_sessions, 1)
    # Map average session length to recommended block (bounded)
    focus_block = int(min(max(avg_session * 0.9, 30), 65))
    # Break: adaptive ~15% of focus block, bounded 5-20
    break_block = int(min(max(focus_block * 0.15, 7), 20))

    # Energy heuristics
    activity_ratio = activity.get("activity_ratio", 0.0)
    if activity_ratio >= 0.35:
        energy = "high"
    elif activity_ratio >= 0.15:
        energy = "medium"
    else:
        energy = "low"

    confidence = 0.5 + min(flow_sessions / 10.0, 0.4) - min(interruptions * 0.03, 0.2)
    confidence = round(max(0.2, min(confidence, 0.95)), 3)

    notes.append(f"Derived avg_session={avg_session:.2f}min → focus_block={focus_block} / break_block={break_block}")
    return focus_block, break_block, confidence, energy, notes


def derive_microtiming(groove: Optional[Dict[str, Any]], rhythm_meta: Optional[Dict[str, Any]]) -> (float, float, List[str]):
    """Return (microtiming_adjust_ms, swing_adjust, notes)."""
    notes: List[str] = []
    if not groove:
        notes.append("Groove profile missing; using neutral timing.")
        return 0.0, 0.0, notes

    base_push_pull = groove.get("push_pull_ms", 0.0)
    swing_ratio = groove.get("swing_ratio", 0.0)

    # Rhythm metadata tempo inference
    bpm = None
    if rhythm_meta:
        bpm = rhythm_meta.get("approx_bpm") or rhythm_meta.get("tempo")
        if isinstance(bpm, (list, tuple)) and bpm:
            bpm = bpm[0]
        if isinstance(bpm, (int, float)):
            notes.append(f"Detected BPM={bpm}")

    # Microtiming adjust heuristic: if swing heavy and BPM fast, reduce push/pull for clarity
    micro_adj = 0.0
    if abs(base_push_pull) > 6:
        micro_adj += -math.copysign(3.0, base_push_pull)
        notes.append("Large push/pull detected → slight normalization")
    if swing_ratio > 0.35 and (bpm and bpm > 128):
        micro_adj += -2.0
        notes.append("Fast tempo + swing → reducing micro push")

    swing_adj = 0.0
    if bpm and bpm < 95 and swing_ratio < 0.2:
        swing_adj = 0.05  # add subtle swing for relaxed low tempo coding
        notes.append("Low tempo → adding subtle swing (0.05)")
    elif bpm and bpm > 140 and swing_ratio > 0.3:
        swing_adj = -0.05
        notes.append("High tempo + existing swing → slight reduction")

    return round(micro_adj, 3), round(swing_adj, 3), notes


def build_recommendations(profile: IntegratedRhythmProfile) -> List[str]:
    rec: List[str] = []
    if profile.energy_state == "high":
        rec.append("⚡ 높은 에너지: 55~65분 집중 블록을 2회 유지 후 점심 전에 짧은 휴식.")
    elif profile.energy_state == "medium":
        rec.append("🌿 중간 에너지: 추천 블록 길이 준수, 첫 블록 후 산책 5분.")
    else:
        rec.append("💤 낮은 에너지: 첫 블록 30~35분 + 활성 휴식 (스트레칭) 권장.")

    if profile.swing_adjust > 0:
        rec.append("🎵 음악 엔진: subtle swing +5% 적용하여 여유감 확보.")
    elif profile.swing_adjust < 0:
        rec.append("🎵 음악 엔진: swing 5% 감소로 명료도 향상.")

    if abs(profile.microtiming_adjust_ms) > 0:
        rec.append(f"🕒 마이크로타이밍 {profile.microtiming_adjust_ms:+.1f}ms 조정 → 리듬 안정화.")

    if profile.confidence < 0.5:
        rec.append("📉 데이터 신뢰도 낮음: 최소 2개 이상 추가 flow 세션 수집 후 재평가.")

    return rec


# --------------------------- Extensions (Presets + Density) ---------------------------
def compute_flow_density(flow_report: Optional[Dict[str, Any]], hours: int) -> Optional[Dict[str, Any]]:
    """Derive simple density metrics from flow observer report.
    If raw events exist we count them; otherwise approximate using summary values.
    """
    if not flow_report:
        return None
    activity = flow_report.get("activity_summary", {})
    total_flow_min = activity.get("total_flow_minutes", 0.0) or 0.0
    flow_sessions = activity.get("flow_sessions", 0) or 0
    raw_events = flow_report.get("events") or flow_report.get("raw_events") or []
    events_count = len(raw_events)
    density_per_hour = total_flow_min / max(hours, 1)
    # Classification thresholds (heuristic): >50 high, >20 medium else low
    if density_per_hour > 50:
        density_class = "high"
    elif density_per_hour > 20:
        density_class = "medium"
    else:
        density_class = "low"
    return {
        "total_flow_minutes": round(total_flow_min, 2),
        "flow_sessions": flow_sessions,
        "density_per_hour": round(density_per_hour, 2),
        "events_count": events_count,
        "density_class": density_class,
    }


def compute_recommended_presets(profile: IntegratedRhythmProfile, groove: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate structured presets for music engine + workflow orchestrator.
    These are downstream-consumable knobs; keeping schema stable helps other scripts.
    """
    base_push_pull = 0.0
    base_swing = 0.0
    if groove:
        base_push_pull = groove.get("push_pull_ms", 0.0) or 0.0
        base_swing = groove.get("swing_ratio", 0.0) or 0.0

    # Mode mapping by energy
    if profile.energy_state == "high":
        mode = "energize"
    elif profile.energy_state == "medium":
        mode = "steady"
    else:
        mode = "recover"

    # Confidence gating – if low confidence, we soften adjustments
    micro_adj = profile.microtiming_adjust_ms * (0.5 if profile.confidence < 0.5 else 1.0)
    swing_target = base_swing + profile.swing_adjust * (0.7 if profile.confidence < 0.5 else 1.0)

    music_engine = {
        "mode": mode,
        "target_swing_ratio": round(swing_target, 3),
        "target_push_pull_ms": round(base_push_pull + micro_adj, 3),
        "confidence": profile.confidence,
        "energy_state": profile.energy_state,
    }

    workflow = {
        "focus_block": profile.focus_block_minutes,
        "break_block": profile.break_block_minutes,
        "cadence_tag": f"{profile.energy_state}{'_low_conf' if profile.confidence < 0.5 else ''}",
        "generated_at": profile.generated_at,
    }

    return {"music_engine": music_engine, "workflow": workflow}


# --------------------------- Main ---------------------------
def integrate(hours: int, open_md: bool = False) -> IntegratedRhythmProfile:
    groove = load_json(OUTPUT_DIR / "groove_profile_latest.json")
    flow = load_json(OUTPUT_DIR / "flow_observer_report_latest.json")
    rhythm_meta = find_latest_rhythm_metadata()

    focus_block, break_block, confidence, energy, notes_blocks = derive_focus_blocks(flow)
    micro_adj, swing_adj, notes_micro = derive_microtiming(groove, rhythm_meta)

    notes = notes_blocks + notes_micro
    tags = []
    if not groove or not flow:
        tags.append("insufficient_data")
    if confidence < 0.5:
        tags.append("low_confidence")

    # Temporary placeholder for dataclass init (recommendations & new fields filled later)
    profile = IntegratedRhythmProfile(
        generated_at=datetime.utcnow().isoformat(),
        groove_source=groove,
        flow_source=flow,
        rhythm_metadata=rhythm_meta,
        focus_block_minutes=focus_block,
        break_block_minutes=break_block,
        microtiming_adjust_ms=micro_adj,
        swing_adjust=swing_adj,
        energy_state=energy,
        confidence=confidence,
        recommendations=[],  # later
        notes=notes,
        tags=tags,
        recommended_presets={},  # later
        flow_density=None,       # later
    )
    profile.recommendations = build_recommendations(profile)
    profile.flow_density = compute_flow_density(flow, hours)
    profile.recommended_presets = compute_recommended_presets(profile, groove)

    # Enrich recommendations with density insights
    if profile.flow_density:
        cls = profile.flow_density.get("density_class")
        if cls == "high":
            profile.recommendations.append("🧠 높은 집중 밀도: 두 번째 블록 후 뇌과로 회복 스트레칭 추천.")
        elif cls == "medium":
            profile.recommendations.append("📈 안정적 집중: 패턴 유지, 오후에 1회 리듬 재평가.")
        else:
            profile.recommendations.append("🔍 낮은 집중 밀도: 환경 방해 요소 점검 및 짧은 워밍업 세션 추가.")

    # Persist JSON
    json_path = OUTPUT_DIR / "rhythm_groove_flow_correlation.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)

    # Persist Markdown summary
    md_path = OUTPUT_DIR / "rhythm_groove_flow_correlation.md"
    md_lines = [
        f"# Rhythm • Groove • Flow Correlation", "",
        f"Generated: {profile.generated_at}", "",
        "## Summary", "",
        f"Energy State: **{profile.energy_state}** (confidence {profile.confidence:.2f})", "",
        f"Focus Block: **{profile.focus_block_minutes}m**  | Break: **{profile.break_block_minutes}m**", "",
        f"Microtiming Adjust: **{profile.microtiming_adjust_ms:+.1f}ms**  | Swing Adjust: **{profile.swing_adjust:+.2f}", "",
        "## Flow Density", "",
        *( [f"- density_per_hour: {profile.flow_density['density_per_hour']}", f"- class: {profile.flow_density['density_class']}"] if profile.flow_density else ["(no density data)"] ), "",
        "## Presets", "",
        f"### Music Engine", "",
        *( [f"- mode: {profile.recommended_presets['music_engine']['mode']}",
            f"- target_swing_ratio: {profile.recommended_presets['music_engine']['target_swing_ratio']}",
            f"- target_push_pull_ms: {profile.recommended_presets['music_engine']['target_push_pull_ms']}"] if profile.recommended_presets else ["(no presets)"] ), "",
        "### Workflow", "",
        *( [f"- focus_block: {profile.recommended_presets['workflow']['focus_block']}",
            f"- break_block: {profile.recommended_presets['workflow']['break_block']}",
            f"- cadence_tag: {profile.recommended_presets['workflow']['cadence_tag']}"] if profile.recommended_presets else [] ), "",
        "## Recommendations", "",
    ] + [f"- {r}" for r in profile.recommendations] + ["", "## Notes", ""] + [f"- {n}" for n in profile.notes] + ["", "## Tags", "", f"`{', '.join(profile.tags) or 'none'}`"]

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))

    if open_md:
        try:
            # VSCode가 있는 경우 code 명령어로 열기 (실패해도 무시)
            import subprocess
            subprocess.Popen(["code", str(md_path)])
        except Exception:
            pass

    return profile


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Integrate rhythm artifacts into a unified profile")
    p.add_argument("--hours", type=int, default=24, help="Lookback hours (currently heuristic only)")
    p.add_argument("--open", action="store_true", help="Open markdown summary in VS Code")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    profile = integrate(hours=args.hours, open_md=args.open)
    print(json.dumps({"status": "ok", "energy_state": profile.energy_state, "focus_block": profile.focus_block_minutes}, ensure_ascii=False))


if __name__ == "__main__":
    main()
