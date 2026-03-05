# Ops Readiness v2 & Incident→Policy Feedback

## Ops Readiness v2
- Script: `scripts/ops_readiness_check_v2.py` → generates `docs/OPS_READINESS_REPORT_v2.md` and `docs/OPS_READINESS_SUMMARY_v2.json`
- Workflow: `.github/workflows/lumen_ops_readiness_v2.yaml` (PR + daily)

## Incident→Policy
- Schema/Logger: `lumen_v1_9_assets/incidents_schema.sql`, `incident_logger_v19.py`
- Feedback: `incident_to_policy_v19.py` → updates `lumen_v1_8_assets/adaptive_gate_policy_v18.json` and appends to `policy_history`
- Dashboard: `lumen_v1_9_assets/grafana_dashboard_v19_incidents_policy.json`
- Workflow: `.github/workflows/lumen_v19_incident_feedback.yaml`
- Helpers: `scripts/v19_incidents_helpers.sh`

## Quickstart
```bash
# Readiness
source scripts/v19_incidents_helpers.sh
l.ops.ready

# Incident logging
export LUMEN_V19="$PWD/lumen_v1_9_assets"
l9.inc prod sev2 gate "policy-miss" mitigated 12 "hotfix applied"

# Apply Incident→Policy feedback
l9.feedback    # updates v1.8 adaptive policy and history
```
