# Autopoietic Loop Verification

This document explains how the pipeline is instrumented to trace the Autopoietic Loop and how to verify it quickly.

## Mapping

- Folding → Thesis (context folding and initial reasoning)
- Unfolding → Antithesis (counter reasoning)
- Integration → Synthesis (integration and final draft)
- Symmetry → Decision + Correction (Binoche decision, Evidence Gate, Self-Correction)

## Ledger Events

The following events are appended to `fdo_agi_repo/memory/resonance_ledger.jsonl` per task:

- autopoietic_phase (phase=folding, stage=start, context_count)
- thesis_start / thesis_end (duration_sec, citations)
- autopoietic_phase (phase=folding, stage=end, duration_sec, citations)
- antithesis_start / antithesis_end (duration_sec)
- autopoietic_phase (phase=unfolding, stage=end, duration_sec)
- synthesis_start / synthesis_end (duration_sec, citations)
- autopoietic_phase (phase=integration, stage=end, duration_sec, citations)
- eval / rune
- autopoietic_phase (phase=symmetry, stage=start)
- binoche_enhanced_decision / binoche_decision / binoche_ab_comparison
- evidence_gate_triggered (when applicable)
- learning / second_pass (when applicable)
- autopoietic_phase (phase=symmetry, stage=end, duration_sec, evidence_gate_triggered, second_pass, final_quality, final_evidence_ok)

## Quick Report

Run the analysis script to generate a 24h report:

- Outputs:
  - `outputs/autopoietic_loop_report_latest.md`
  - `outputs/autopoietic_loop_report_latest.json`

The script can be invoked with the repo virtualenv or system Python.

## Interpreting Results

- Complete Loops should rise as new tasks run after this instrumentation.
- Symmetry duration reflects the time spent in decision and corrective paths.
- Final Evidence OK Rate should improve after Evidence Gate/self-correction when triggered.

## Next Steps

- Add scheduled execution alongside existing monitoring to trend Autopoietic Loop health over time.
- Correlate loop durations with quality improvements and A/B decision match rates.
