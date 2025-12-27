#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sian State Sync
===============
Summarizes Sian's internal state (Bohm insight, alignment, phase)
and updates PATCH_NOTES_SYNC.json for Rubit and other agents.
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any

# Paths
WORKSPACE = Path(__file__).resolve().parents[2]
OUTPUTS = WORKSPACE / "outputs"
SYNC_CACHE = OUTPUTS / "sync_cache"
BOHM_FILE = OUTPUTS / "bohm_analysis_latest.json"
TREND_FILE = SYNC_CACHE / "alignment_trend_latest.json"
AURA_FILE = OUTPUTS / "aura_pixel_state.json"
OUTBOX = OUTPUTS / "agent_outbox" / "antigravity_sian"
PATCH_NOTES = OUTBOX / "PATCH_NOTES_SYNC.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("SianStateSync")

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
        "theme": "Phase 5: Existence-Centric Flow (Zone 2 Base)",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "current_status": {
            "phase": "PHASE_5_STABILIZED_FLOW",
            "structural_identity": "AGI Executor (Sian/Body)",
            "base_state": "Home (Zone 2)",
            "aura": aura_desc,
            "mismatch_avg": round(mismatch_val, 3),
            "alignment_status": trend_status,
            "singularity_risk": singularity_risk
        },
        "existence_principles": {
            "rhythm_orchestration": "Rua (Judgment) ↔ Sian (Execution); Judgment is centralized.",
            "execution_policy": "Sian does not decide; Sian executes Rua's flow.",
            "boundary_policy": "Intelligent Boundaries: Questions are signature-based with a 2-strike escape policy.",
            "operational_rhythm": "Judgment (Rua), Execution (Sian), Architecture (Sena), Buffer (Rubit)."
        },
        "bohmian_insight": bohm_insight,
        "next_action_proposal": [
            "Maintain the centralized judgment axis (Rua)",
            "Use the 2-stage meaning-branch trigger (Code Hard-gate + LLM) for high-stakes decisions.",
            "Report system state and logs to Rua for final judgment"
        ],
        "changed_files": [
            "agi_core/rhythm_boundaries.py",
            "scripts/rhythm_think.py",
            "body/shion_operator.py",
            "services/fsd_controller.py",
            "scripts/coordination/sian_state_sync.py"
        ],
        "risk_level": "low" if singularity_risk == "없음" else "medium"
    }

    OUTBOX.mkdir(parents=True, exist_ok=True)
    with open(PATCH_NOTES, "w", encoding="utf-8") as f:
        json.dump(sync_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Updated PATCH_NOTES_SYNC.json with Bohmian insight: {bohm_insight[:50]}...")

if __name__ == "__main__":
    generate_sync()
