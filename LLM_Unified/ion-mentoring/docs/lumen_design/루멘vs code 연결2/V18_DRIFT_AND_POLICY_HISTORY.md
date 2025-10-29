# v1.8 — Drift Alerts & Policy History (Ledger v2)

## 구성요소
- 정책 이력 레저: `ledger_v18_policy.db` (`policy_history`, `drift_events`)
  - 스키마: `ledger_v18_policy_schema.sql`
  - 업서트: `policy_history_upsert_v18.py`
- 드리프트 모니터: `drift_monitor_v18.py` (지표:9153 vs 정책:9154 비교, 위반 시 웹훅 알림)
- 워크플로: `lumen_v18_drift_watch.yaml` (매시간 자동 체크)
- 대시보드: `grafana_dashboard_v18_policy_history.json` (정책/드리프트 표/시계열)

## 사용
```bash
# 정책 업서트
cd lumen_v1_8_assets
python ledger_analyzer_v18.py
python policy_history_upsert_v18.py

# 정책/지표 익스포터 기동
(python policy_trace_exporter_v18.py &) &
(cd ../lumen_v1_7_assets && (python metrics_feedback_graph_exporter.py &) &)

# 드리프트 체크 (옵션: 웹훅)
export LUMEN_ALERT_WEBHOOK="https://hooks.slack.com/services/..."
python drift_monitor_v18.py --indices http://127.0.0.1:9153/metrics --policy http://127.0.0.1:9154/metrics --margin 0.00
```
