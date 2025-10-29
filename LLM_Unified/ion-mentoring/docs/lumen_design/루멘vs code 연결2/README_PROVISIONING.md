# Lumen v1.5 Ops — Provisioning & Monitoring

## Grafana provisioning
- Place `datasources.yaml` into Grafana provisioning path: `/etc/grafana/provisioning/datasources/`
- Place `dashboards.yaml` into `/etc/grafana/provisioning/dashboards/`
- Copy dashboard json (`lumen_v1_5_assets/grafana_dashboard_lumen_maturity.json`) to `/var/lib/grafana/dashboards/`

## Prometheus Operator
- Deploy chart with ServiceMonitor enabled (file `templates/servicemonitor.yaml`)

## Kafka topics via Helm hook
- Post-install job (bitnami/kafka) ensures topics exist using `.Values.streaming.kafka.*`
