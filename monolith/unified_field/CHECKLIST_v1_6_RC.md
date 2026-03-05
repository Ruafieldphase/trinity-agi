# v1.6 RC Checklist (One-pager)

```bash
# 1) Bump tag
./scripts/release_bump_v16_rc.sh v1.6-rc1

# 2) Stage deploy (flags ON)
helm upgrade --install lumen charts/lumen -f charts/lumen/values.stage.yaml -n lumen-stage       --set featureFlags.enableV16Enrichment=true --set featureFlags.enableV16Adaptation=true

# 3) RC gate + canary in Stage
gh workflow run lumen_release_gate --ref main -f metrics_url="http://<stage-maturity>:9143/metrics" -f m_score_min=0.45 -f h_eff_max=0.72
kubectl apply -f argo/analysis-template.yaml -n lumen-stage
kubectl apply -f argo/rollout.yaml -n lumen-stage

# 4) Evidence bundle
python scripts/proof_bundle.py --root .

# 5) RC Release (GitHub)
gh workflow run lumen_v16_rc_release --ref main -f tag="v1.6-rc1"
```
