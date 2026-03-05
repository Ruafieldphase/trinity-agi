# Alerting — Slack Routing & Noise Guard (Asia/Seoul)

## Files
- Alertmanager route: `monitoring/alertmanager_elo_routing.yaml`
- Recording rules: `monitoring/elo_recording_rules.yaml`
- Guarded alerts: `monitoring/elo_alert_rules_extras_guarded.yaml`

## Wiring (Prometheus)
1. Add recording rules:
   ```
   --rule.files=.../elo_recording_rules.yaml,.../elo_alert_rules_extras_guarded.yaml
   ```
2. Keep existing ELO base rules loaded as well.

## Wiring (Alertmanager)
1. Use:
   ```
   --config.file=.../alertmanager_elo_routing.yaml
   ```
2. Set env:
   - `SLACK_WEBHOOK_URL_HIGH`
   - `SLACK_WEBHOOK_URL_LOW`

## Semantics
- *Eligibility*: `elo_domain_eligible` requires ≥50 events in 5m to alert.
- *Daytime vs Night*: warnings go to `#elo-notices` by day, `#elo-notices-night` by night. Criticals always to `#elo-alerts`.
- *Inhibition*: Critical suppresses Warning for same `alertname`+`domain`.

## Tuning knobs
- Thresholds: `0.30 / 0.50` for low-confidence; `0.20 / 0.15` for drifts.
- Traffic guard: change `> 50` in `elo_recording_rules.yaml`.
- Slack channels: tweak receivers in `alertmanager_elo_routing.yaml`.
