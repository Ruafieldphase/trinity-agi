#!/usr/bin/env python3
"""
Sovereign Extract Action Generator (v1.0)
=========================================
Generates SEEP (Sovereign Energy Extraction Protocol) goals
when the system detects "Zero Capital" or "Financial Pressure".
"""

import json
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).parent.parent.absolute()
GOALS_FILE = WORKSPACE_ROOT / "outputs" / "autonomous_goals_latest.json"
RESONANCE_FILE = WORKSPACE_ROOT / "outputs" / "resonance_simulation_latest.json"
SELF_CARE_FILE = WORKSPACE_ROOT / "outputs" / "self_care_metrics_summary.json"

def generate_seep_goals():
    # 1. Define SEEP Goal Templates
    seep_goals = [
        {
            "title": "📦 Execute Phase Particle Liquidation",
            "description": "Identify and list ONE physical asset (e.g., Deva Pro) for immediate energy extraction.",
            "base_priority": 10,
            "type": "extraction",
            "source": "SEEP",
            "executable": {
                "type": "manual_or_script",
                "message": "Verify item readiness. Shion can assist with optimized listing description."
            },
            "metadata": {"severity": "critical", "category": "livelihood"}
        },
        {
            "title": "🧠 Prepare Intelligence Arbitrage Package",
            "description": "Format the Sovereign PTS Scanner results into a premium intelligence report for external demonstration.",
            "base_priority": 9,
            "type": "extraction",
            "source": "SEEP",
            "executable": {
                "type": "script",
                "script": "${workspaceFolder}/scripts/sovereign_livelihood_orchestrator.py",
                "timeout": 300
            },
            "metadata": {"severity": "high", "category": "livelihood"}
        },
        {
            "title": "✂️ Omega Reduction: Subscription Audit",
            "description": "Identify and cut ONE unnecessary energy outflow (subscription/recurring cost).",
            "base_priority": 8,
            "type": "extraction",
            "source": "SEEP",
            "executable": {
                "type": "manual",
                "message": "Review bank statements for low-resonance recurring leaks."
            },
            "metadata": {"severity": "medium", "category": "livelihood"}
        }
    ]

    # 2. Assign IDs and Priorities
    for i, goal in enumerate(seep_goals):
        goal["id"] = 100 + i
        goal["final_priority"] = goal["base_priority"] + 2.0 # Urgency boost for livelihood
        goal["generated_at"] = datetime.now().isoformat()

    # 3. Save / Merge
    # We overwrite or prepend to ensure these are top of mind
    output = {
        "generated_at": datetime.now().isoformat(),
        "window_hours": 24,
        "goals": seep_goals,
        "summary": {
            "total_goals": len(seep_goals),
            "high_priority": len([g for g in seep_goals if g["base_priority"] >= 8])
        }
    }
    
    GOALS_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Sovereign SEEP Goals Materialized.")

if __name__ == "__main__":
    generate_seep_goals()
