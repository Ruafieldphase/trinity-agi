"""
generate_dreams_from_resonance.py
Resonance 패턴 기반 자동 Dream 생성
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter
from workspace_root import get_workspace_root

# Add workspace to path
workspace = get_workspace_root()
sys.path.insert(0, str(workspace))

from fdo_agi_repo.orchestrator.resonance_bridge import (
    init_resonance_store,
    _RESONANCE_STORE,
)


def extract_high_delta_patterns(hours: int = 24, top_k: int = 10):
    """Extract high-delta patterns from Resonance Ledger"""
    if _RESONANCE_STORE is None:
        init_resonance_store()
    
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    all_events = _RESONANCE_STORE.read_all()
    recent_events = [
        e for e in all_events
        if e.timestamp >= cutoff
    ]
    
    # Collect patterns with their deltas (quality as proxy)
    patterns = []
    for event in recent_events:
        quality = event.metrics.get("quality", 0.0)
        delta = quality * 1000000  # Scale for Dream Mode compatibility
        
        patterns.append({
            "pattern": event.resonance_key,
            "delta": delta,
            "quality": quality,
            "timestamp": event.timestamp.isoformat(),
        })
    
    # Sort by delta
    patterns.sort(key=lambda x: x["delta"], reverse=True)
    
    return patterns[:top_k]


def generate_dreams(patterns: list, num_dreams: int = 5):
    """Generate dreams by recombining high-delta patterns"""
    import random
    
    dreams = []
    
    for i in range(num_dreams):
        # Random recombination (2-3 patterns per dream)
        num_patterns = random.randint(2, min(3, len(patterns)))
        selected = random.sample(patterns, num_patterns)
        
        # Create dream
        dream = {
            "dream_id": f"dream_resonance_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "resonance_ledger",
            "patterns": [
                f"{p['pattern']} (delta={p['delta']:.0f})"
                for p in selected
            ],
            "recombinations": [
                " + ".join([p["pattern"] for p in selected])
            ],
            "narrative": f"In this dream, {' then '.join([p['pattern'] for p in selected])}...",
            "interesting": True,  # Resonance-based dreams are always interesting
            "delta": sum(p["delta"] for p in selected) / len(selected),
            "metadata": {
                "avg_quality": sum(p["quality"] for p in selected) / len(selected),
                "pattern_count": len(selected),
            }
        }
        
        dreams.append(dream)
    
    return dreams


def main():
    """Main dream generation routine"""
    print("🌙 Dream Generation from Resonance Ledger")
    print("=" * 60)
    
    # Config
    hours = 24
    top_k_patterns = 10
    num_dreams = 5
    
    print(f"⏰ Analyzing last {hours} hours")
    print(f"📊 Extracting top {top_k_patterns} patterns")
    print(f"🌙 Generating {num_dreams} dreams")
    print()
    
    # Extract patterns
    patterns = extract_high_delta_patterns(hours=hours, top_k=top_k_patterns)
    
    if not patterns:
        print("⚠️  No patterns found in Resonance Ledger")
        print("   Run some tasks first to populate the ledger")
        return
    
    print(f"✅ Found {len(patterns)} high-quality patterns:")
    for p in patterns[:5]:
        print(f"   • {p['pattern']:<40} (Δ={p['delta']:.0f})")
    if len(patterns) > 5:
        print(f"   ... and {len(patterns) - 5} more")
    print()
    
    # Generate dreams
    dreams = generate_dreams(patterns, num_dreams=num_dreams)
    
    print(f"🌙 Generated {len(dreams)} dreams:")
    for dream in dreams:
        print(f"   • {dream['dream_id']}")
        print(f"     Patterns: {', '.join(dream['patterns'][:2])}...")
        print(f"     Avg Delta: {dream['delta']:.0f}")
    print()
    
    # Save dreams
    output_path = workspace / "outputs" / "dreams_from_resonance.jsonl"
    with open(output_path, "a") as f:
        for dream in dreams:
            f.write(json.dumps(dream) + "\n")
    
    print(f"💾 Saved {len(dreams)} dreams to {output_path}")
    
    # Also save summary
    summary_path = workspace / "outputs" / "dream_generation_summary.json"
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "hours": hours,
            "top_k_patterns": top_k_patterns,
            "num_dreams": num_dreams,
        },
        "patterns_found": len(patterns),
        "dreams_generated": len(dreams),
        "avg_delta": sum(d["delta"] for d in dreams) / len(dreams) if dreams else 0,
    }
    
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"📊 Saved summary to {summary_path}")
    print()
    print("✅ Dream generation complete!")
    print(f"   Next: Run Dream Integration to consolidate these dreams")


if __name__ == "__main__":
    main()
