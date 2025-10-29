# v1.5-α — Maturity Gate & Policy Hint

- 게이트: `scripts/maturity_gate_v15.py` (overall/sense/feedback/release 임계)
- 힌트: `scripts/maturity_to_policy_hint_v15.py` → v1.8 정책 JSON 보정
- 워크플로: `.github/workflows/lumen_v15_maturity_gate_and_hint.yaml`

## 로컬
```bash
python lumen_v1_5_preview_assets/maturity_spectrum_v15_alpha.py
MATURITY_OVERALL_MIN=0.6 python scripts/maturity_gate_v15.py
python scripts/maturity_to_policy_hint_v15.py
```
