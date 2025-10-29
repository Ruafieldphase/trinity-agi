# v1.9 — Operational Intelligence Loop (Endgame)

## Components
- Notifier: `scripts/incident_notifier_v19.py` (Slack/Discord)
- ROI↔Incident Bridge: `scripts/roi_incident_bridge_v19.py`
- Full Ops Loop Workflow: `.github/workflows/lumen_v19_full_ops_loop.yaml`

## Behavior
1) Readiness check (v2) → report artifacts
2) ROI gate (env-specific) → PASS: green alert / FAIL: sev2 incident auto-log + red alert
3) (Schedule) Runs every 30 min or manual dispatch

## Setup
```bash
# Webhook secrets (GitHub Actions → repo secrets)
#   SLACK_WEBHOOK_URL, DISCORD_WEBHOOK_URL
```

## Manual
```bash
# Local quick test
export ROI_ENV=prod
python scripts/roi_incident_bridge_v19.py
```
