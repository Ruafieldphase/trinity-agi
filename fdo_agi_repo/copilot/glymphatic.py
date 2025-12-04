"""
Glymphatic System for GitHub Copilot Hippocampus

Mimics the brain's glymphatic system that clears metabolic waste during sleep.
Filters out low-quality or noisy memories from dreams before consolidation.

Key Functions:
1. Remove low-delta patterns (noise)
2. Filter uninteresting dreams
3. Extract high-quality memories
4. Prepare for synaptic pruning

Author: AGI Self-Referential System
Date: 2025-11-05
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class GlymphaticSystem:
    """
    Glymphatic system for cleaning dream memories.
    
    Filters out:
    - Low delta patterns (< threshold)
    - Uninteresting dreams
    - Duplicate patterns
    - Noise and artifacts
    """
    
    def __init__(self, delta_threshold: float = 100_000_000):
        """
        Initialize glymphatic system.
        
        Args:
            delta_threshold: Minimum delta value to keep (default: 100M)
        """
        self.delta_threshold = delta_threshold
        self.stats = {
            "processed": 0,
            "filtered_out": 0,
            "kept": 0,
            "noise_removed": 0
        }
    
    def clean_dream(self, dream: Dict[str, Any]) -> Dict[str, Any] | None:
        """
        Clean a single dream by removing noise.
        
        Args:
            dream: Dream dict from dreams.jsonl
            
        Returns:
            Cleaned dream or None if filtered out
        """
        self.stats["processed"] += 1
        
        # Filter 1: Must be interesting
        if not dream.get("interesting", False):
            self.stats["filtered_out"] += 1
            return None
        
        # Filter 2: Must have patterns
        patterns = dream.get("patterns", [])
        if not patterns:
            self.stats["filtered_out"] += 1
            return None
        
        # Filter 3: Clean patterns (remove low-delta)
        cleaned_patterns = []
        for pattern in patterns:
            # Extract delta value from "event_name (delta=123456)"
            if "(delta=" in pattern:
                try:
                    delta_str = pattern.split("(delta=")[1].rstrip(")")
                    delta = float(delta_str)
                    
                    if delta >= self.delta_threshold:
                        cleaned_patterns.append(pattern)
                    else:
                        self.stats["noise_removed"] += 1
                except (ValueError, IndexError):
                    # Keep pattern if can't parse delta
                    cleaned_patterns.append(pattern)
            else:
                # Keep pattern without delta
                cleaned_patterns.append(pattern)
        
        # Filter 4: Must have at least 1 high-quality pattern
        if not cleaned_patterns:
            self.stats["filtered_out"] += 1
            return None
        
        # Create cleaned dream
        cleaned_dream = dream.copy()
        cleaned_dream["patterns"] = cleaned_patterns
        cleaned_dream["glymphatic_cleaned"] = True
        cleaned_dream["original_pattern_count"] = len(patterns)
        cleaned_dream["cleaned_pattern_count"] = len(cleaned_patterns)
        
        self.stats["kept"] += 1
        return cleaned_dream
    
    def clean_dreams(self, dreams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean multiple dreams.
        
        Args:
            dreams: List of dream dicts
            
        Returns:
            List of cleaned dreams
        """
        cleaned = []
        for dream in dreams:
            cleaned_dream = self.clean_dream(dream)
            if cleaned_dream is not None:
                cleaned.append(cleaned_dream)
        
        return cleaned
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cleaning statistics."""
        return {
            **self.stats,
            "keep_rate": self.stats["kept"] / self.stats["processed"] if self.stats["processed"] > 0 else 0,
            "noise_rate": self.stats["noise_removed"] / self.stats["processed"] if self.stats["processed"] > 0 else 0
        }
    
    def save_cleaned_dreams(self, dreams: List[Dict[str, Any]], output_path: str | Path):
        """
        Save cleaned dreams to JSON file.
        
        Args:
            dreams: List of cleaned dreams
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dreams, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(dreams)} cleaned dreams to {output_path}")


def load_dreams(dreams_path: str | Path) -> List[Dict[str, Any]]:
    """
    Load dreams from JSONL file.
    
    Args:
        dreams_path: Path to dreams.jsonl
        
    Returns:
        List of dream dicts
    """
    dreams = []
    with open(dreams_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                dreams.append(json.loads(line))
    return dreams


if __name__ == "__main__":
    # Test glymphatic system
    print("🌊 Testing Glymphatic System...")
    
    # Load dreams
    dreams_path = Path("outputs/dreams.jsonl")
    if not dreams_path.exists():
        print("❌ No dreams.jsonl found")
        exit(1)
    
    dreams = load_dreams(dreams_path)
    print(f"📊 Loaded {len(dreams)} dreams")
    
    # Clean dreams
    glymphatic = GlymphaticSystem(delta_threshold=100_000_000)
    cleaned = glymphatic.clean_dreams(dreams)
    
    # Show stats
    stats = glymphatic.get_stats()
    print(f"\n✅ Glymphatic Cleaning Complete:")
    print(f"  Processed: {stats['processed']}")
    print(f"  Kept: {stats['kept']} ({stats['keep_rate']:.1%})")
    print(f"  Filtered out: {stats['filtered_out']}")
    print(f"  Noise removed: {stats['noise_removed']}")
    
    # Save cleaned dreams
    output_path = Path("outputs/dreams_cleaned.json")
    glymphatic.save_cleaned_dreams(cleaned, output_path)
    
    print(f"\n🎯 Next: Feed cleaned dreams to Synaptic Pruner")
