# Lumen v1.6 P3 — Resonance Memory & History

## 구성
- `resonance_memory_store.py`: enriched_stream.jsonl → memory_store.json (패턴 시그니처), memory_metrics.csv
- `history_tracker_v1.py`: semantic/adaptation 결합 → v16_history.csv (entropy_shift + resync)

## 사용법
```bash
cd lumen_v1_6_assets
make p2-smoke   # 지표 노출
make memory     # 시그니처 생성
make history    # 엔트로피 시프트 + 리싱크 기록
```

## Prometheus Operator (예시)
- ServiceMonitor 샘플: `lumen_v1_6_assets/servicemonitor_samples/*`
  - 서비스가 포트 이름 `enrichment`(9151), `adaptation`(9152)를 노출한다고 가정
