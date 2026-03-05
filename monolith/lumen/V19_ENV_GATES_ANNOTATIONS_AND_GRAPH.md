# v1.9 — Annotations Upload, Env-specific ROI Gates, ROI Graph

## Components
- Grafana annotations uploader: `scripts/upload_grafana_annotations_v18.py`
- Env-specific ROI gate checker: `scripts/check_roi_thresholds_env_v19.py`
- Thresholds example: `docs/roi_thresholds_v19.example.yaml`
- ROI graph (PNG): `scripts/build_roi_graph_v19.py`
- Extended RC→Final: `.github/workflows/lumen_v19_rc_to_final_plus.yaml`

## Usage
```bash
# 1) 정책 어노테이션 업로드
export GRAFANA_URL="https://grafana.example.com"
export GRAFANA_API_KEY="***"
python scripts/upload_grafana_annotations_v18.py

# 2) 환경별 ROI 게이트
export ROI_ENV=prod
export ROI_THRESHOLDS_FILE=docs/roi_thresholds_v19.example.yaml
python scripts/check_roi_thresholds_env_v19.py

# 3) ROI 그래프 생성 (PNG)
python scripts/build_roi_graph_v19.py  # -> docs/ROI_GRAPH_v1_9_YYYYMMDD.png

# 4) 확장 파이프라인 실행 (릴리즈에 PNG 첨부)
# GitHub Actions → lumen_v19_rc_to_final_plus → Run workflow
```
