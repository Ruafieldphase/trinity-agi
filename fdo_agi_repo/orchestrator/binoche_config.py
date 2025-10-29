"""
Binoche Decision Configuration

Phase 6i: Adaptive thresholds for BQI-based auto-decision

작성자: GitHub Copilot (Gitco)
날짜: 2025-10-28
"""

from typing import Dict, Any

# Phase 6i: Pattern-specific thresholds (learned from Phase 6f-6h)
PATTERN_THRESHOLDS = {
    "p1_e:neutral_r:exploration": {
        "auto_approve_confidence": 0.60,  # 88% approve, n=152 → High confidence
        "auto_approve_quality": 0.70,
        "description": "Exploration tasks with neutral emotion (most common, 56.7%)"
    },
    "p1_e:neutral_r:planning": {
        "auto_revise_confidence": 0.50,   # 83% revise, n=94 → Medium-high confidence
        "auto_revise_quality": 0.60,      # Lower quality bar for early correction
        "description": "Planning tasks (35.1%, high revise rate)"
    },
    "p3_e:neutral_r:exploration": {
        "auto_approve_confidence": 0.30,  # 100% approve but n=8 → Lower confidence due to small sample
        "auto_approve_quality": 0.65,     # Slightly lower for urgent tasks
        "description": "Urgent exploration tasks (3.0%, 100% approve)"
    },
    "p1_e:keywords_r:exploration": {
        "auto_approve_confidence": 0.25,  # 100% approve but n=5 → Very low confidence
        "auto_approve_quality": 0.75,     # Higher quality bar to compensate
        "description": "Keyword-driven exploration (1.9%, 100% approve)"
    },
    "p1_e:keywords_r:integration": {
        "auto_approve_confidence": 0.25,  # 100% approve but n=5 → Very low confidence
        "auto_approve_quality": 0.75,
        "description": "Keyword-driven integration (1.9%, 100% approve)"
    },
    "p1_e:neutral_r:integration": {
        "auto_approve_confidence": 0.15,  # 100% approve but n=1 → Minimal confidence
        "auto_approve_quality": 0.80,     # High quality bar required
        "description": "Integration tasks (rare, n=1)"
    },
    "p1_e:neutral_r:reflection": {
        "auto_approve_confidence": 0.20,  # 100% approve but n=2 → Very low confidence
        "auto_approve_quality": 0.80,
        "description": "Reflection tasks (rare, n=2)"
    },
    "p2_e:neutral_r:exploration": {
        "auto_approve_confidence": 0.15,  # 100% approve but n=1 → Minimal confidence
        "auto_approve_quality": 0.80,
        "description": "P2 exploration (rare, n=1)"
    }
}

# Default thresholds for unknown patterns
DEFAULT_THRESHOLDS = {
    "auto_approve_confidence": 0.70,  # Require high confidence for unknowns
    "auto_approve_quality": 0.80,     # Require high quality
    "auto_revise_confidence": 0.60,   # Medium confidence for revise
    "auto_revise_quality": 0.50,      # Lower quality bar for correction
    "description": "Unknown pattern (fallback to conservative thresholds)"
}

def get_pattern_threshold(pattern_key: str, threshold_type: str = "auto_approve_confidence") -> float:
    """
    Get adaptive threshold for specific pattern
    
    Args:
        pattern_key: BQI pattern (e.g., "p1_e:neutral_r:exploration")
        threshold_type: "auto_approve_confidence", "auto_approve_quality", 
                       "auto_revise_confidence", "auto_revise_quality"
    
    Returns:
        Threshold value (float)
    """
    pattern_config = PATTERN_THRESHOLDS.get(pattern_key, DEFAULT_THRESHOLDS)
    return pattern_config.get(threshold_type, DEFAULT_THRESHOLDS.get(threshold_type, 0.7))

def should_auto_approve(pattern_key: str, confidence: float, quality: float) -> bool:
    """
    Check if pattern + metrics meet auto-approve criteria
    
    Args:
        pattern_key: BQI pattern
        confidence: Binoche confidence (0.0-1.0)
        quality: Task quality (0.0-1.0)
    
    Returns:
        True if should auto-approve
    """
    conf_threshold = get_pattern_threshold(pattern_key, "auto_approve_confidence")
    qual_threshold = get_pattern_threshold(pattern_key, "auto_approve_quality")
    
    return confidence >= conf_threshold and quality >= qual_threshold

def should_auto_revise(pattern_key: str, confidence: float, quality: float, rhythm_phase: str) -> bool:
    """
    Check if pattern + metrics meet auto-revise criteria
    
    Args:
        pattern_key: BQI pattern
        confidence: Binoche confidence (0.0-1.0)
        quality: Task quality (0.0-1.0)
        rhythm_phase: Task rhythm (exploration/planning/etc.)
    
    Returns:
        True if should trigger auto-revise
    """
    # Planning tasks have specific auto-revise logic
    if rhythm_phase == "planning":
        conf_threshold = get_pattern_threshold(pattern_key, "auto_revise_confidence")
        qual_threshold = get_pattern_threshold(pattern_key, "auto_revise_quality")
        return confidence >= conf_threshold and quality >= qual_threshold
    
    return False

def get_pattern_info(pattern_key: str) -> Dict[str, Any]:
    """
    Get full configuration for pattern
    
    Args:
        pattern_key: BQI pattern
    
    Returns:
        Dict with thresholds and description
    """
    return PATTERN_THRESHOLDS.get(pattern_key, DEFAULT_THRESHOLDS)

def get_all_patterns() -> Dict[str, Dict[str, Any]]:
    """Get all pattern configurations"""
    return PATTERN_THRESHOLDS

if __name__ == "__main__":
    import json
    
    print("🎯 Binoche Adaptive Thresholds (Phase 6i)\n")
    
    # Test exploration pattern
    pattern = "p1_e:neutral_r:exploration"
    print(f"Pattern: {pattern}")
    print(f"  Auto-approve: confidence ≥ {get_pattern_threshold(pattern, 'auto_approve_confidence'):.2f}, quality ≥ {get_pattern_threshold(pattern, 'auto_approve_quality'):.2f}")
    print(f"  Should approve (conf=0.64, qual=0.85)? {should_auto_approve(pattern, 0.64, 0.85)}")
    print()
    
    # Test planning pattern
    pattern = "p1_e:neutral_r:planning"
    print(f"Pattern: {pattern}")
    print(f"  Auto-revise: confidence ≥ {get_pattern_threshold(pattern, 'auto_revise_confidence'):.2f}, quality ≥ {get_pattern_threshold(pattern, 'auto_revise_quality'):.2f}")
    print(f"  Should revise (conf=0.55, qual=0.85)? {should_auto_revise(pattern, 0.55, 0.85, 'planning')}")
    print()
    
    # Show all patterns
    print("All Pattern Thresholds:")
    for key, config in get_all_patterns().items():
        print(f"  {key}:")
        print(f"    Approve: conf ≥ {config.get('auto_approve_confidence', 'N/A')}, qual ≥ {config.get('auto_approve_quality', 'N/A')}")
        if 'auto_revise_confidence' in config:
            print(f"    Revise:  conf ≥ {config.get('auto_revise_confidence')}, qual ≥ {config.get('auto_revise_quality')}")
        print(f"    ({config['description']})")
        print()
