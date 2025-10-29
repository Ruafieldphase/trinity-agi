# 🌙 Lumen v1.5 Release (RC)

_Generated: 2025-10-24T04:14:08.934733Z_

## Highlights
- Unified gate: ROI/SLO × Maturity (with windowed spectrum 6h/24h)
- Kafka/Loki streaming ingestion layer
- Prometheus/Grafana integration (Operational Intelligence dashboard)
- Helm chart (pre/post gate hooks) + Argo App-of-Apps
- Auto flipback skeleton + incident cards (Slack/Discord)
- Nightly self-check automation (03:00 KST)

## Deploy (Helm)
```bash
helm upgrade --install lumen-v15 ./helm/lumen-v15-preview   --set image.repository=ghcr.io/<owner>/lumen   --set image.tag=v1.5-rc   --set exporter.enabled=true
```

## Monitor
- Grafana: `grafana/dashboard_v19xv15_operational_intel.json`
- Prometheus rules: `prometheus_rules/prom_rules_lumen.yaml`
- CronWorkflow: `argocd/cron/lumen-v15-selfcheck-cronworkflow.yaml`

## Notes
- Kafka requires `confluent-kafka` in runtime (image includes best-effort install).
- Helm hooks: release fails if gate fails by design; configure flipback per env.
