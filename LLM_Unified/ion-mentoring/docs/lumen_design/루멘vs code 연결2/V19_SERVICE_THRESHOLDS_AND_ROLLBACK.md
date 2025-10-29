# v1.9 — Service Threshold Matrix & Auto-Rollback (stub)

## Files
- Thresholds matrix (env→service): `docs/roi_thresholds_matrix_v19.example.yaml`
- ROI gate decider: `scripts/roi_gate_decider_v19.py`
- Rollback stub: `scripts/perform_rollback_stub.sh`
- Workflow: `.github/workflows/lumen_v19_auto_rollback_on_gate.yaml`

## Use
```bash
# Evaluate env+service gate locally
export ROI_ENV=prod
export ROI_SERVICE=api
export ROI_THRESHOLDS_MATRIX_FILE=docs/roi_thresholds_matrix_v19.example.yaml
python scripts/roi_gate_decider_v19.py

# Manual rollback flow (stub; replace with your platform)
APP_SERVICE=api ROLLBACK_VERSION=previous-stable bash scripts/perform_rollback_stub.sh
```

## In CI (GitHub Actions)
- Run **lumen_v19_auto_rollback_on_gate** with inputs (env, service, rollback target).
- On FAIL: gate step returns non-zero → **Auto rollback (stub)** 실행.
- Replace stub with Helm/ArgoCD/K8s rollout to enact real rollback.
