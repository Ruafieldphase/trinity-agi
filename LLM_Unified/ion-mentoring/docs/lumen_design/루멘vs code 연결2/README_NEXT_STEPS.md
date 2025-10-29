# Lumen v1.5 Preview Assets

This directory contains runnable skeletons for the streaming + maturity layer:

- `event_bus_adapter.py` — Kafka/Loki adapter -> writes `stream_buffer_metrics.csv`
- `maturity_exporter.py` — exposes Prometheus metrics on `:9143/metrics`
- `feedback_graph_builder.py` — creates `graph_feedback_unified.json`
- `Makefile` — convenience targets: `make stream`, `make maturity`, `make graph`
- `prometheus_scrape_lumen_maturity.yaml` — Prometheus scrape snippet
- `grafana_dashboard_lumen_maturity.json` — minimal Grafana dashboard

## Quick start (local)
```bash
cd lumen_v1_4_monorepo_skeleton   # or your repo root
cp -r /mnt/data/lumen_v1_5_assets/* .

# Start streaming adapter (Kafka optional; will mock if unavailable)
make stream

# In another terminal: expose maturity metrics
make maturity

# Build feedback graph (offline)
make graph
```

## Prometheus
Add `prometheus_scrape_lumen_maturity.yaml` to your Prometheus config and reload.

## Grafana
Import `grafana_dashboard_lumen_maturity.json` as a new dashboard.
