# Lumen v1.9 — Production ROI (Deploy/Rollback History)

## Components
- SQLite ledger: `lumen_v1_9_assets/lumen_prod_events.db` (schema `prod_events_schema.sql`)
- Logger CLI: `prod_event_logger.py`
- Exporter (:9156): `prod_roi_exporter_v19.py`
- Dashboard: `grafana_dashboard_v19_prod_roi.json`
- GitHub Actions: `lumen_v19_record_prod_event.yaml`
- Helpers: `scripts/v19_prod_roi_helpers.sh`

## Usage
```bash
export LUMEN_V19="$PWD/lumen_v1_9_assets"
source scripts/v19_prod_roi_helpers.sh
l9.log prod deploy v1.9.0 alice success "blue/green succeeded"
l9.log prod rollback v1.9.0 alice success "canary rollback"
l9.roi
```
