# v1.7 Final Prep — Native Matrix, Graph Viewer & Pipeline

## Native Matrix Injection
- `lumen_v1_6_assets/resonance_adapter_v1_native_matrix.py`
  - `LUMEN_MATRIX_FILE`(기본 `/data/v17/gain_alpha_matrix.json`)을 읽어 `gain_alpha`/`window_ms` 튜닝에 바이어스 적용

## Graph Viewer (D3)
- 파일: `web/feedback_graph_view_v17.html`
- 사용: 브라우저에서 열고 `feedback_graph.json` 업로드 → force-directed 그래프 렌더

## CI Pipeline
- `lumen_v17_final_pipeline`: v1.6 네이티브 어댑터 + v1.7 그래프/익스포터 + 엄격 게이트(0.75/0.60/0.55)

## Session Restore
- `SESSION_RESTORE_2025-10-24_v1_7_FINAL.yaml` → `l7.final.run`
