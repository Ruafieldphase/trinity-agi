#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proactive Reporter
==================
Monitors critical health metrics (Alignment, Bohmian Singularity)
and issues proactive alerts if the system drifts towards dangerous zones.
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any
from workspace_root import get_workspace_root

# Paths
WORKSPACE = get_workspace_root()
OUTPUTS = WORKSPACE / "outputs"
SYNC_CACHE = OUTPUTS / "sync_cache"
BOHM_FILE = OUTPUTS / "bohm_analysis_latest.json"
TREND_FILE = SYNC_CACHE / "alignment_trend_latest.json"
URGENT_REPORT = OUTPUTS / "URGENT_REPORT.md"
URGENT_SIGNAL = OUTPUTS / "urgent_signal.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("ProactiveReporter")

def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def check_health():
    bohm = load_json(BOHM_FILE)
    trend = load_json(TREND_FILE)
    
    singularity_risk = (bohm.get("interpretation") or {}).get("singularity_risk", "UNKNOWN")
    trend_status = trend.get("status", "UNKNOWN")
    mismatch_avg = trend.get("moving_avg_mismatch", 0.0)
    
    triggers = []
    
    # Thresholds
    if trend_status == "DIVERGING" or mismatch_avg > 0.8:
        triggers.append(f"Statistical Alignment DIVERGING (Mismatch: {mismatch_avg:.2f})")
    
    if singularity_risk.upper() in ["HIGH", "CRITICAL"]:
        triggers.append(f"Bohmian Singularity Risk: {singularity_risk}")

    if triggers:
        issue_alert(triggers, bohm, trend)
    else:
        # Clear signal if health is restored
        if URGENT_SIGNAL.exists():
            URGENT_SIGNAL.unlink(missing_ok=True)
            logger.info("Health restored. Urgent signal cleared.")

def issue_alert(triggers: list, bohm: dict, trend: dict):
    logger.warning(f"🚨 Proactive Alert Triggered: {', '.join(triggers)}")
    
    # 1. Generate Markdown Report
    report_lines = [
        "# 🚨 URGENT SYSTEM HEALTH REPORT (Proactive)",
        f"- **Timestamp (UTC)**: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "",
        "## Triggered Conditions",
    ]
    for t in triggers:
        report_lines.append(f"- {t}")
    
    report_lines.extend([
        "",
        "## Technical Context",
        f"- **Alignment Status**: {trend.get('status')}",
        f"- **Mismatch Avg**: {trend.get('moving_avg_mismatch')}",
        f"- **Bohm Interpretation**: {bohm.get('interpretation', {}).get('bohm_interpretation', 'N/A')}",
        "",
        "## Recommended Mitigation",
        "1. Temporarily activate Homeostasis Rest Gate.",
        "2. Review recent high-mismatch actions.",
        "3. Check for external stimulus overload."
    ])
    
    URGENT_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    
    # 2. Generate JSON Signal for Aura Pixel
    signal = {
        "timestamp": time.time(),
        "level": "CRITICAL",
        "triggers": triggers,
        "blink": True,
        "color": "#FF0000"
    }
    with open(URGENT_SIGNAL, "w", encoding="utf-8") as f:
        json.dump(signal, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    check_health()
