#!/usr/bin/env python3
"""Trinity 신호 분리 검증 - 최근 trinity_demo 이벤트만 분석"""

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / "memory" / "resonance_ledger.jsonl"


def load_trinity_demo_signals(hours: int = 24):
    """최근 trinity_demo 소스 신호만 로드"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    signals = {"lua": [], "elo": [], "Core": []}
    
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line.strip())
            except:
                continue
            
            # trinity_demo 소스만 필터
            metadata = event.get("metadata", {})
            if metadata.get("source") != "trinity_demo":
                continue
            
            # 타임스탬프 확인
            ts_str = event.get("ts") or event.get("timestamp")
            if ts_str:
                if isinstance(ts_str, (int, float)):
                    ts = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                else:
                    ts_parsed = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts_parsed.tzinfo is None:
                        ts = ts_parsed.replace(tzinfo=timezone.utc)
                    else:
                        ts = ts_parsed
                
                if ts < cutoff:
                    continue
            
            persona = event.get("persona_id")
            if persona not in signals:
                continue
            
            score = event.get("resonance_score")
            if score is not None:
                signals[persona].append(float(score))
    
    return {k: np.array(v) for k, v in signals.items() if v}


def analyze_separation(signals):
    """신호 분리 검증"""
    print("=" * 70)
    print("📊 Trinity Signal Separation Verification (trinity_demo only)")
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
        
        # Expected ranges
        expected = {
            "lua": (0.1, 0.3),
            "Core": (0.4, 0.6),
            "elo": (0.7, 0.9)
        }
        
        exp_min, exp_max = expected.get(persona, (0, 1))
        in_range = np.sum((values >= exp_min) & (values <= exp_max))
        in_range_pct = (in_range / len(values)) * 100
        
        print(f"\n   Expected Range: [{exp_min}, {exp_max}]")
        print(f"   In Range: {in_range}/{len(values)} ({in_range_pct:.1f}%)")
        
        if in_range_pct >= 95:
            print(f"   ✅ PASS: Separation verified")
        else:
            print(f"   ⚠️  WARN: Some values outside expected range")
    
    # Pairwise overlap check
    print("\n" + "=" * 70)
    print("🔺 Range Overlap Check")
    print("=" * 70)
    
    personas = list(signals.keys())
    overlap_found = False
    
    for i, p1 in enumerate(personas):
        for p2 in personas[i+1:]:
            v1 = signals[p1]
            v2 = signals[p2]
            
            r1_min, r1_max = np.min(v1), np.max(v1)
            r2_min, r2_max = np.min(v2), np.max(v2)
            
            overlap_start = max(r1_min, r2_min)
            overlap_end = min(r1_max, r2_max)
            
            print(f"\n🔗 {p1.upper()} vs {p2.upper()}")
            print(f"   {p1.upper()} range: [{r1_min:.3f}, {r1_max:.3f}]")
            print(f"   {p2.upper()} range: [{r2_min:.3f}, {r2_max:.3f}]")
            
            if overlap_start < overlap_end:
                overlap_range = overlap_end - overlap_start
                print(f"   ⚠️  Range overlap: [{overlap_start:.3f}, {overlap_end:.3f}] ({overlap_range:.3f})")
                overlap_found = True
            else:
                print(f"   ✅ No overlap")
    
    print("\n" + "=" * 70)
    if not overlap_found:
        print("🎯 SUCCESS: All signals are cleanly separated!")
    else:
        print("⚠️  ATTENTION: Some overlap detected")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    signals = load_trinity_demo_signals(hours)
    
    if not signals:
        print("❌ No trinity_demo signals found in recent ledger")
        print(f"   (Checked last {hours} hours)")
        sys.exit(1)
    
    analyze_separation(signals)
