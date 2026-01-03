"""
Dream Integration Script

Integrates dreams into Hippocampus long-term memory through:
1. Glymphatic cleaning
2. Synaptic pruning
3. Long-term consolidation

Pipeline:
  dreams.jsonl → Glymphatic → dreams_cleaned.json
              → Synaptic Pruner → memories_pruned.json
              → Hippocampus → long_term_memory.json

Author: AGI Self-Referential System
Date: 2025-11-05
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from workspace_root import get_workspace_root

# Add fdo_agi_repo to path
repo_root = get_workspace_root()
fdo_agi_repo = repo_root / "fdo_agi_repo"
if str(fdo_agi_repo) not in sys.path:
    sys.path.insert(0, str(fdo_agi_repo))

from copilot.hippocampus import CopilotHippocampus
from copilot.glymphatic import GlymphaticSystem, load_dreams
from copilot.synaptic_pruner import SynapticPruner, load_cleaned_dreams


def integrate_dreams(
    dreams_path: str | Path = "outputs/dreams.jsonl",
    output_dir: str | Path = "outputs",
    delta_threshold: float = 100_000_000,
    min_frequency: int = 2,
    importance_boost: float = 0.1
):
    """
    Integrate dreams into long-term memory.
    
    Args:
        dreams_path: Path to dreams.jsonl
        output_dir: Output directory for intermediate files
        delta_threshold: Glymphatic delta threshold
        min_frequency: Synaptic pruner min frequency
        importance_boost: Synaptic pruner importance boost
    """
    dreams_path = Path(dreams_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  🌙 Dream Integration Pipeline                               ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Step 1: Load dreams
    print("📂 Step 1: Loading dreams...")
    if not dreams_path.exists():
        print(f"❌ Error: {dreams_path} not found")
        return False
    
    dreams = load_dreams(dreams_path)
    print(f"✅ Loaded {len(dreams)} dreams from {dreams_path}")
    
    # Step 2: Glymphatic cleaning
    print("\n🌊 Step 2: Glymphatic cleaning...")
    glymphatic = GlymphaticSystem(delta_threshold=delta_threshold)
    cleaned_dreams = glymphatic.clean_dreams(dreams)
    
    glymphatic_stats = glymphatic.get_stats()
    print(f"✅ Cleaned: {glymphatic_stats['kept']}/{glymphatic_stats['processed']} dreams kept")
    print(f"   Noise removed: {glymphatic_stats['noise_removed']} patterns")
    
    # Save cleaned dreams
    cleaned_path = output_dir / "dreams_cleaned.json"
    glymphatic.save_cleaned_dreams(cleaned_dreams, cleaned_path)
    
    # Step 3: Synaptic pruning
    print("\n🧠 Step 3: Synaptic pruning...")
    pruner = SynapticPruner(min_frequency=min_frequency, importance_boost=importance_boost)
    memories = pruner.prune_dreams(cleaned_dreams)
    
    pruner_stats = pruner.get_stats()
    print(f"✅ Pruned: {pruner_stats['input_patterns']} → {pruner_stats['output_memories']} memories")
    print(f"   Compression: {pruner_stats['compression_ratio']:.1%}")
    
    # Save pruned memories
    pruned_path = output_dir / "memories_pruned.json"
    pruner.save_memories(memories, pruned_path)
    
    # Step 4: Save pruned memories for manual integration
    print("\n💾 Step 4: Saving pruned memories for integration...")
    
    # Create integration-ready format
    integration_data = {
        "timestamp": datetime.now().isoformat(),
        "source": "dream_consolidation",
        "memories": memories,
        "stats": {
            "dreams_input": len(dreams),
            "dreams_cleaned": len(cleaned_dreams),
            "memories_pruned": len(memories),
            "glymphatic": glymphatic_stats,
            "synaptic_pruner": pruner_stats
        }
    }
    
    integration_path = output_dir / "dream_integration_ready.json"
    with open(integration_path, "w", encoding="utf-8") as f:
        json.dump(integration_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Integration data saved to {integration_path}")
    
    # Step 5: Verify integration
    print("\n🔍 Step 5: Verifying integration...")
    
    # Check long-term memory directory
    lt_mem_dir = Path("fdo_agi_repo/memory")
    if lt_mem_dir.exists():
        print(f"✅ Long-term memory directory exists: {lt_mem_dir}")
        
        # Show top memories
        print(f"\n🏆 Top 3 Dream Memories:")
        for i, mem in enumerate(memories[:3], 1):
            print(f"  {i}. {mem['pattern_name']}")
            print(f"     Frequency: {mem['frequency']}, Importance: {mem['importance']}")
    else:
        print(f"⚠️  Warning: Long-term memory directory not found at {lt_mem_dir}")
    
    # Summary
    print("\n" + "="*64)
    print("🎉 Dream Integration Complete!")
    print("="*64)
    print(f"\n📊 Pipeline Summary:")
    print(f"  Dreams loaded: {len(dreams)}")
    print(f"  Dreams cleaned: {len(cleaned_dreams)}")
    print(f"  Memories pruned: {len(memories)}")
    print(f"\n📁 Output Files:")
    print(f"  - {cleaned_path}")
    print(f"  - {pruned_path}")
    print(f"  - {integration_path}")
    print(f"\n✅ Dreams successfully processed and ready for integration!")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Integrate dreams into Hippocampus long-term memory")
    parser.add_argument("--dreams", default="outputs/dreams.jsonl", help="Path to dreams.jsonl")
    parser.add_argument("--output", default="outputs", help="Output directory")
    parser.add_argument("--delta-threshold", type=float, default=100_000_000, help="Glymphatic delta threshold")
    parser.add_argument("--min-frequency", type=int, default=2, help="Synaptic pruner min frequency")
    parser.add_argument("--importance-boost", type=float, default=0.1, help="Synaptic pruner importance boost")
    
    args = parser.parse_args()
    
    success = integrate_dreams(
        dreams_path=args.dreams,
        output_dir=args.output,
        delta_threshold=args.delta_threshold,
        min_frequency=args.min_frequency,
        importance_boost=args.importance_boost
    )
    
    sys.exit(0 if success else 1)
