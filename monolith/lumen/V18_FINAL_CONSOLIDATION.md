# v1.8 — Final Consolidation

## 새 구성요소
- Policy Trace Exporter (:9154) → `lumen_v1_8_assets/policy_trace_exporter_v18.py`
- Grafana 대시보드(Policy Trace): `grafana_dashboard_v18_policy_trace.json`
- 주간 자동화(월 03:00 UTC): `.github/workflows/lumen_v18_adaptive_weekly.yaml`
- 최종 릴리즈 워크플로: `.github/workflows/lumen_v18_final_release.yaml`
- 세션 복원(최종): `lumen_v1_8_assets/SESSION_RESTORE_2025-10-24_v1_8_FINAL.yaml`
- SBOM/License 게이트(오프라인 플레이스홀더): `scripts/sbom_gate.sh`, `scripts/license_gate.sh`

## 실행
```bash
# Policy trace exporter
cd lumen_v1_8_assets
python ledger_analyzer_v18.py
(python policy_trace_exporter_v18.py &) && sleep 1
curl -fsSL http://127.0.0.1:9154/metrics

# v1.8 풀 루프
source lumen_v1_8_assets/SESSION_RESTORE_2025-10-24_v1_8_FINAL.yaml
l8.full.run
```
