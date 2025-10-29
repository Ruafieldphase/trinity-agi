# Lumen v1.7 — Final Consolidation

## Release Pipeline
- Workflow: `.github/workflows/lumen_v17_release_pipeline.yaml`
- Steps: v1.6 stack → v1.7 exporter → Gate(strict) → Ledger → Helm package → (optional) notify → Release

## Dashboard
- `lumen_v1_7_assets/grafana_dashboard_v17_full_loop.json`

## Full Loop Session
```bash
source SESSION_RESTORE_2025-10-24_v1_7_FULL_LOOP.yaml
l7.full.run
```
