# Observability Extras

## Grafana Badge Panel
- Import `grafana/elo_dashboard_with_badge.json`.
- Ensure Prometheus scrapes `elo_last_action{domain="ops"}` from the ELO exporter (run with `--last_action`).
- Value mapping: 0→rollback, 1→hold, 2→promote.

## Alertmanager Routing
- Use `monitoring/alertmanager_routes_example.yaml` as a starting point.
- The label `suppressed="true"` (from noise-control alerts) routes to a quiet receiver.
- An inhibit rule prevents duplicate efficiency alerts when a critical one is active.
