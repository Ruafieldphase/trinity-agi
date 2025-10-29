# v1.5 Production Cutover Checklist

## 0) Freeze & Stakeholders
- [ ] Release window confirmed (UTC/KST)
- [ ] Change freeze enforced on `main`
- [ ] Stakeholders on-call: SRE, Platform, Release, Security

## 1) Pre-flight
- [ ] Stage rollout complete, no active `LumenFastBurn`
- [ ] RC Gate PASS (m_score ≥ 0.48, h_eff ≤ 0.70)
- [ ] Proof bundle archived & attached to release PR
- [ ] Kafka topics present; offsets healthy

## 2) Backup & Safeguards
- [ ] Prometheus backup (`scripts/backup_prometheus.sh`)
- [ ] Loki backup (`scripts/backup_loki.sh`)
- [ ] Helm previous REV noted: `helm history lumen -n lumen-prod`

## 3) Cutover (Helm)
```bash
helm upgrade --install lumen charts/lumen -f charts/lumen/values.prod.yaml -n lumen-prod
```

## 4) Post-deploy Verification (10m)
- [ ] `/maturity` exporter responds 200 within 2s
- [ ] `lumen_m_score` ≥ 0.48 median(5m)
- [ ] `lumen_h_eff` ≤ 0.70 average(5m)
- [ ] Grafana dashboard shows steady m_score trend
- [ ] Error budget burn alerts not firing

## 5) Canary/Traffic
- [ ] Argo Rollouts to 50% → analysis PASS → 100%

## 6) Completion
- [ ] Remove freeze, post-release summary sent
- [ ] Update CHANGELOG (Final) & tag `v1.5.0`
