#!/usr/bin/env python3
"""
Historical Replay Test
======================
Replays historical states from resonance_ledger.jsonl to test Alpha Background Self's reaction.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

def load_historical_data(limit: int = 50) -> List[Dict]:
    """Load recent ledger entries."""
    entries = []
    try:
        with open(LEDGER_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    entries.append(json.loads(line))
                except:
                    pass
    except Exception as e:
        print(f"Error loading ledger: {e}")
    return entries

def simulate_alpha_reaction(entries: List[Dict]):
    """
    Feed entries to Alpha logic (simulated).
    We can't easily inject into the running daemon, so we'll simulate the logic here.
    """
    print(f"🎬 Starting Historical Replay ({len(entries)} events)")
    print("=" * 60)
    
    # Import Alpha logic locally
    sys.path.append(str(WORKSPACE_ROOT / "scripts"))
    from pattern_drift_detector import PatternDriftDetector
    
    detector = PatternDriftDetector()
    
    for i, entry in enumerate(entries):
        timestamp = entry.get('timestamp', 'Unknown')
        msg_type = entry.get('type', 'Unknown')
        metadata = entry.get('metadata', {})
        
        # Extract signals from metadata if available
        fear = metadata.get('fear_level', 0.0)
        resonance = metadata.get('resonance_score', 1.0)
        
        # Simulate sensor inputs
        signals = {
            'rhythm_resonance': resonance,
            'fear_level': fear,
            'urgency_level': 0.5, # Default
            'reflex_frequency': 0.0
        }
        
        # Detect drift
        drift_score = detector.calculate_drift_score(signals)
        state = detector.determine_state(drift_score)
        
        # Output
        print(f"[{timestamp}] Event: {msg_type}")
        print(f"   Signals: Fear={fear:.2f}, Resonance={resonance:.2f}")
        print(f"   Alpha: Drift={drift_score:.2f} → State={state}")
        
        if state == 'INTERVENTION':
            print("   🚨 INTERVENTION TRIGGERED!")
        
        print("-" * 40)
        time.sleep(0.1) # Fast forward

if __name__ == "__main__":
    import sys
    data = load_historical_data(limit=20)
    simulate_alpha_reaction(data)
