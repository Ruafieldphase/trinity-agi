#!/usr/bin/env python3
"""
Live Replay - Time Machine Test
================================
Replays historical conversation data by updating actual sensor files.
Alpha Background Self daemon will detect and react in real-time.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from workspace_root import get_workspace_root

# Configuration
WORKSPACE_ROOT = get_workspace_root()
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
LEDGER_FILE = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"

# Sensor Files (what Alpha monitors)
CORE_STATE = OUTPUTS_DIR / "core_state.json"
THOUGHT_STREAM = OUTPUTS_DIR / "thought_stream_latest.json"
RESONANCE_STATE = OUTPUTS_DIR / "resonance_expression_state.json"

def load_conversation_history(hours: int = 24) -> List[Dict]:
    """Load recent conversation data from ledger."""
    entries = []
    cutoff_time = datetime.now().timestamp() - (hours * 3600)
    
    try:
        with open(LEDGER_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    timestamp = entry.get('timestamp', '')
                    
                    # Parse timestamp
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if dt.timestamp() > cutoff_time:
                            entries.append(entry)
                    except:
                        pass
                except:
                    pass
    except Exception as e:
        print(f"Error loading ledger: {e}")
    
    return entries

def update_sensor_files(entry: Dict):
    """Update sensor files based on ledger entry."""
    entry_type = entry.get('type', '')
    metadata = entry.get('metadata', {})
    
    # Update Fear (Core State)
    fear = metadata.get('fear_level', 0.0)
    if fear > 0:
        core_data = {
            "fear": {"level": fear},
            "strategy": metadata.get('strategy', 'Unknown'),
            "timestamp": entry.get('timestamp')
        }
        with open(CORE_STATE, 'w') as f:
            json.dump(core_data, f)
    
    # Update Resonance (Thought Stream)
    resonance = metadata.get('resonance_score', 1.0)
    if entry_type == 'thought_stream':
        thought_data = {
            "delivery": {
                "resonance": resonance,
                "feeling": metadata.get('feeling', 'neutral')
            },
            "timestamp": entry.get('timestamp')
        }
        with open(THOUGHT_STREAM, 'w') as f:
            json.dump(thought_data, f)
    
    # Update Urgency (Resonance Expression)
    if 'urgency' in metadata or entry_type == 'resonance_expression':
        urgency = metadata.get('urgency', 'MEDIUM')
        resonance_data = {
            "last_status": urgency,
            "last_time": time.time()
        }
        with open(RESONANCE_STATE, 'w') as f:
            json.dump(resonance_data, f)

def run_time_machine(entries: List[Dict], speed: float = 10.0):
    """
    Replay conversation history in fast-forward.
    
    Args:
        entries: Ledger entries to replay
        speed: Playback speed multiplier (10.0 = 10x faster)
    """
    print("=" * 60)
    print("🕰️  Time Machine Test - Alpha Background Self")
    print("=" * 60)
    print(f"Replaying {len(entries)} events at {speed}x speed")
    print("Watch Alpha's logs: tail -f ~/agi/outputs/alpha_background_self.log")
    print("=" * 60)
    print()
    
    prev_time = None
    
    for i, entry in enumerate(entries):
        timestamp = entry.get('timestamp', '')
        msg_type = entry.get('type', 'unknown')
        
        # Calculate delay (fast-forwarded)
        if prev_time:
            try:
                current_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                prev_dt = datetime.fromisoformat(prev_time.replace('Z', '+00:00'))
                real_delay = (current_dt - prev_dt).total_seconds()
                fast_delay = max(0.1, real_delay / speed)  # Min 0.1s
                time.sleep(fast_delay)
            except:
                time.sleep(0.5)
        
        # Update sensor files
        update_sensor_files(entry)
        
        # Display progress
        metadata = entry.get('metadata', {})
        fear = metadata.get('fear_level', 0.0)
        
        print(f"[{i+1}/{len(entries)}] {timestamp[:19]} | {msg_type}")
        if fear > 0:
            print(f"   Fear: {fear:.2f}")
        
        prev_time = timestamp
    
    print()
    print("=" * 60)
    print("✅ Time Machine Replay Complete")
    print("=" * 60)
    print("Check Alpha's reaction in:")
    print("  - tail -f ~/agi/outputs/alpha_background_self.log")
    print("  - python3 ~/agi/scripts/alpha_status.py")

if __name__ == "__main__":
    import sys
    
    # Load last 24 hours of data
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    speed = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
    
    print(f"Loading last {hours} hours of conversation data...")
    data = load_conversation_history(hours)
    print(f"Found {len(data)} events")
    
    if len(data) == 0:
        print("No data to replay. Try increasing hours: python3 live_replay.py 48")
        sys.exit(1)
    
    print(f"\nStarting replay at {speed}x speed...")
    print("Press Ctrl+C to stop\n")
    
    try:
        run_time_machine(data, speed)
    except KeyboardInterrupt:
        print("\n\n🛑 Replay stopped by user")
