# v1.9 — Composite ROI + SLO + Rollback(workflow)

## 구성
- SLO 레저/로거/익스포터(:9157): `lumen_v1_9_assets/slo_schema.sql`, `slo_logger_v19.py`, `slo_exporter_v19.py`
- 복합 게이트: `scripts/composite_roi_v19.py` (ROI 게이트 + SLO burn)
- 롤백 스켈레톤: `scripts/helm_rollback_v19.sh`, `scripts/argocd_rollback_v19.sh`
- 워크플로: `.github/workflows/lumen_v19_composite_gate_and_rollback.yaml`

## 사용
```bash
# SLO 샘플 기록
(cd lumen_v1_9_assets && python slo_logger_v19.py --service api --errors 12 --requests 1000)

# 익스포터 가동(로컬 테스트)
(cd lumen_v1_9_assets && (python slo_exporter_v19.py &) && sleep 1)

# 복합 게이트(로컬)
export ROI_ENV=prod
export ROI_SERVICE=api
export ROI_THRESHOLDS_MATRIX_FILE=docs/roi_thresholds_matrix_v19.example.yaml
python scripts/composite_roi_v19.py  # FAIL이면 종료코드 2

# CI에서 수동 실행 → 필요 시 롤백
# GitHub Actions → lumen_v19_composite_gate_and_rollback
# inputs: roi_env, roi_service, platform(helm|argocd|none), target
```
