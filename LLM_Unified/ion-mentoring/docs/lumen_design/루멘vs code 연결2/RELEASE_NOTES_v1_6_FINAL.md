# Lumen v1.6 — Final — 2025-10-23

## Overview
v1.6는 Streaming Enrichment + Resonance Adaptation + Memory/History를 통해
실시간 정보 흐름의 의미 밀도를 높이고, 시스템 리듬을 상황에 맞게 자가 조정하며,
패턴 시그니처와 변동 히스토리를 증빙 번들에 통합합니다.

## Changes since RC
- Helm v1.6 차트 안정화(퍼시스턴스/ServiceMonitor 기본값 보강, 유닛테스트 통과)
- v1.6 Preview/RC 스모크·릴리즈 파이프라인 통합
- Grafana v1.6 대시보드 프로비저닝 스크립트 포함
- 스냅샷/복구 스크립트(v16 memory) 채택

## Final Quality Gates
- Stage:   m_score ≥ 0.45, h_eff ≤ 0.72, canary analysis PASS
- Prod:    m_score ≥ 0.48, h_eff ≤ 0.70, FastBurn 없음(≥ 24h), canary 2단계 PASS
- Evidence bundle 첨부: memory/history/enrichment/adaptation + dashboards + SBOM + gate logs

## Upgrade
```bash
# v1.5 → v1.6
source SESSION_RESTORE_2025-10-24_v1_6_PREVIEW.yaml
helm upgrade --install lumen charts/lumen -f charts/lumen/values.prod.yaml -n lumen-prod       --set featureFlags.enableV16Enrichment=true --set featureFlags.enableV16Adaptation=true
```

## Rollback
`helm rollback lumen <REV>` 후 smoke/gate 재검증, 필요 시 v1.5 세션 복원으로 즉시 전환.
