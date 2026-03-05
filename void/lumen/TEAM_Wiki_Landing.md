# LUON Team Wiki — Landing

## Quick Links
- **운영 1‑페이지**: `runbooks/OPS_OnePager.md`
- **DR 런북**: `runbooks/Disaster_Recovery_Runbook.md`
- **모니터링 가이드**: `ops/README_Monitoring.md`
- **배포 가이드**: `ops/README_Deploy.md`
- **클러스터(K8s)**: `ops/k8s/README_Kubernetes.md` · `ops/k8s/README_Addons_Hardening.md`
- **인덱스**: `README_Index.md`

## How we run
- 주간: 카나리 승급 → SLO 모니터링 → 주간 리뷰
- 야간: 자동 롤백 우선(안정성 최상위), 오전에 원인 분석 후 재시도
- 모든 결정/변경은 감사 로그(`luon_audit_log.jsonl`)로 남긴다.
