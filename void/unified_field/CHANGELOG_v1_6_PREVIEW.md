# Lumen v1.6 — Preview — 2025-10-23

## What’s new
- **Streaming Enrichment (P1)**: `stream_enricher_v1.py` → `enriched_stream.jsonl`, `semantic_metrics.csv`
- **Resonance Adaptation (P2)**: `resonance_adapter_v1.py` + exporter(`:9152`) → `adaptation_state.json`, `adaptation_metrics.csv`
- **Memory & History (P3)**: `resonance_memory_store.py`, `history_tracker_v1.py` → `memory_store.json`, `v16_history.csv`
- **Helm v1.6**: Enricher/Adapter Deployments, Service/ServiceMonitor, PVC 옵션, values 플래그
- **Grafana**: v1.6 대시보드 2종(Enrich&Adapt, Memory&History)
- **CI**: `lumen_v16_smoke` 스모크 잡

## Quick start
```bash
cd lumen_v1_6_assets
make p2-smoke    # :9151, :9152 노출 → memory/history 실행
make memory
make history
```
