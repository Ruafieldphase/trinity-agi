# v1.7 RC — Matrix Injection & Gate

- `matrix_injector_v17.py` : v1.7 `gain_alpha_matrix.json`을 v1.6 `adaptation_state.json`에 힌트로 주입
- `adapter_bridge_v17.py`  : 주기적 주입 루프(옵션)
- Helm: `v17_matrix_configmap.yaml` 로 매트릭스 ConfigMap 생성, v16 Adapter에 `/data/v17`로 마운트
- Gate: `v17_gate.py` → `symmetry_score/s_index/c_index` 임계 검증

## 로컬 RC 러너
```bash
source SESSION_RESTORE_2025-10-24_v1_7_RC.yaml
l7.rc.run
```

## GitHub Actions
- `lumen_v17_rc_pipeline`: 그래프 생성 → 주입 → 익스포터 → 게이트
