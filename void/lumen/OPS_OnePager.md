# OPS One Pager

- `ops/Makefile` targets:
  - `elo_convert`: Convert JSONL to CSV
  - `elo_metrics`: Compute metrics to Markdown
  - `preflight`: Sanity checks, create sample data
  - `quickstart`: Preflight + run a short canary dry-run

Observability: hook Prometheus exporter (todo) and publish `elo_*` metrics.
