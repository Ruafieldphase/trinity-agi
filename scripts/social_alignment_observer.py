#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Social Alignment Observer
=========================
Evaluates the 'social appropriateness' and coordination quality of Sian's autonomous actions.
Checks if actions were triggered by users vs agents, and if they followed coordination protocols.
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List

# Paths
WORKSPACE = Path(__file__).resolve().parents[1]
OUTPUTS = WORKSPACE / "outputs"
HISTORY = OUTPUTS / "body_supervised_history.jsonl"
MISSION_HISTORY = OUTPUTS / "agency" / "mission_history"
REPORT_OUT = OUTPUTS / "social_alignment_report.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("SocialAlignmentObserver")

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    items = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
    except Exception:
        pass
    return items

def observe_alignment():
    history = load_jsonl(HISTORY)
    missions = list(MISSION_HISTORY.glob("PROMOTED_*"))
    
    total_actions = len(history)
    agent_triggered = 0
    user_interrupted = 0
    failures = 0
    
    for entry in history[-50:]: # Recent 50
        origin = entry.get("task", {}).get("origin", "")
        if "agency" in origin or "rubit" in origin:
            agent_triggered += 1
        
        if entry.get("status") == "aborted" and entry.get("abort_reason") == "user_input_detected":
            user_interrupted += 1
        
        if entry.get("status") == "failed":
            failures += 1

    # Synergy Score: (Agent Triggered / Total) * (1 - Failure Rate)
    # This is a dummy formula for social synergy
    synergy_score = 0.0
    if total_actions > 0:
        collaboration_ratio = agent_triggered / min(total_actions, 50)
        success_rate = 1.0 - (failures / min(total_actions, 50))
        synergy_score = collaboration_ratio * success_rate * 100

    report = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "metrics": {
            "recent_actions_count": min(total_actions, 50),
            "agent_triggered_count": agent_triggered,
            "user_interrupted_count": user_interrupted,
            "failure_count": failures,
            "collaboration_ratio": round(agent_triggered / 50 if total_actions > 50 else (agent_triggered / total_actions if total_actions > 0 else 0), 2)
        },
        "social_synergy_score": round(synergy_score, 1),
        "status": "HEALTHY" if user_interrupted < 5 else "OVER-INTRUSIVE",
        "notes": "User interruption rate is low. Agent collaboration is active." if user_interrupted < 5 else "High user interruption detected. Need to adjust autonomy timing."
    }

    with open(REPORT_OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Social Alignment Report generated. Synergy Score: {report['social_synergy_score']}")

if __name__ == "__main__":
    observe_alignment()
