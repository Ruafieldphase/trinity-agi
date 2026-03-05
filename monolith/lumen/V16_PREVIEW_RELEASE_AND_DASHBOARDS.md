# v1.6 Preview — Release & Dashboards

## Release
- Workflow: `lumen_v16_release_preview`
  - Smoke → Helm Package → GitHub Release(Helm tgz + dashboards + changelog)

## Dashboards provisioning
- Place `grafana_provisioning/dashboards_v16.yaml` into Grafana provisioning dashboards dir.
- Copy dashboards with `scripts/install_v16_dashboards.sh` (default to /var/lib/grafana/dashboards/v16).

## Snapshot
- Save memory/history/enrichment/adaptation artifacts:
  ```bash
  scripts/v16_snapshot_memory.sh   # outputs tar.gz under v16_snapshots/
  scripts/v16_restore_memory.sh <snapshot.tar.gz> [/data]
  ```
