"""
Synaptic Pruner for GitHub Copilot Hippocampus

Mimics synaptic pruning in the brain - strengthens important connections,
weakens or removes less important ones.

Key Functions:
1. Remove duplicate patterns
2. Merge similar memories
3. Prune low-importance memories
4. Prepare high-quality memories for long-term storage

Author: AGI Self-Referential System
Date: 2025-11-05
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter
from datetime import datetime


class SynapticPruner:
    """
    Synaptic pruner for optimizing memories.
    
    Strategies:
    - Remove exact duplicates
    - Merge similar patterns
    - Prune low-frequency patterns
    - Boost high-frequency important patterns
    """
    
    def __init__(self, min_frequency: int = 2, importance_boost: float = 0.1):
        """
        Initialize synaptic pruner.
        
        Args:
            min_frequency: Minimum frequency to keep a pattern (default: 2)
            importance_boost: Importance boost per frequency (default: 0.1)
        """
        self.min_frequency = min_frequency
        self.importance_boost = importance_boost
        self.stats = {
            "input_dreams": 0,
            "input_patterns": 0,
            "unique_patterns": 0,
            "pruned_patterns": 0,
            "output_memories": 0
        }
    
    def extract_pattern_name(self, pattern: str) -> str:
        """
        Extract pattern name without delta.
        
        Example: "system_startup (delta=123)" -> "system_startup"
        """
        if "(delta=" in pattern:
            return pattern.split(" (delta=")[0]
        return pattern
    
    def prune_dreams(self, dreams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prune dreams into consolidated memories.
        
        Args:
            dreams: List of cleaned dreams
            
        Returns:
            List of pruned memory entries
        """
        self.stats["input_dreams"] = len(dreams)
        
        # Step 1: Extract all patterns
        all_patterns = []
        for dream in dreams:
            patterns = dream.get("patterns", [])
            self.stats["input_patterns"] += len(patterns)
            all_patterns.extend(patterns)
        
        # Step 2: Count pattern frequency
        pattern_names = [self.extract_pattern_name(p) for p in all_patterns]
        pattern_freq = Counter(pattern_names)
        self.stats["unique_patterns"] = len(pattern_freq)
        
        # Step 3: Prune low-frequency patterns
        kept_patterns = {
            name: freq for name, freq in pattern_freq.items()
            if freq >= self.min_frequency
        }
        self.stats["pruned_patterns"] = len(pattern_freq) - len(kept_patterns)
        
        # Step 4: Create consolidated memories
        memories = []
        for pattern_name, frequency in kept_patterns.items():
            # Calculate importance based on frequency
            base_importance = 0.5
            importance = min(0.95, base_importance + (frequency * self.importance_boost))
            
            memory = {
                "pattern_name": pattern_name,
                "frequency": frequency,
                "importance": round(importance, 2),
                "type": "episodic",  # From dreams
                "category": self._categorize_pattern(pattern_name),
                "pruned_at": datetime.now().isoformat(),
                "source": "dream_consolidation"
            }
            memories.append(memory)
        
        self.stats["output_memories"] = len(memories)
        
        # Sort by importance (descending)
        memories.sort(key=lambda x: x["importance"], reverse=True)
        
        return memories
    
    def _categorize_pattern(self, pattern_name: str) -> str:
        """Categorize pattern by name."""
        pattern_lower = pattern_name.lower()
        
        if "error" in pattern_lower or "fail" in pattern_lower:
            return "error"
        elif "startup" in pattern_lower or "init" in pattern_lower:
            return "initialization"
        elif "task" in pattern_lower or "complete" in pattern_lower:
            return "task_completion"
        elif "user" in pattern_lower or "input" in pattern_lower:
            return "user_interaction"
        else:
            return "general"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pruning statistics."""
        return {
            **self.stats,
            "compression_ratio": self.stats["output_memories"] / self.stats["input_patterns"] if self.stats["input_patterns"] > 0 else 0,
            "prune_rate": self.stats["pruned_patterns"] / self.stats["unique_patterns"] if self.stats["unique_patterns"] > 0 else 0
        }
    
    def save_memories(self, memories: List[Dict[str, Any]], output_path: str | Path):
        """
        Save pruned memories to JSON file.
        
        Args:
            memories: List of memory dicts
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(memories, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(memories)} pruned memories to {output_path}")


def load_cleaned_dreams(dreams_path: str | Path) -> List[Dict[str, Any]]:
    """
    Load cleaned dreams from JSON file.
    
    Args:
        dreams_path: Path to dreams_cleaned.json
        
    Returns:
        List of dream dicts
    """
    with open(dreams_path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    # Test synaptic pruner
    print("🧠 Testing Synaptic Pruner...")
    
    # Load cleaned dreams
    dreams_path = Path("outputs/dreams_cleaned.json")
    if not dreams_path.exists():
        print("❌ No dreams_cleaned.json found. Run glymphatic.py first.")
        exit(1)
    
    dreams = load_cleaned_dreams(dreams_path)
    print(f"📊 Loaded {len(dreams)} cleaned dreams")
    
    # Prune dreams
    pruner = SynapticPruner(min_frequency=2, importance_boost=0.1)
    memories = pruner.prune_dreams(dreams)
    
    # Show stats
    stats = pruner.get_stats()
    print(f"\n✅ Synaptic Pruning Complete:")
    print(f"  Input dreams: {stats['input_dreams']}")
    print(f"  Input patterns: {stats['input_patterns']}")
    print(f"  Unique patterns: {stats['unique_patterns']}")
    print(f"  Pruned patterns: {stats['pruned_patterns']} ({stats['prune_rate']:.1%})")
    print(f"  Output memories: {stats['output_memories']}")
    print(f"  Compression ratio: {stats['compression_ratio']:.1%}")
    
    # Show top memories
    print(f"\n🏆 Top 5 Memories (by importance):")
    for i, mem in enumerate(memories[:5], 1):
        print(f"  {i}. {mem['pattern_name']} (freq={mem['frequency']}, imp={mem['importance']})")
    
    # Save pruned memories
    output_path = Path("outputs/memories_pruned.json")
    pruner.save_memories(memories, output_path)
    
    print(f"\n🎯 Next: Integrate memories into Hippocampus long-term storage")
