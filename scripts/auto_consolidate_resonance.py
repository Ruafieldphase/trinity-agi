"""
auto_consolidate_resonance.py
Resonance Ledger → Hippocampus 자동 consolidation 스크립트
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root

# Add workspace to path
workspace = get_workspace_root()
sys.path.insert(0, str(workspace))

from fdo_agi_repo.orchestrator.resonance_bridge import (
    init_resonance_store,
    consolidate_to_hippocampus,
)


def main():
    """Main consolidation routine"""
    print("🌊 Resonance → Hippocampus Auto-Consolidation")
    print("=" * 60)
    
    # Initialize
    init_resonance_store()
    
    # Consolidation config
    config = {
        "hours": 24,  # 최근 24시간
        "min_importance": 0.7,  # 중요도 0.7 이상만
    }
    
    # Load config if exists
    config_path = workspace / "configs" / "consolidation_config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            user_config = json.load(f)
            config.update(user_config)
        print(f"✅ Loaded config from {config_path}")
    
    print(f"⏰ Processing last {config['hours']} hours")
    print(f"📊 Min importance: {config['min_importance']}")
    print()
    
    # Run consolidation
    result = consolidate_to_hippocampus(
        hours=config["hours"],
        min_importance=config["min_importance"],
        workspace_root=workspace,
    )
    
    # Report
    print("📈 Consolidation Results:")
    print(f"  Processed: {result['processed']} events")
    print(f"  Stored: {result['stored']} memories")
    print(f"  Skipped (low importance): {result['skipped_low_importance']}")
    print()
    
    cons_result = result.get("consolidation_result", {})
    print("🧠 Long-term Memory:")
    print(f"  Episodic: {cons_result.get('episodic', 0)}")
    print(f"  Semantic: {cons_result.get('semantic', 0)}")
    print(f"  Procedural: {cons_result.get('procedural', 0)}")
    print(f"  Total: {cons_result.get('total', 0)}")
    print()
    
    # Save result
    output_path = workspace / "outputs" / "consolidation_latest.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"💾 Saved results to {output_path}")
    
    # Summary
    if result["stored"] > 0:
        print()
        print("✅ Consolidation complete!")
        print(f"   {result['stored']} events → Hippocampus long-term memory")
    else:
        print()
        print("⚠️  No events met importance threshold")
        print(f"   Try lowering min_importance (current: {config['min_importance']})")


if __name__ == "__main__":
    main()
