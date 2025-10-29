# Lumen v1.1 — Go/No-Go Checklist

## A. Monitoring Stack (Prometheus/Grafana)
- [ ] Docker stack up: `docker compose ps` shows prometheus, node-exporter, grafana, alertmanager as **running**
- [ ] Grafana login & dashboards auto-provisioned (folder **Lumen**)
- [ ] Prometheus can scrape node-exporter and sees `lumen_metrics.prom` via textfile collector
- [ ] Alertmanager UI reachable at http://localhost:9093

## B. Adaptive Feedback Loop
- [ ] `.env` configured (`PROM_URL`, `PLUGIN_MODE`, `SERVICE`, optional Grafana/Slack vars)
- [ ] `python collect_metrics.py` succeeds (or simulated metrics available)
- [ ] `python resonance_mapper.py metrics.json` produces `resonance_mapped.json`
- [ ] `python resonance_notifier.py --rules=feedback_rules_v2.yaml --emit_json` outputs `proposals.json`
- [ ] `python resonance_executor.py` updates `weights_state.json`, bumps metrics, appends ledger
- [ ] `python prometheus_textfile_publisher.py` writes `metrics/lumen_metrics.prom`
- [ ] `python resonance_rollback.py` processes TTL when due

## C. Alerting
- [ ] `prom_alert_rules.yml` loaded (Prometheus logs show rule files loaded)
- [ ] Slack webhook configured in `alertmanager.yml`
- [ ] Inhibition works: critical suppresses warning/info for same `alertname`+`team`

## D. CI/CD & Release Security
- [ ] GitHub Actions CI green (lint + tests)
- [ ] Release workflow available and permissions set: `contents: write`, `packages: write`, `id-token: write`
- [ ] GHCR image builds successfully; cosign signature present
- [ ] SBOM (`sbom.spdx.json`) attached to latest Release

## E. Proof & Auditing
- [ ] `proof_ledger.jsonl` accumulating apply/rollback events
- [ ] Regular backup scheduled for ledger artifacts

## Decision
- [ ] Go — All checks pass
- [ ] No-Go — Open items listed with owner & ETA
