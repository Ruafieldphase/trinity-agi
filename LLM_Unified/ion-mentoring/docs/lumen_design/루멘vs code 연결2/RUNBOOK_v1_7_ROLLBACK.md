# Runbook — v1.7 Rollback

## Symptoms
- Gate fails (symmetry/s_index/c_index), exporter not scraping, dashboard anomalies.

## Immediate actions
```bash
# Restore adapter tuning
python lumen_v1_7_assets/v17_gate_rollback.py --state-file lumen_v1_6_assets/adaptation_state.json --window 1200 --alpha 0.12

# Helm rollback
helm history lumen -n <ns>
helm rollback lumen <REV> -n <ns>
```
## Verification
- :9151/:9152 exporters OK
- Maturity exporter stable; Grafana indices back to normal bands

## Evidence
- Attach indices.csv (if exported), adapter_state, Helm REV before/after
