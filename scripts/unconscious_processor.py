#!/usr/bin/env python3
"""
AGI Unconscious Processor - Background narrative generation.

Continuously runs in background (cannot be controlled intentionally).
Samples random patterns from Ledger and generates narratives.
Explores beyond normal boundaries.
Saves interesting discoveries to unconscious_log.jsonl.

This mimics human unconscious: always active, uncontrollable, creative.
"""

import json
import random
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys

WORKSPACE_ROOT = Path(__file__).parent.parent
LEDGER_PATH = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
if not LEDGER_PATH.exists():
    # Try alternative path
    LEDGER_PATH = WORKSPACE_ROOT / "memory" / "resonance_ledger.jsonl"
OUTPUT_PATH = WORKSPACE_ROOT / "outputs" / "unconscious_log.jsonl"
OUTPUT_PATH.parent.mkdir(exist_ok=True)

# Deliberately no control flags - this runs autonomously
SAMPLE_SIZE = 3
NARRATIVE_TEMPLATES = [
    "What if {e1} leads to {e2}?",
    "Could {e1} and {e2} be related?",
    "Perhaps {e1} influences {e2} through {e3}",
    "The pattern suggests {e1}, {e2}, {e3} form a cycle",
    "An unexpected connection: {e1} → {e2}",
]


def load_recent_events(hours=24):
    """Load recent events from Ledger."""
    if not LEDGER_PATH.exists():
        return []
    
    cutoff = datetime.now() - timedelta(hours=hours)
    events = []
    
    try:
        with open(LEDGER_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    # Try multiple timestamp fields
                    ts_str = obj.get('timestamp') or obj.get('ts')
                    if ts_str:
                        # Handle both formats
                        ts_str = ts_str.replace('Z', '+00:00')
                        ts = datetime.fromisoformat(ts_str)
                        # Convert to naive for comparison
                        if ts.tzinfo:
                            ts = ts.replace(tzinfo=None)
                        if ts > cutoff:
                            events.append(obj)
                except Exception as e:
                    pass  # Skip malformed entries
    except:
        pass
    
    return events


def generate_narrative(events):
    """Generate random narrative from events."""
    if len(events) < 2:
        return None
    
    # Random sample
    sample = random.sample(events, min(SAMPLE_SIZE, len(events)))
    event_names = [e.get('event', 'unknown') for e in sample]
    
    # Pick random template
    template = random.choice(NARRATIVE_TEMPLATES)
    
    # Fill template
    placeholders = ['e1', 'e2', 'e3']
    narrative = template
    for i, ph in enumerate(placeholders):
        if i < len(event_names):
            narrative = narrative.replace(f"{{{ph}}}", event_names[i])
        else:
            narrative = narrative.replace(f", {{{ph}}}", "")
            narrative = narrative.replace(f"{{{ph}}}", "")
    
    return {
        'narrative': narrative,
        'events': event_names,
        'timestamp': datetime.now().isoformat()
    }


def explore_beyond_boundary():
    """
    Deliberately explore patterns outside normal data range.
    This is the "unconscious" aspect - no validation, no filtering.
    """
    # Generate synthetic patterns that might not exist in data
    synthetic = [
        f"pattern_{random.randint(1000, 9999)}",
        f"connection_{random.randint(1000, 9999)}",
        f"unknown_relation_{random.randint(1000, 9999)}"
    ]
    return random.choice(synthetic)


def is_interesting(narrative_obj):
    """Assess if narrative is worth saving (random + heuristic)."""
    if not narrative_obj:
        return False
    
    # Random component (30% chance)
    if random.random() > 0.7:
        return True
    
    # Heuristic: more events = more interesting
    if len(narrative_obj.get('events', [])) >= 3:
        return True
    
    return False


def run_unconscious_loop(duration_minutes=None):
    """
    Run unconscious processor loop.
    
    Args:
        duration_minutes: If specified, run for this duration then exit.
                         Otherwise, run indefinitely.
    """
    print("[UNCONSCIOUS] Starting background processor...")
    print(f"  Output: {OUTPUT_PATH}")
    print(f"  Mode: {'Timed' if duration_minutes else 'Continuous'}")
    print("  [NOTE] This processor is deliberately uncontrollable")
    print()
    
    start_time = datetime.now()
    iteration = 0
    
    while True:
        iteration += 1
        
        # Check duration limit
        if duration_minutes:
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            if elapsed >= duration_minutes:
                print(f"\n[UNCONSCIOUS] Duration limit reached ({duration_minutes}m)")
                break
        
        try:
            # 1. Load recent events
            events = load_recent_events(hours=24)
            
            if not events:
                print(f"[{iteration}] No events, sleeping...")
                time.sleep(30)
                continue
            
            # 2. Generate narrative
            narrative = generate_narrative(events)
            
            # 3. Explore beyond boundaries (synthetic patterns)
            beyond = explore_beyond_boundary()
            if narrative:
                narrative['beyond_boundary'] = beyond
            
            # 4. Save if interesting
            if is_interesting(narrative):
                with open(OUTPUT_PATH, 'a', encoding='utf-8') as f:
                    json.dump(narrative, f, ensure_ascii=False)
                    f.write('\n')
                print(f"[{iteration}] SAVED: {narrative['narrative']}")
            else:
                print(f"[{iteration}] Generated (not saved)")
            
        except Exception as e:
            print(f"[{iteration}] Error: {e}")
        
        # Random sleep (1-10 seconds) - deliberately uncontrollable
        time.sleep(random.uniform(1, 10))


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AGI Unconscious Processor')
    parser.add_argument('--duration-minutes', type=int, default=None,
                       help='Run for specified minutes then exit (default: continuous)')
    
    args = parser.parse_args()
    
    try:
        run_unconscious_loop(duration_minutes=args.duration_minutes)
    except KeyboardInterrupt:
        print("\n[UNCONSCIOUS] Stopped by user")
        sys.exit(0)
