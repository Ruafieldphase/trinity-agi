# Lumen v1.5 Preview — Streaming & Maturity Layer

## What is included
- **Streaming ingestor (stub)**: `streaming_ingestor_v15.py` → Kafka/Loki placeholders, JSONL fallback
- **Maturity index**: `maturity_index_v15.py` → entropy/volatility/gap 기반 간단 지표
- **Unified Feedback Graph**: `unified_feedback_graph_v15.py` → DOT/JSON 산출

## How to run
```bash
source SESSION_BOOTSTRAP_*.yaml      # or source the exact filename created today
l15.run
# Artifacts:
#  - lumen_v1_5_preview_assets/normalized_fractal_events.jsonl
#  - docs/V15_MATURITY_REPORT.md
#  - lumen_v1_5_preview_assets/Unified_Feedback_Graph_v1_5.(json|dot)
```

## Next
- Kafka/Loki 실제 연동 (confluent-kafka, promtail 등)
- Maturity index hardening (per-loop weights, decay, confidence bounds)
- Graph → Grafana panel & auto-annotations
