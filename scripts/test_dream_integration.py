"""
Test Dream Integration Pipeline

Validates the complete dream→memory pipeline:
1. Glymphatic cleaning
2. Synaptic pruning  
3. Memory consolidation

Author: AGI Self-Referential System
Date: 2025-11-05
"""

import json
from pathlib import Path


def test_dream_integration():
    """Test the complete dream integration pipeline."""
    
    print("🧪 Testing Dream Integration Pipeline\n")
    print("="*64)
    
    # Test 1: Check input
    print("\n📊 Test 1: Input Validation")
    dreams_path = Path("outputs/dreams.jsonl")
    assert dreams_path.exists(), "❌ dreams.jsonl not found"
    
    with open(dreams_path, "r", encoding="utf-8-sig") as f:
        dream_count = sum(1 for line in f if line.strip())
    
    print(f"✅ Found {dream_count} dreams")
    assert dream_count == 18, f"❌ Expected 18 dreams, got {dream_count}"
    
    # Test 2: Check glymphatic output
    print("\n🌊 Test 2: Glymphatic Cleaning")
    cleaned_path = Path("outputs/dreams_cleaned.json")
    assert cleaned_path.exists(), "❌ dreams_cleaned.json not found"
    
    with open(cleaned_path, "r", encoding="utf-8") as f:
        cleaned = json.load(f)
    
    print(f"✅ {len(cleaned)} dreams cleaned")
    assert len(cleaned) > 0, "❌ No dreams survived cleaning"
    assert all(d.get("glymphatic_cleaned") for d in cleaned), "❌ Not all dreams marked as cleaned"
    
    # Test 3: Check synaptic pruning
    print("\n🧠 Test 3: Synaptic Pruning")
    pruned_path = Path("outputs/memories_pruned.json")
    assert pruned_path.exists(), "❌ memories_pruned.json not found"
    
    with open(pruned_path, "r", encoding="utf-8") as f:
        memories = json.load(f)
    
    print(f"✅ {len(memories)} memories pruned")
    assert len(memories) > 0, "❌ No memories after pruning"
    
    # Validate memory structure
    required_fields = ["pattern_name", "frequency", "importance", "type", "category"]
    for mem in memories:
        for field in required_fields:
            assert field in mem, f"❌ Missing field '{field}' in memory"
    
    print(f"✅ All memories have required fields")
    
    # Test 4: Check integration data
    print("\n💾 Test 4: Integration Data")
    integration_path = Path("outputs/dream_integration_ready.json")
    assert integration_path.exists(), "❌ dream_integration_ready.json not found"
    
    with open(integration_path, "r", encoding="utf-8") as f:
        integration = json.load(f)
    
    assert "memories" in integration, "❌ No memories in integration data"
    assert "stats" in integration, "❌ No stats in integration data"
    
    stats = integration["stats"]
    print(f"✅ Integration stats:")
    print(f"   Dreams input: {stats['dreams_input']}")
    print(f"   Dreams cleaned: {stats['dreams_cleaned']}")
    print(f"   Memories pruned: {stats['memories_pruned']}")
    
    # Test 5: Quality checks
    print("\n🎯 Test 5: Quality Checks")
    
    # Check importance distribution
    importances = [m["importance"] for m in memories]
    avg_importance = sum(importances) / len(importances)
    print(f"✅ Average importance: {avg_importance:.2f}")
    assert avg_importance >= 0.5, f"❌ Low average importance: {avg_importance}"
    
    # Check frequency distribution
    frequencies = [m["frequency"] for m in memories]
    total_freq = sum(frequencies)
    print(f"✅ Total frequency: {total_freq}")
    assert total_freq > 0, "❌ Zero total frequency"
    
    # Check categories
    categories = set(m["category"] for m in memories)
    print(f"✅ Found {len(categories)} categories: {', '.join(categories)}")
    
    # Test 6: Compression ratio
    print("\n📐 Test 6: Compression Ratio")
    
    # Count total patterns in cleaned dreams
    total_patterns = sum(len(d.get("patterns", [])) for d in cleaned)
    compression_ratio = len(memories) / total_patterns if total_patterns > 0 else 0
    
    print(f"✅ Compression: {total_patterns} patterns → {len(memories)} memories ({compression_ratio:.1%})")
    assert compression_ratio < 0.5, f"❌ Low compression: {compression_ratio:.1%}"
    
    # Final summary
    print("\n" + "="*64)
    print("🎉 All Tests Passed!")
    print("="*64)
    print(f"\n✅ Dream Integration Pipeline is working correctly!")
    print(f"\n📊 Final Stats:")
    print(f"   Input: {dream_count} dreams")
    print(f"   Cleaned: {len(cleaned)} dreams")
    print(f"   Output: {len(memories)} memories")
    print(f"   Compression: {compression_ratio:.1%}")
    print(f"   Avg Importance: {avg_importance:.2f}")
    
    return True


if __name__ == "__main__":
    try:
        test_dream_integration()
        print("\n✅ Test suite completed successfully!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
