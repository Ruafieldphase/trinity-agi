# Lumen v1.8 — Final — 2025-10-23

## Overview
- **Self-Tuning Ledger**: weekly policy retraining from `ledger_v17.db`
- **Adaptive Gate Policy**: policy trace exporter (:9154) & Grafana dashboard
- **Full Loop**: analyzer → exporter → gate → ledger → release (if desired)

## Gates (initial)
- Thresholds derived by analyzer (P50/P55). Minimum clamps: sym ≥ 0.65, s ≥ 0.50, c ≥ 0.45

## Artifacts
- `adaptive_gate_policy_v18.json`, `grafana_dashboard_v18_policy_trace.json`

## Upgrade
```bash
# Policy refresh
python lumen_v1_8_assets/ledger_analyzer_v18.py
# Export policy
(python lumen_v1_8_assets/policy_trace_exporter_v18.py &) && sleep 1
```

## Rollback
- Revert to fixed thresholds by overriding env: `LUMEN_GATE_TARGET_*`
