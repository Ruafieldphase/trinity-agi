# Lumen v1.5 — Release Candidate (RC) — 2025-10-23

## ✨ Highlights
- **Streaming Layer**: Kafka/Loki 어댑터(`event_bus_adapter.py`) + 버퍼 메트릭 CSV
- **Maturity Layer**: Prometheus 익스포터(`maturity_exporter.py`) — `lumen_h_eff`, `lumen_i_sync`, `lumen_m_score`
- **Unified Feedback Graph**: `feedback_graph_builder.py` → `graph_feedback_unified.json`
- **Observability**: Grafana 대시보드(성숙도/SLO) + Prometheus 녹화/알람 룰
- **Helm 차트**: 프로브/보안 컨텍스트/ServiceMonitor/토픽 훅/시크릿/스케줄링/Ingress+TLS
- **자동화**: 세션 복원 스크립트, CI 품질 게이트, SBOM, 증빙 번들, OPA 정책, 카나리(Argo Rollouts)
- **확장성**: KEDA/HPA 오토스케일, Prometheus Adapter 기반 커스텀 메트릭 HPA
- **보안/거버넌스**: OAuth2 Proxy, NetworkPolicy, RBAC, 테넌트 분리(Quota/Limit/Default Deny)

## 🔧 주요 파일(루트 기준)
- 세션 복원: `SESSION_RESTORE_2025-10-24_v1_4_FULL.yaml`, `SESSION_RESTORE_2025-10-24_v1_5_PREVIEW.yaml`
- v1.5 자산: `lumen_v1_5_assets/*`
- Helm 차트: `charts/lumen/*` (+ `values.*.yaml` 프로파일)
- CI/정책: `.github/workflows/*`, `policy/rego/*`, `scripts/release_gate.py`, `scripts/proof_bundle.py`
- 관측: `prometheus/*`, `loki/*`, `grafana_provisioning/*`
- 운영/문서: `docs/*`

## ✅ 품질 게이트 기준 (기본)
- `m_score >= 0.45`, `h_eff <= 0.72`
- FastBurn 경보 미발생
- 카나리 단계 평균 `avg_over_time(lumen_m_score[2m]) >= 0.45`

## 🧪 검증 시나리오
1. v1.4 복원 후 프리뷰 부트스트랩 → 성숙도 메트릭 노출 확인
2. Grafana 대시보드 임포트 → 메트릭 트렌드 확인
3. 릴리즈 게이트 로컬/Actions 실행 → 통과 여부
4. Helm Stage 배포 → Argo Rollouts 점진 + 분석 성공
5. 증빙 번들 생성 → PR 첨부

## 🗂️ 증빙 번들(예시 포함 항목)
- Prometheus 룰/알람, Grafana JSON, `graph_feedback_unified.json`, SBOM, 게이트 로그

## 🧯 롤백
- `helm rollback lumen <REV>`
- Kafka 훅 비활성화: `featureFlags.enableKafkaTopicsHook=false`
- 버퍼 윈도/게인 파라미터 원복

