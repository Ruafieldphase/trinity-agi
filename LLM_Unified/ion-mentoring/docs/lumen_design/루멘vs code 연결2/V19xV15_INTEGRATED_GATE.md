# Integrated Gate — v1.9(ROI/SLO) × v1.5(Maturity)

## 스크립트
- `scripts/integrated_gate_v19_v15.py` — ROI/SLO 결과와 Maturity Spectrum을 결합하여 최종 PASS/FAIL 결정
  - Maturity가 FAIL이면 무조건 FAIL
  - Maturity가 경계선(Overall < min + penalty)인 경우, ROI PASS라도 FAIL로 격하 가능 (기본 penalty=0.10)

## 워크플로
- `.github/workflows/lumen_integrated_gate_and_flipback.yaml`
  - 통합 게이트 수행 → 실패시 선택적 플립백(helm/argocd) → Slack/Discord 알림

## 사용 (GitHub Actions → Run workflow)
- inputs:
  - `roi_env` (prod/stage/dev)
  - `roi_service` (api/web/worker…)
  - `maturity_overall_min` (기본 0.60)
  - `flip_platform` (none|helm|argocd)
  - `flip_target` (previous 등)

## 로컬 테스트
```bash
# maturity 산출
python lumen_v1_5_preview_assets/maturity_spectrum_v15_alpha.py
# 통합 게이트
MATURITY_OVERALL_MIN=0.6 python scripts/integrated_gate_v19_v15.py
```
