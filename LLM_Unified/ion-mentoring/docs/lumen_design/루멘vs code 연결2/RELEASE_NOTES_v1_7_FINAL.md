# Lumen v1.7 — Final — 2025-10-23

## Overview
- **Adaptive Feedback Graph 2.0**: symmetry-centered loop, native matrix injection to adapter
- **Indices**: `s_index`(stability), `c_index`(creative), `symmetry_score`
- **Full Loop Pipeline**: build → gate(strict) → ledger → package → release/notify
- **Visualization**: v17 full-loop Grafana dashboard + D3 viewer

## Changes since RC
- Adapter: native `LUMEN_MATRIX_FILE` 지원 (`resonance_adapter_v1_native_matrix.py`)
- Gate 강화: symmetry ≥ 0.75, s ≥ 0.60, c ≥ 0.55 기본
- Ledger: `ledger_v17.db` 적재 파이프라인 추가
- Release: `lumen_v17_release_pipeline`에 통합

## Quality Gates (Final)
- PASS 기준(기본): symmetry ≥ 0.75, s ≥ 0.60, c ≥ 0.55 (조정 가능)
- 실패 시: 롤백 훅으로 어댑터 상태 복구(window=1200, alpha=0.12)

## Artifacts
- Helm chart(tgz), `feedback_graph.json`, `gain_alpha_matrix.json`, `indices.json`, `ledger_v17.db`

## Upgrade
```bash
# Stage → Prod
helm upgrade --install lumen charts/lumen -f charts/lumen/values.prod.yaml -n lumen-prod
# v17 exporter/ServiceMonitor 활성 (values.featureFlags.enableV17FeedbackGraph = true)
```

## Rollback
- `helm rollback lumen <REV>`
- 어댑터 상태 복원: `python lumen_v1_7_assets/v17_gate_rollback.py --state-file lumen_v1_6_assets/adaptation_state.json --window 1200 --alpha 0.12`
