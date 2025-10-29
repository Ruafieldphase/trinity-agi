# v1.7 — Ledger & RC→Final
- Ledger: `ledger_v17_schema.sql`, `ledger_v17_ingestor.py`
- Gate 실패 롤백: `v17_gate_rollback.py`
- 파이프라인: `.github/workflows/lumen_v17_rc_to_final.yaml`

## 로컬
```bash
cd lumen_v1_7_assets
python feedback_graph_core_v17.py
python ledger_v17_ingestor.py        # ledger_v17.db 생성
python v17_gate_rollback.py --state-file ../lumen_v1_6_assets/adaptation_state.json --window 1200 --alpha 0.12
```
