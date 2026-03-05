# v1.6 Final — Production Cutover Checklist

## Preconditions
- Stage RC gate PASS, canary PASS, no FastBurn ≥ 24h
- Backups (Prom/Loki) completed; previous Helm REV recorded

## Deploy
```bash
helm upgrade --install lumen charts/lumen -f charts/lumen/values.prod.yaml -n lumen-prod       --set featureFlags.enableV16Enrichment=true       --set featureFlags.enableV16Adaptation=true
```

## Verify (10–15m)
- :9143 maturity exporter: m_score ≥ 0.48 median(5m), h_eff ≤ 0.70 avg(5m)
- :9151/:9152 exporters responding; ServiceMonitor scraping
- Grafana v1.6 dashboards stable; no FastBurn alerts

## Canary
- Argo Rollouts 20%→50%→100% with analysis PASS at each step

## Evidence
- `scripts/proof_bundle.py --root .` and attach to release PR

## Post
- Tag final `v1.6.0` (or run `lumen_v1_6_final_release` workflow)
- Remove freeze; announce release
