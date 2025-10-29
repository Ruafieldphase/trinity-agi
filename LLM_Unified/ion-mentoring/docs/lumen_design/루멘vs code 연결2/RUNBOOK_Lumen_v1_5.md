# Lumen v1.5 Ops Runbook

## Objectives
- Keep `lumen_maturity_state == 1` during steady state.
- Meet monthly SLO: 99.5% maturity pass ratio (0.5% error budget).

## Dashboards
- Resonance Maturity: grafana_dashboard_lumen_maturity.json
- SLO/Error Budget: grafana_dashboard_lumen_slo.json

## Prometheus
- Load recording rules: recording_rules_lumen_slo.yaml
- Alerts:
  - LumenFastBurn (5m): error ratio > 2x budget for 10m
  - LumenSlowBurn (30m): error ratio > budget for 2h

## Tuning Playbook
1) Error ratio 상승 & H_eff > 0.7
   - Increase STREAM_BUFFER_WINDOW_MS (e.g., 1200 -> 1800)
   - Reduce GAIN_TRAINER_ALPHA (e.g., 0.12 -> 0.08)
2) Pass ratio 변동성 높음 (롤링)
   - Increase GAIN_TRAINER_DECAY (e.g., 0.93 -> 0.96)
   - Add small backoff in Auto-Remediation loop
3) I_sync 낮음 & lag_ms 상승
   - Check Kafka/Loki latency; consider batching
   - Pin pods via nodeSelector/affinity to reduce cross-AZ hops

## Escalation
- If both FastBurn & SlowBurn firing: freeze release pipeline, capture proof bundle, open incident (SEV-2).
