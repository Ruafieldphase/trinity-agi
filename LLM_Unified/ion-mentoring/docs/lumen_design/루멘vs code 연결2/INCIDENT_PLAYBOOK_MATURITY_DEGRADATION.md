# Incident Playbook — Maturity Degradation

## Trigger
- FastBurn or SlowBurn alert firing
- m_score trend downwards with h_eff sustained high

## Immediate Actions (15m)
1) Freeze release & notify #oncall-lumen
2) Capture proof bundle: `python scripts/proof_bundle.py --root .`
3) Increase STREAM_BUFFER_WINDOW_MS (+300ms) and reduce GAIN_TRAINER_ALPHA (-0.02)
4) Check Kafka/Loki latency; rebalance or throttle noisy producers

## Diagnostics
- Grafana: SLO + Maturity dashboards (last 30m/6h)
- Compare phase_diff & lag_ms distributions
- Review Argo canary analysis results

## Remediation Paths
- Gain decay up (0.93 → 0.96) for stability
- Window widen (1200 → 1500/1800)
- If external noise: temporarily disable streaming intake

## Rollback
- `helm rollback lumen <REV>`
- Re-run smoke/gate; verify alerts clear

## Postmortem
- Timeline, root cause, action items, follow-up PRs
