# v1.6 Preview — Helm & CI

## Helm
- Templates: v16_enricher.yaml, v16_adapter.yaml, v16_servicemonitors.yaml
- Values: `v16.enricher/*`, `v16.adapter/*`, featureFlags.enableV16*

## Grafana
- Import `lumen_v1_6_assets/grafana_dashboard_v16_memory_history.json`.

## CI
- Workflow: `lumen_v16_smoke` (manual) — exporters respond and metrics are present.
