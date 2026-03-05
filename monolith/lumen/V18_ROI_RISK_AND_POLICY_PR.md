# v1.8 — ROI/Risk KPIs & Auto PR on Policy

## 구성요소
- ROI/Risk Exporter (:9155): `roi_risk_exporter_v18.py`
  - `lumen_v18_release_success_rate`, `lumen_v18_rollback_rate`, `lumen_v18_drift_violation_count`
- Grafana: `grafana_dashboard_v18_roi_risk.json`
- Auto PR 워크플로: `lumen_v18_policy_pr.yaml` (autotune 완료 시 자동 PR 생성)
- 헬퍼: `v18_roi_helpers.sh`

## 사용
```bash
# ROI/Risk 지표 노출
source scripts/v18_roi_helpers.sh
l8.roi 100    # 최근 N=100 윈도우

# 수동 PR 트리거
gh workflow run lumen_v18_policy_pr
```
