#!/usr/bin/env python3
"""신호 분포 시각화 - I3 디버깅"""

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter
import numpy as np

def load_recent_signals(hours: int = 1):
    """최근 시간 내 신호 로드"""
    ledger_path = Path(__file__).parent.parent / "memory" / "resonance_ledger.jsonl"
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    signals = {"lua": [], "elo": [], "lumen": []}
    
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            event = json.loads(line.strip())
            ts_str = event.get("ts") or event.get("timestamp")
            if not ts_str:
                continue
            
            # 타임스탬프 처리
            if isinstance(ts_str, (int, float)):
                ts = datetime.fromtimestamp(ts_str, tz=timezone.utc)
            else:
                ts_parsed = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                # timezone-aware로 변환
                if ts_parsed.tzinfo is None:
                    ts = ts_parsed.replace(tzinfo=timezone.utc)
                else:
                    ts = ts_parsed
            
            if ts < cutoff:
                continue
            
            persona = event.get("persona_id", "unknown")
            if persona not in signals:
                continue
            
            # 점수 추출
            score = event.get("resonance_score")
            if score is None:
                outcome = event.get("outcome", {})
                score = outcome.get("quality") or outcome.get("confidence")
            
            if score is not None:
                signals[persona].append(float(score))
    
    return {k: np.array(v) for k, v in signals.items() if v}


def analyze_signal_distribution(signals):
    """신호 분포 분석"""
    print("=" * 70)
    print("📊 Trinity Signal Distribution Analysis")
    print("=" * 70)
    
    for persona, values in signals.items():
        if len(values) == 0:
            continue
        
        print(f"\n🔹 {persona.upper()}")
        print(f"   Count: {len(values)}")
        print(f"   Mean:  {np.mean(values):.4f}")
        print(f"   Std:   {np.std(values):.4f}")
        print(f"   Min:   {np.min(values):.4f}")
        print(f"   Max:   {np.max(values):.4f}")
        
        # 히스토그램 (10 bins)
        hist, edges = np.histogram(values, bins=10, range=(0, 1))
        print(f"\n   히스토그램 (10 bins):")
        for i, count in enumerate(hist):
            bar = "█" * int(count / max(hist) * 40)
            print(f"     [{edges[i]:.2f}-{edges[i+1]:.2f}] {count:3d} {bar}")
        
        # Unique 값 분포
        unique_vals = np.unique(values)
        print(f"\n   Unique 값 수: {len(unique_vals)}")
        if len(unique_vals) <= 20:
            print(f"   Unique 값: {sorted(unique_vals)[:10]}...")
    
    # Pairwise correlation
    print("\n" + "=" * 70)
    print("🔺 Pairwise Analysis")
    print("=" * 70)
    
    personas = list(signals.keys())
    for i, p1 in enumerate(personas):
        for p2 in personas[i+1:]:
            v1 = signals[p1]
            v2 = signals[p2]
            
            min_len = min(len(v1), len(v2))
            v1 = v1[:min_len]
            v2 = v2[:min_len]
            
            # Pearson correlation
            corr = np.corrcoef(v1, v2)[0, 1]
            
            # Histogram overlap
            hist1, _ = np.histogram(v1, bins=10, range=(0, 1), density=True)
            hist2, _ = np.histogram(v2, bins=10, range=(0, 1), density=True)
            overlap = np.sum(np.minimum(hist1, hist2))
            
            print(f"\n🔗 {p1.upper()} vs {p2.upper()}")
            print(f"   Pearson correlation: {corr:+.4f}")
            print(f"   Histogram overlap:   {overlap:.4f}")
            
            # Range overlap check
            r1_min, r1_max = np.min(v1), np.max(v1)
            r2_min, r2_max = np.min(v2), np.max(v2)
            overlap_start = max(r1_min, r2_min)
            overlap_end = min(r1_max, r2_max)
            if overlap_start < overlap_end:
                overlap_range = overlap_end - overlap_start
                print(f"   Range overlap:       [{overlap_start:.3f}, {overlap_end:.3f}] ({overlap_range:.3f})")
            else:
                print(f"   Range overlap:       None")


if __name__ == "__main__":
    import sys
    
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    signals = load_recent_signals(hours)
    
    if not signals:
        print("❌ No signals found")
        sys.exit(1)
    
    analyze_signal_distribution(signals)
