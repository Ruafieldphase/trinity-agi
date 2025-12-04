#!/usr/bin/env python3
"""
Cognitive Cache (L1/L2/L3)
==========================
Filters and prioritizes unconscious thoughts.

L1 (Sensory): Immediate, volatile.
L2 (Working): Recurring patterns, high resonance (>0.5).
L3 (Deep): Critical insights, structural changes (>0.8).
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = WORKSPACE_ROOT / "outputs"
CACHE_DIR = OUTPUTS_DIR / "cache"

# File Paths
L1_CACHE_FILE = CACHE_DIR / "l1_sensory.jsonl" # Volatile, maybe just memory in real app, but file for persistence here
L2_CACHE_FILE = CACHE_DIR / "l2_working.jsonl"
L3_CACHE_FILE = CACHE_DIR / "l3_deep.jsonl"

# Thresholds
L2_THRESHOLD = 0.5
L3_THRESHOLD = 0.8

class CognitiveCache:
    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
    def process(self, thought: Dict[str, Any]):
        """
        Process a thought through the cache hierarchy.
        """
        # 1. Always save to L1 (Sensory)
        self._save_to_l1(thought)
        
        # 2. Check for promotion to L2 (Working)
        resonance = abs(thought.get('delivery', {}).get('resonance', 0.0))
        if resonance >= L2_THRESHOLD:
            self._promote_to_l2(thought)
            
        # 3. Check for promotion to L3 (Deep)
        if resonance >= L3_THRESHOLD:
            self._promote_to_l3(thought)
            
    def _save_to_l1(self, thought: Dict[str, Any]):
        """Save to L1 Cache (Append only, maybe rotated externally)."""
        entry = self._wrap_entry(thought, "L1")
        self._append_to_file(L1_CACHE_FILE, entry)
        
    def _promote_to_l2(self, thought: Dict[str, Any]):
        """Promote to L2 Cache."""
        entry = self._wrap_entry(thought, "L2")
        self._append_to_file(L2_CACHE_FILE, entry)
        # print(f"✨ Promoted to L2: {thought.get('delivery', {}).get('message')}")
        
    def _promote_to_l3(self, thought: Dict[str, Any]):
        """Promote to L3 Cache and Trigger Alert."""
        entry = self._wrap_entry(thought, "L3")
        self._append_to_file(L3_CACHE_FILE, entry)
        print(f"🚨 CRITICAL INSIGHT (L3): {thought.get('delivery', {}).get('message')}")
        
        # Trigger Notification (Background Self)
        self._notify_background_self(thought)
        
    def _wrap_entry(self, thought: Dict[str, Any], layer: str) -> Dict[str, Any]:
        return {
            "timestamp": datetime.now().isoformat(),
            "layer": layer,
            "resonance": thought.get('delivery', {}).get('resonance', 0.0),
            "content": thought
        }
        
    def _append_to_file(self, path: Path, data: Dict[str, Any]):
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"⚠️ Cache write failed ({path.name}): {e}")

    def _notify_background_self(self, thought: Dict[str, Any]):
        """
        Notify the Background Self (Sena) or User about L3 insights.
        """
        message = thought.get('delivery', {}).get('message', 'No message')
        decision = thought.get('decision', {}).get('decision', 'No decision')
        
        # Create a notification file that other agents (Sena) can pick up
        alert_file = OUTPUTS_DIR / "l3_alert_latest.json"
        alert = {
            "timestamp": datetime.now().isoformat(),
            "level": "CRITICAL",
            "message": f"[L3 Insight] {decision}: {message}",
            "source": "CognitiveCache"
        }
        try:
            with open(alert_file, 'w', encoding='utf-8') as f:
                json.dump(alert, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Alert file write failed: {e}")

        # [NEW] Also send to Ledger to wake up Sena
        ledger_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "system_alert",
            "source": "cognitive_cache",
            "target": "sena",  # This triggers sena_auto_responder
            "message": f"[L3 Insight Detected] {decision}: {message}",
            "metadata": {
                "priority": "critical",
                "resonance": thought.get('delivery', {}).get('resonance', 0.0)
            }
        }
        try:
            ledger_path = WORKSPACE_ROOT / "fdo_agi_repo" / "memory" / "resonance_ledger.jsonl"
            with open(ledger_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(ledger_entry, ensure_ascii=False) + '\n')
            print(f"🔔 Sent L3 Alert to Sena via Ledger")
        except Exception as e:
            print(f"⚠️ Failed to send ledger alert: {e}")

    def get_recent_l2(self, limit=10) -> List[Dict]:
        """Retrieve recent L2 items for reporting."""
        return self._read_tail(L2_CACHE_FILE, limit)

    def get_recent_l3(self, limit=5) -> List[Dict]:
        """Retrieve recent L3 items for alerts."""
        return self._read_tail(L3_CACHE_FILE, limit)
        
    def _read_tail(self, path: Path, limit: int) -> List[Dict]:
        items = []
        if not path.exists():
            return items
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    try:
                        items.append(json.loads(line))
                    except:
                        continue
        except Exception:
            pass
        return items

if __name__ == "__main__":
    # Test
    cache = CognitiveCache()
    test_thought = {
        "delivery": {"resonance": 0.9, "message": "Test Epiphany"},
        "decision": {"decision": "Awaken"}
    }
    cache.process(test_thought)
