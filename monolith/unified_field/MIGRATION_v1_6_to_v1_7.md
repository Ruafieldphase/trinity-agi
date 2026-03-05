# Migration — v1.6 → v1.7

## What changes
- v1.7 introduces the **Adaptive Feedback Graph 2.0** and a native matrix injection to the adapter.
- New exporter at :9153 with indices: `s_index`, `c_index`, `symmetry_score`.

## Required flags
```yaml
featureFlags:
  enableV17FeedbackGraph: true
```

## Adapter
- Use `resonance_adapter_v1_native_matrix.py` (v1.7) or sidecar injector for compatibility.
- Env: `LUMEN_MATRIX_FILE=/data/v17/gain_alpha_matrix.json`

## Dashboards
- Provision `dashboards_v17.yaml`; copy v17 dashboard JSONs to `/var/lib/grafana/dashboards/v17`.

## Rollback
- Revert Helm REV and restore adapter state:
```bash
python lumen_v1_7_assets/v17_gate_rollback.py --state-file lumen_v1_6_assets/adaptation_state.json --window 1200 --alpha 0.12
```
