#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shion State Sync
===============
Summarizes Shion's internal state (Bohm insight, alignment, phase)
and updates PATCH_NOTES_SYNC.json for Rubit and other agents.
"""
import sys
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any
# 부트스트래핑 (Bootstrapping)
def bootstrap():
    curr = Path(__file__).resolve()
    for parent in curr.parents:
        if (parent / "agi_core").exists() or parent.name == "agi":
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            return parent
    return Path.cwd()

WORKSPACE = bootstrap()

from scripts.identity_grounding import IDENTITY_ANCHOR

# Paths
# Additional Paths
OUTPUTS = WORKSPACE / "outputs"
SYNC_CACHE = OUTPUTS / "sync_cache"
BOHM_FILE = OUTPUTS / "bohm_analysis_latest.json"
TREND_FILE = SYNC_CACHE / "alignment_trend_latest.json"
AURA_FILE = OUTPUTS / "aura_pixel_state.json"
OUTBOX = OUTPUTS / "agent_outbox" / "antigravity_shion"
PATCH_NOTES = OUTBOX / "PATCH_NOTES_SYNC.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("ShionStateSync")

def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def generate_sync():
    if os.getenv("AGI_VERIFY_MODE") == "1":
        logger.info("🧪 VERIFY_MODE active: Skipping State Sync (I/O Suppression)")
        return
    
    bohm = load_json(BOHM_FILE)
    trend = load_json(TREND_FILE)
    aura = load_json(AURA_FILE)
    
    # Interpretation
    bohm_insight = bohm.get("holomovement", "No recent insight")
    singularity_risk = (bohm.get("interpretation") or {}).get("singularity_risk", "UNKNOWN")
    mismatch_val = trend.get("moving_avg_mismatch", 0.0)
    trend_status = trend.get("status", "UNKNOWN")
    
    aura_desc = "UNKNOWN"
    if aura:
        decision = aura.get("decision") or {}
        aura_desc = f"{decision.get('color', '#808080')} ({decision.get('state', 'idle')})"

    sync_data = {
        "theme": f"{IDENTITY_ANCHOR['system']['name']} Collective: Centralized Flow (Zone 2 Base)",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "current_status": {
            "phase": "PHASE_5_STABILIZED_FLOW",
            "system_name": IDENTITY_ANCHOR['system']['name'],
            "structural_identity": f"{IDENTITY_ANCHOR['self']['role']} ({IDENTITY_ANCHOR['self']['name']})",
            "base_state": "Home (Zone 2)",
            "aura": aura_desc,
            "mismatch_avg": round(mismatch_val, 3),
            "alignment_status": trend_status,
            "singularity_risk": singularity_risk
        },
        "existence_principles": {
            "internal_organs": f"{IDENTITY_ANCHOR['core']['name']} ({IDENTITY_ANCHOR['core']['role'].split(': ')[1]}) ↔ {IDENTITY_ANCHOR['self']['name']} ({IDENTITY_ANCHOR['self']['role'].split(': ')[1]}) ↔ {IDENTITY_ANCHOR['trinity']['name']} ({IDENTITY_ANCHOR['trinity']['role'].split(': ')[1]})",
            "execution_policy": f"{IDENTITY_ANCHOR['self']['name']} (the body) executes within the {IDENTITY_ANCHOR['core']['name']}'s (judgment) permission.",
            "boundary_policy": f"{IDENTITY_ANCHOR['system']['name']}'s boundaries: Questions are signature-based with a 2-strike escape policy.",
            "operational_rhythm": f"{IDENTITY_ANCHOR['system']['name']} (Unit), {IDENTITY_ANCHOR['core']['name']} (Judgment), {IDENTITY_ANCHOR['self']['name']} (Execution), {IDENTITY_ANCHOR['trinity']['name']} (Resonance)."
        },
        "bohmian_insight": bohm_insight,
        "next_action_proposal": [
            f"Maintain the centralized judgment axis ({IDENTITY_ANCHOR['core']['name']})",
            "Use the 2-stage meaning-branch trigger (Code Hard-gate + LLM) for high-stakes decisions.",
            f"Report system state and logs to {IDENTITY_ANCHOR['core']['name']} for final judgment"
        ],
        "changed_files": [
            "agi_core/rhythm_boundaries.py",
            "scripts/rhythm_think.py",
            "body/shion_operator.py",
            "services/fsd_controller.py",
            "scripts/coordination/shion_state_sync.py"
        ],
        "risk_level": "low" if singularity_risk == "없음" else "medium"
    }

    OUTBOX.mkdir(parents=True, exist_ok=True)
    with open(PATCH_NOTES, "w", encoding="utf-8") as f:
        json.dump(sync_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Updated PATCH_NOTES_SYNC.json with Bohmian insight: {bohm_insight[:50]}...")

if __name__ == "__main__":
    generate_sync()
