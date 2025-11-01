# Agent Instructions (for human/AI contributors)

This repository supports multi‑agent handoffs. Follow this guide to continue work safely and consistently.

- Start Here
  - Read: `docs/AGENT_HANDOFF.md` (latest context, next actions)
  - Read: `docs/AGI_RESONANCE_INTEGRATION_PLAN.md` (project plan; update as you go)

- Conventions
  - Encoding: UTF‑8 (without BOM). Avoid emojis in PowerShell console output.
  - Tests: default scope is limited via `pytest.ini` to core suites. Run: `python -m pytest -q`.
  - Style: keep changes minimal and targeted; prefer small, composable helpers.
  - Docs: update plan and handoff docs whenever scope/status changes.

- High‑value Entry Points
  - Resonance integration: `fdo_agi_repo/orchestrator/resonance_bridge.py`, `fdo_agi_repo/orchestrator/pipeline.py`
  - Validators and monitors: `scripts/validate_performance_dashboard.ps1`, `scripts/generate_monitoring_report.ps1`
  - Dashboard UI text: `scripts/monitoring_dashboard_template.html`

- Quick Commands
  - Core tests: `python -m pytest -q`
  - Performance dashboard: `scripts/generate_performance_dashboard.ps1 -WriteLatest -ExportJson -ExportCsv`
  - Validate dashboard outputs: `scripts/validate_performance_dashboard.ps1 -VerboseOutput`
  - Monitoring report (24h): `scripts/generate_monitoring_report.ps1 -Hours 24 -OpenMd`

- Handoff Discipline
  - If you make non‑trivial changes, update:
    - `docs/AGENT_HANDOFF.md` (What changed / Next actions)
    - `docs/AGI_RESONANCE_INTEGRATION_PLAN.md` (Plan, checklist, acceptance)
  - Optionally, refresh `outputs/agent_handoff.json` (machine‑readable snapshot).

