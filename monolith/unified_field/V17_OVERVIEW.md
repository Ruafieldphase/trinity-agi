# Lumen v1.7 — Adaptive Feedback Graph 2.0 (Preview)

## 구성
- Core: `feedback_graph_core_v17.py` → `feedback_graph.json`, `gain_alpha_matrix.json`, `indices.json`
- Exporter: `metrics_feedback_graph_exporter.py` (:9153/metrics) — s_index, c_index, symmetry_score
- Helm: `templates/v17_feedback.yaml`, `templates/v17_feedback_servicemonitor.yaml`, values flags
- Grafana: `grafana_dashboard_v17_afg2.json`

## 실행
```bash
cd lumen_v1_7_assets
make smoke      # 그래프 생성 → :9153 지표 확인
```

## 다음
- v1.7 RC: gain_alpha_matrix를 Adapter에 주입하여 루프 간 가중치 적용
- v1.7 Final: Graph 시각화 패널(노드/엣지) 추가 + ledger 연동
