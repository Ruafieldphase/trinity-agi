# v1.9 — Weighted Composite Score & Blue/Green Flipback

## 구성
- 가중치 매트릭스: `docs/roi_weights_matrix_v19.example.yaml`
- 점수 계산: `scripts/composite_score_v19.py` (0..100)
- Flipback(2단계): `scripts/bluegreen_flipback_v19.sh` (dry-run → execute)
- 워크플로: `.github/workflows/lumen_v19_composite_score_and_flipback.yaml`

## 점수식
`score = 100 * (w_success*success - w_rollback*rollback - w_burn*max(0, burn-1)/burn_norm)`  
- burn > 1.0 일 때만 패널티. burn_norm(예: 3.0)으로 1..4 범위를 0..1로 정규화.

## 사용
```bash
# SLO 익스포터 가동 + ROI 게이트 디시더 사용(선행 필요)
# 점수 계산
export ROI_ENV=prod
export ROI_SERVICE=api
export ROI_WEIGHTS_MATRIX_FILE=docs/roi_weights_matrix_v19.example.yaml
python scripts/composite_score_v19.py  # {"score": 78.4, ...}

# GitHub Actions → lumen_v19_composite_score_and_flipback
#  - score_min 미만이면 DRY-RUN 플립백 수행
#  - confirm_execute = yes 설정 시 실제 플립백 실행(스크립트 내부는 기본 주석/드라이런)
```
