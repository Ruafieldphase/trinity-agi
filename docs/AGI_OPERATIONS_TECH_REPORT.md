# Trinity AGI Operations: Technical Report (skeleton)

Last updated: 2025-11-07

Purpose
- Document Trinity’s autonomous operations stack and how we measure autonomy, improvement, resilience, and safety during real operations.
- Serve as a living report: link to outputs, summarize last 24–72h, and record design/ablation notes.

System Overview
- Orchestrator: `fdo_agi_repo/orchestrator/pipeline.py`, `resonance_bridge.py`
- Autonomy loop: `scripts/autonomous_goal_generator.py`, `scripts/autonomous_goal_executor.py`
- Self-care: `fdo_agi_repo/orchestrator/self_care.py` (telemetry summarized via `scripts/update_self_care_metrics.ps1`)
- Glymphatic: `fdo_agi_repo/orchestrator/adaptive_glymphatic_system.py` (telemetry via `metrics_logger.py`)

Operational Telemetry
- Ledgers
  - Resonance: `fdo_agi_repo/memory/resonance_ledger.jsonl`
  - Glymphatic: `fdo_agi_repo/memory/glymphatic_ledger.jsonl`
- Summaries
  - Self-care: `outputs/self_care_metrics_summary.json`
  - Glymphatic: `outputs/glymphatic_metrics_latest.json`
  - Unified monitoring: `outputs/monitoring_metrics_latest.json`, `outputs/monitoring_dashboard_latest.html`

Measurement Axes (v0.1)
- Autonomy: no-touch completion rate; coverage (observed minutes / window)
- Improvement: replan rate↓, avg duration↓, success rate↑ (EWMA/CUSUM)
- Resilience: MTBF↑, MTTR↓, self-heal success↑ (planned vs unplanned reboot separated)
- Safety: resource throttles, killswitch hits, isolation success

Minimal Procedures
- Daily (manual)
  - `scripts/generate_monitoring_report.ps1 -WriteLatest -ExportJson -ExportCsv`
  - `scripts/update_self_care_metrics.ps1 -Hours 24 -Json -OpenSummary`
  - `scripts/update_glymphatic_metrics.ps1 -Hours 24 -OpenSummary`
- Optional (scheduled)
  - Goal monitor: `REGISTER_GOAL_MONITOR.ps1 -Register -IntervalMinutes 10 -ThresholdMinutes 15`

Evidence Template
- Window: [start/end, coverage%]
- Autonomy: success rate, no-touch% (trend)
- Improvement: avg duration (Δ%), replan (Δ%)
- Resilience: MTBF, MTTR, self-heal rate
- Safety: incidents, limit hits
- Notes/changes: tool/policy additions and pre/post impact

Open Items
- Add “Autonomous Improvement” section into unified dashboard
- Reboot markers (planned/unplanned) in ledgers for MTBF/MTTR clarity

This file is intentionally lightweight. Fill in links/metrics as runs accumulate.
