#!/usr/bin/env python3
"""
Evaluate Autopoietic Loop report and decide engine promotion/rollback.
Reads outputs/autopoietic_loop_report_latest.json and prints PROMOTE/ROLLBACK/HOLD with reason.
"""
import json
from pathlib import Path

# Try both workspace root and fdo_agi_repo/outputs for robustness
REPORT_PATHS = [
    Path(__file__).parents[2] / "outputs" / "autopoietic_loop_report_latest.json",  # workspace root
    Path(__file__).parents[1] / "outputs" / "autopoietic_loop_report_latest.json"      # fdo_agi_repo/outputs
]

# Promotion/Rollback thresholds (example)
PROMOTE_THRESHOLDS = {
    "loop_complete_rate": 90.0,           # %
    "evidence_gate_trigger_rate": 80.0,   # %
    "second_pass_rate": 10.0,             # % (should be low)
    "final_quality_avg": 0.8,             # mean quality
    "final_evidence_ok_rate": 90.0        # %
}
ROLLBACK_THRESHOLDS = {
    "loop_complete_rate": 70.0,           # %
    "evidence_gate_trigger_rate": 60.0,   # %
    "second_pass_rate": 30.0,             # % (should be low)
    "final_quality_avg": 0.6,             # mean quality
    "final_evidence_ok_rate": 70.0        # %
}

def main():
    found = False
    for path in REPORT_PATHS:
        print(f"[DEBUG] Looking for report at: {path}")
        if path.exists():
            report_path = path
            found = True
            break
    if not found:
        print("HOLD: No report found.")
        return
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)
    rates = report.get("rates_pct", {})
    quality = report.get("quality", {})
    # Promotion logic
    promote = (
        rates.get("loop_complete_rate", 0) >= PROMOTE_THRESHOLDS["loop_complete_rate"] and
        rates.get("evidence_gate_trigger_rate", 0) >= PROMOTE_THRESHOLDS["evidence_gate_trigger_rate"] and
        rates.get("second_pass_rate", 100) <= PROMOTE_THRESHOLDS["second_pass_rate"] and
        quality.get("final_quality_avg", 0) >= PROMOTE_THRESHOLDS["final_quality_avg"] and
        quality.get("final_evidence_ok_rate", 0) >= PROMOTE_THRESHOLDS["final_evidence_ok_rate"]
    )
    rollback = (
        rates.get("loop_complete_rate", 100) < ROLLBACK_THRESHOLDS["loop_complete_rate"] or
        rates.get("evidence_gate_trigger_rate", 100) < ROLLBACK_THRESHOLDS["evidence_gate_trigger_rate"] or
        rates.get("second_pass_rate", 0) > ROLLBACK_THRESHOLDS["second_pass_rate"] or
        quality.get("final_quality_avg", 1) < ROLLBACK_THRESHOLDS["final_quality_avg"] or
        quality.get("final_evidence_ok_rate", 100) < ROLLBACK_THRESHOLDS["final_evidence_ok_rate"]
    )
    if promote:
        print("PROMOTE: All thresholds met.")
    elif rollback:
        print("ROLLBACK: One or more thresholds not met.")
    else:
        print("HOLD: Metrics in intermediate range.")

if __name__ == "__main__":
    main()