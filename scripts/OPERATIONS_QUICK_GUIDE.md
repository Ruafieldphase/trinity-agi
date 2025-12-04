# Operations Quick Guide (ASCII)

This guide lists common runbooks and one‑liners. All commands are ASCII‑safe and work on Windows PowerShell.

---

## Start Services

- Start Phase 5 system (queue + web):
  - `scripts/start_phase5_system.ps1`
- Ensure RPA worker running (single instance):
  - `scripts/ensure_rpa_worker.ps1 -EnforceSingle -MaxWorkers 1`
- Quick status (ports, health, perf digest):
  - `scripts/quick_status.ps1 -Perf`

## Performance Dashboard

- Generate 7‑day dashboard, open, export JSON/CSV, update latest:
  - `scripts/generate_performance_dashboard.ps1 -Days 7 -OpenDashboard -ExportJson -ExportCsv -WriteLatest`
- Filter by bands and respect in attention list:
  - `scripts/generate_performance_dashboard.ps1 -OnlyBands Needs -AttentionRespectsBands -WriteLatest`
- Adjust thresholds (defaults: ExcellentAt=90, GoodAt=70):
  - `scripts/generate_performance_dashboard.ps1 -ExcellentAt 92 -GoodAt 75`
- Profiles (shortcuts):
  - Daily ops: `scripts/dashboard_ops_daily.ps1 -Open`
  - Focus (needs attention): `scripts/dashboard_ops_focus.ps1 -Open`
- Validate exported data (structure/types):
  - `scripts/validate_performance_dashboard.ps1 -VerboseOutput`
- Latest artifacts:
  - `outputs/performance_dashboard_latest.md`
  - `outputs/performance_metrics_latest.json`

## Monitoring Report

- 24h report and open:
  - `scripts/generate_monitoring_report.ps1 -Hours 24 -OpenMd`
- Report includes a Performance Snapshot from `outputs/performance_metrics_latest.json` when present.
- Optional channels (e.g., Local2 on port 18090):
  - Detected automatically and tracked separately
  - Console: Hidden by default with `-HideOptional`, shown without flag
  - MD Report: Shows CSV path when detected
  - HTML Dashboard: Displays with "OPTIONAL" badge in channel table
  - CSV: `outputs/monitoring_timeseries_optional_latest.csv`
  - Optional channels excluded from overall health/availability calculations

  ## Quick Status Smoke (strict SLO + trend)

  - Sanity + strict SLO verification with optional trend stability check:
    - `scripts/tests/quick_status_smoke.ps1 -Strict -Profile latency-first -CheckTrendStability`
  - Emit a one‑line JSON summary for downstream parsing when strict checks pass:
    - `scripts/tests/quick_status_smoke.ps1 -Strict -Profile ops-tight -ExplainStrict`
  - Docs: `docs/QUICK_STATUS_SMOKE_GUIDE.md`

## Autonomous Dashboard (Phase 5.5)

- Generate orchestration-aware dashboard (monitoring + routing + recovery):
  - `python scripts/generate_autonomous_dashboard.py --open`
  - Or use VS Code Task: "Monitoring: Generate Autonomous Dashboard (with Orchestration)"
- Output: `outputs/autonomous_dashboard_latest.html`
- Includes:
  - Channel health (EXCELLENT/GOOD/DEGRADED/POOR/OFFLINE)
  - Routing recommendations (Primary/Fallback selection)
  - Auto-recovery triggers (monitoring-based actions)
- Orchestration Bridge API:
  - `scripts/orchestration_bridge.py` (reads monitoring metrics)
  - Used by: FeedbackOrchestrator, auto_recover, routing helpers
- Auto-recovery with monitoring:
  - `fdo_agi_repo/scripts/auto_recover.py --server http://127.0.0.1:8091 --once`
  - Detects DEGRADED channels and triggers worker restart
  - Logs: `monitoring_triggered: true` in recovery JSON

## Daily Briefing

- Generate (opens report):
  - `scripts/generate_daily_briefing.ps1 -OpenReport`
- Register scheduled task (at logon):
  - `scripts/register_daily_briefing.ps1 -Install`

## Autostart (optional)

- Register Phase 5 services to start on login:
  - `scripts/register_phase5_autostart.ps1 -Install`
- Remove:
  - `scripts/register_phase5_autostart.ps1 -Uninstall`

## Encoding & Console

- Prefer UTF‑8 when saving from PowerShell:
  - `Out-File -Encoding UTF8`
- Set UTF‑8 for Python output (current session):
  - `$env:PYTHONIOENCODING = 'utf-8'`

---

See also: `MONITORING_QUICKSTART.md`, `OPERATIONS_GUIDE.md`, `CURRENT_SYSTEM_STATUS.md`, and `docs/PERFORMANCE_DASHBOARD_QUICK_REF.md`.

## Lumen Gateway Probe

- Run probe (writes JSONL + latest digest):
  - `scripts/run_lumen_probe.ps1 -Attempts 3 -BackoffMs 300 -TimeoutSec 8 -Tag "manual"`
- Open latest digest after run:
  - `scripts/run_lumen_probe.ps1 -OpenLatest`
- Scheduled (existing):
  - `scripts/register_lumen_probe_task.ps1 -Register -Time "09:00"`
- Latest artifacts:
  - `outputs/lumen_probe_log.jsonl` (append‑only)
  - `outputs/lumen_probe_latest.md`, `outputs/lumen_probe_latest.json`

## Lumen Probe Summary

- Summarize last 24h and open:
  - `scripts/generate_lumen_probe_summary.ps1 -Hours 24 -OpenMd`
- Outputs:
  - `outputs/lumen_probe_summary_latest.md`
  - `outputs/lumen_probe_summary_latest.json`

## VS Code Tasks

- Monitoring: Quick Status (-Perf)
- Monitoring: Generate Report (24h)
- Monitoring: Open Latest Report (MD)
- Monitoring: Open Dashboard (HTML)
- Performance: Ops Daily / Ops Focus / Validate Dashboard
- Lumen: Probe Now / Summary / Register / Unregister

Open with Ctrl+Shift+P, then run: `Tasks: Run Task`.
