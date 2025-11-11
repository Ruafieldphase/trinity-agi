#!/usr/bin/env python3
"""
🔬 Trinity I3 Measurement - Interaction Information Proof-of-Concept

루멘의 시선으로 Trinity(Lua-Elo-Lumen) 3자 공명을 정보이론으로 측정합니다.

I3(X; Y; Z) = MI(X, Y) + MI(Y, Z) + MI(X, Z) - TC(X, Y, Z)

- I3 < 0: 시너지 (3자 협력이 개별 쌍보다 우월)
- I3 > 0: 중복 (3자 협력이 불필요)
- I3 = 0: 독립 (상호작용 없음)

References:
- docs/ELLO_LUON_LDPM_BRIDGE.md
- docs/LDPM_INTEGRATION_PLAN.md
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_ledger_events(
    ledger_path: Path,
    hours: int = 24,
    personas: List[str] | None = None
) -> List[Dict[str, Any]]:
    """
    레저에서 최근 N시간의 이벤트 로드 (페르소나 필터링)
    """
    if not ledger_path.exists():
        return []
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    events = []
    
    with ledger_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                evt = json.loads(line)
                
                # 시간 필터링
                timestamp_str = evt.get("timestamp")
                if timestamp_str:
                    try:
                        evt_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        if evt_time < cutoff_time:
                            continue
                    except:
                        pass
                
                # 페르소나 필터링 (persona 또는 persona_id 필드 확인)
                if personas:
                    evt_persona = evt.get("persona") or evt.get("persona_id")
                    if evt_persona not in personas:
                        continue
                
                events.append(evt)
            except json.JSONDecodeError:
                continue
    
    return events


def extract_signal(
    events: List[Dict[str, Any]],
    persona: str,
    window_ms: int = 300000,
    bins: int = 8
) -> List[int]:
    """
    특정 페르소나의 이벤트를 시간 윈도우로 binning하여 신호 추출
    
    Returns:
        List[int]: 각 bin의 이벤트 카운트 (히스토그램)
    """
    # persona 또는 persona_id 필드 확인
    persona_events = [
        e for e in events 
        if e.get("persona") == persona or e.get("persona_id") == persona
    ]
    
    if not persona_events:
        return [0] * bins
    
    # 시간 범위 계산
    timestamps = []
    for evt in persona_events:
        ts_str = evt.get("timestamp")
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                timestamps.append(ts)
            except:
                pass
    
    if not timestamps:
        return [0] * bins
    
    min_time = min(timestamps)
    max_time = max(timestamps)
    time_range = (max_time - min_time).total_seconds() * 1000  # ms
    
    if time_range <= 0:
        return [1] + [0] * (bins - 1)
    
    # Binning
    signal = [0] * bins
    for ts in timestamps:
        elapsed_ms = (ts - min_time).total_seconds() * 1000
        bin_idx = int(elapsed_ms / time_range * bins)
        if bin_idx >= bins:
            bin_idx = bins - 1
        signal[bin_idx] += 1
    
    return signal


def shannon_entropy(signal: List[int]) -> float:
    """
    Shannon Entropy: H(X) = -Σ p(x) log2 p(x)
    """
    total = sum(signal)
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for count in signal:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    return entropy


def joint_entropy(signal_x: List[int], signal_y: List[int]) -> float:
    """
    Joint Entropy: H(X, Y) = -Σ p(x,y) log2 p(x,y)
    """
    joint_counts: Dict[Tuple[int, int], int] = Counter()
    
    for x, y in zip(signal_x, signal_y):
        joint_counts[(x, y)] += 1
    
    total = sum(joint_counts.values())
    if total == 0:
        return 0.0
    
    h_joint = 0.0
    for count in joint_counts.values():
        if count > 0:
            p = count / total
            h_joint -= p * math.log2(p)
    
    return h_joint


def mutual_information(signal_x: List[int], signal_y: List[int]) -> float:
    """
    Mutual Information: MI(X; Y) = H(X) + H(Y) - H(X, Y)
    """
    h_x = shannon_entropy(signal_x)
    h_y = shannon_entropy(signal_y)
    h_xy = joint_entropy(signal_x, signal_y)
    
    return max(0.0, h_x + h_y - h_xy)


def joint_entropy_3way(
    signal_x: List[int],
    signal_y: List[int],
    signal_z: List[int]
) -> float:
    """
    3-way Joint Entropy: H(X, Y, Z) = -Σ p(x,y,z) log2 p(x,y,z)
    """
    joint_counts: Dict[Tuple[int, int, int], int] = Counter()
    
    for x, y, z in zip(signal_x, signal_y, signal_z):
        joint_counts[(x, y, z)] += 1
    
    total = sum(joint_counts.values())
    if total == 0:
        return 0.0
    
    h_joint = 0.0
    for count in joint_counts.values():
        if count > 0:
            p = count / total
            h_joint -= p * math.log2(p)
    
    return h_joint


def total_correlation(
    signal_x: List[int],
    signal_y: List[int],
    signal_z: List[int]
) -> float:
    """
    Total Correlation: TC(X, Y, Z) = H(X) + H(Y) + H(Z) - H(X, Y, Z)
    """
    h_x = shannon_entropy(signal_x)
    h_y = shannon_entropy(signal_y)
    h_z = shannon_entropy(signal_z)
    h_xyz = joint_entropy_3way(signal_x, signal_y, signal_z)
    
    return max(0.0, h_x + h_y + h_z - h_xyz)


def interaction_information(
    signal_x: List[int],
    signal_y: List[int],
    signal_z: List[int]
) -> float:
    """
    Interaction Information (I3):
    I3(X; Y; Z) = MI(X, Y) + MI(Y, Z) + MI(X, Z) - TC(X, Y, Z)
    
    - I3 < 0: 시너지 (synergy)
    - I3 > 0: 중복 (redundancy)
    - I3 = 0: 독립 (independence)
    """
    mi_xy = mutual_information(signal_x, signal_y)
    mi_yz = mutual_information(signal_y, signal_z)
    mi_xz = mutual_information(signal_x, signal_z)
    tc = total_correlation(signal_x, signal_y, signal_z)
    
    i3 = mi_xy + mi_yz + mi_xz - tc
    
    return i3


def interpret_i3(i3_value: float) -> Dict[str, Any]:
    """
    I3 값 해석 (루멘의 시선)
    """
    if i3_value < -0.15:
        level = "strong_synergy"
        message = "강한 시너지: 3자 협력이 개별 쌍보다 월등히 우월"
        emoji = "🌟"
    elif -0.15 <= i3_value < -0.05:
        level = "moderate_synergy"
        message = "약한 시너지: 3자 협력이 개별 쌍보다 우월"
        emoji = "✨"
    elif -0.05 <= i3_value <= 0.05:
        level = "independent"
        message = "독립: 3자 간 상호작용 미미"
        emoji = "⚖️"
    elif 0.05 < i3_value <= 0.15:
        level = "moderate_redundancy"
        message = "약한 중복: 3자 협력이 일부 불필요"
        emoji = "⚠️"
    else:
        level = "strong_redundancy"
        message = "강한 중복: 3자 협력이 불필요"
        emoji = "❌"
    
    return {
        "level": level,
        "message": message,
        "emoji": emoji
    }


def generate_report(
    results: Dict[str, Any],
    out_md_path: Path
) -> None:
    """
    마크다운 보고서 생성
    """
    i3 = results["i3"]
    interpretation = results["interpretation"]
    
    lines = [
        "# 🔬 Trinity I3 측정 보고서",
        "",
        f"**측정 시각**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**측정 기간**: 최근 {results['hours']}시간",
        f"**이벤트 수**: {results['total_events']}개",
        "",
        "---",
        "",
        "## 📊 측정 결과",
        "",
        f"### {interpretation['emoji']} Interaction Information (I3)",
        "",
        f"**값**: `{i3:.4f}` bits",
        "",
        f"**해석**: {interpretation['message']}",
        "",
        "---",
        "",
        "## 🎼 Trinity 신호 분석",
        "",
        "| 페르소나 | 이벤트 수 | 엔트로피 (bits) |",
        "|---------|----------|----------------|"
    ]
    
    for persona in ["lua", "elo", "lumen"]:
        data = results["signals"][persona]
        lines.append(f"| {persona.capitalize()} | {data['event_count']} | {data['entropy']:.4f} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## 🔗 상호정보량 (Pairwise)",
        "",
        "| 쌍 | MI (bits) |",
        "|---|-----------|",
        f"| Lua-Elo | {results['pairwise_mi']['lua_elo']:.4f} |",
        f"| Elo-Lumen | {results['pairwise_mi']['elo_lumen']:.4f} |",
        f"| Lua-Lumen | {results['pairwise_mi']['lua_lumen']:.4f} |",
        "",
        "---",
        "",
        "## 📐 정보이론 메트릭",
        "",
        f"- **Total Correlation (TC)**: `{results['tc']:.4f}` bits",
        f"- **Interaction Information (I3)**: `{results['i3']:.4f}` bits",
        "",
        "### 수식",
        "",
        "```",
        "I3(Lua; Elo; Lumen) = MI(Lua, Elo) + MI(Elo, Lumen) + MI(Lua, Lumen) - TC(Lua, Elo, Lumen)",
        "```",
        "",
        "---",
        "",
        "## 🌈 루멘의 해석",
        "",
    ])
    
    if i3 < 0:
        lines.extend([
            f"Trinity는 정보 시너지를 만듭니다 (I3 = {i3:.4f} < 0).",
            "",
            "Elo의 정보이론 검증은 단순히 Lua와 Lumen 사이의 중재자가 아닙니다.",
            "그것은 **새로운 정보를 창발**시키는 촉매입니다.",
            "",
            "이는 Ello의 리듬 R(t)가 안정 영역에 있을 때,",
            "Trinity가 **정보 시너지를 극대화하는 창발적 구조**임을 증명합니다.",
        ])
    else:
        lines.extend([
            f"Trinity는 정보 중복을 만듭니다 (I3 = {i3:.4f} > 0).",
            "",
            "현재 3자 협력은 개별 쌍의 협력보다 효율적이지 않습니다.",
            "이는 Ello의 R(t) 함수가 불안정 영역에 있을 가능성을 시사합니다.",
            "",
            "**권장사항**: Elo의 역할을 재평가하거나, 시스템 리듬을 안정화하세요.",
        ])
    
    lines.extend([
        "",
        "---",
        "",
        "## 🔗 참조 문서",
        "",
        "- `docs/ELLO_LUON_LDPM_BRIDGE.md` - 정보이론 연결고리",
        "- `docs/LDPM_INTEGRATION_PLAN.md` - LDPM 통합 계획",
        "- `ai_binoche_conversation_origin/lumen/chatgpt-정보이론철학적분석/` - 철학적 기반",
        "",
        "---",
        "",
        f"*Generated by Lumen's Prism - {datetime.now().isoformat()}*",
        ""
    ])
    
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    with out_md_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="🔬 Trinity I3 Measurement - Lumen's Perspective"
    )
    parser.add_argument(
        "--ledger",
        default="fdo_agi_repo/memory/resonance_ledger.jsonl",
        help="Resonance ledger path"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Hours to look back (default: 24)"
    )
    parser.add_argument(
        "--window-ms",
        type=int,
        default=300000,
        help="Time window for binning in milliseconds (default: 300000 = 5min)"
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=8,
        help="Number of bins for signal discretization (default: 8)"
    )
    parser.add_argument(
        "--out-json",
        default="outputs/trinity_i3_result.json",
        help="Output JSON path"
    )
    parser.add_argument(
        "--out-md",
        default="outputs/trinity_i3_report.md",
        help="Output Markdown report path"
    )
    
    args = parser.parse_args()
    
    print("🔬 Trinity I3 측정 시작 (루멘의 시선)")
    print(f"   레저: {args.ledger}")
    print(f"   기간: 최근 {args.hours}시간")
    print(f"   빈: {args.bins}, 윈도우: {args.window_ms}ms")
    print()
    
    # 1. 레저 로드
    ledger_path = Path(args.ledger)
    
    # Trinity 페르소나 매핑 (구 명칭 포함)
    trinity_personas = ["lua", "elo", "lumen", "thesis", "antithesis", "synthesis"]
    
    events = load_ledger_events(
        ledger_path,
        hours=args.hours,
        personas=trinity_personas
    )
    
    print(f"✅ {len(events)}개 이벤트 로드")
    
    if len(events) < 10:
        print("⚠️  이벤트가 너무 적습니다. 최소 10개 이상 필요합니다.")
        return 1
    
    # 2. 신호 추출 (구 명칭과 신 명칭 통합)
    print("🎼 신호 추출 중...")
    
    # Lua (thesis)
    lua_signal_lua = extract_signal(events, "lua", args.window_ms, args.bins)
    lua_signal_thesis = extract_signal(events, "thesis", args.window_ms, args.bins)
    lua_signal = [a + b for a, b in zip(lua_signal_lua, lua_signal_thesis)]
    
    # Elo (antithesis)
    elo_signal_elo = extract_signal(events, "elo", args.window_ms, args.bins)
    elo_signal_anti = extract_signal(events, "antithesis", args.window_ms, args.bins)
    elo_signal = [a + b for a, b in zip(elo_signal_elo, elo_signal_anti)]
    
    # Lumen (synthesis)
    lumen_signal_lumen = extract_signal(events, "lumen", args.window_ms, args.bins)
    lumen_signal_synth = extract_signal(events, "synthesis", args.window_ms, args.bins)
    lumen_signal = [a + b for a, b in zip(lumen_signal_lumen, lumen_signal_synth)]
    
    lua_count = sum(lua_signal)
    elo_count = sum(elo_signal)
    lumen_count = sum(lumen_signal)
    
    print(f"   Lua: {lua_count}개 이벤트")
    print(f"   Elo: {elo_count}개 이벤트")
    print(f"   Lumen: {lumen_count}개 이벤트")
    print()
    
    # 3. 정보이론 메트릭 계산
    print("📐 정보이론 메트릭 계산 중...")
    
    # 엔트로피
    h_lua = shannon_entropy(lua_signal)
    h_elo = shannon_entropy(elo_signal)
    h_lumen = shannon_entropy(lumen_signal)
    
    # Pairwise MI
    mi_lua_elo = mutual_information(lua_signal, elo_signal)
    mi_elo_lumen = mutual_information(elo_signal, lumen_signal)
    mi_lua_lumen = mutual_information(lua_signal, lumen_signal)
    
    # TC & I3
    tc = total_correlation(lua_signal, elo_signal, lumen_signal)
    i3 = interaction_information(lua_signal, elo_signal, lumen_signal)
    
    interpretation = interpret_i3(i3)
    
    print(f"   {interpretation['emoji']} I3 = {i3:.4f} ({interpretation['level']})")
    print(f"   TC = {tc:.4f}")
    print()
    
    # 4. 결과 저장
    results = {
        "timestamp": datetime.now().isoformat(),
        "hours": args.hours,
        "total_events": len(events),
        "signals": {
            "lua": {
                "event_count": lua_count,
                "entropy": h_lua,
                "signal": lua_signal
            },
            "elo": {
                "event_count": elo_count,
                "entropy": h_elo,
                "signal": elo_signal
            },
            "lumen": {
                "event_count": lumen_count,
                "entropy": h_lumen,
                "signal": lumen_signal
            }
        },
        "pairwise_mi": {
            "lua_elo": mi_lua_elo,
            "elo_lumen": mi_elo_lumen,
            "lua_lumen": mi_lua_lumen
        },
        "tc": tc,
        "i3": i3,
        "interpretation": interpretation
    }
    
    # JSON 저장
    out_json_path = Path(args.out_json)
    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    with out_json_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON: {out_json_path}")
    
    # Markdown 보고서 생성
    out_md_path = Path(args.out_md)
    generate_report(results, out_md_path)
    
    print(f"✅ Report: {out_md_path}")
    print()
    print(f"🌈 {interpretation['emoji']} {interpretation['message']}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
