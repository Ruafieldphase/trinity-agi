# Lumen — Release Notes (v1.4 Final → v1.5 Preview)
_Generated: 2025-10-24T03:45:55.138291Z_

## TL;DR
- **v1.4**는 안정 리듬/자가복구/증빙 라인을 마무리했고,  
- **v1.5 Preview**는 *Maturity Spectrum*과 *통합 게이트(ROI/SLO × Maturity)*, *스트리밍 연동*을 추가로 얹었습니다.

---

## v1.4 Final — 스냅샷
- 감응/리듬: `resonance_mapper.py`, `feedback_rules.yaml`, `observer_field.yaml`
- 증빙/보안: `proofd_stats`, `proof_exporter_v1_3_stats`, `proof_auto_logger.py`
- 자동복구: `auto_remediation_service.py`, `auto_remediation_rules.yaml`
- 승인연계: `approval_bridge_linked.py`, `bridge_config.linked.yaml`
- 운영자동화: `lumen_v1_4_monorepo_skeleton.zip` (Makefile 기반 통합)
- 보안검증: `SECURITY_CHECKLIST_v1_4.md`, 환경별 ACL/Quorum
- CI 가드레일: `lumen_v1_4_ops_ci_guardrails.zip`
- 릴리즈 자동화: `lumen_v1_4_release_automation.zip` (Semantic-Release + SBOM)

**세션 복원 파일**: `SESSION_RESTORE_2025-10-24_v1_4_FULL.yaml` → 한 줄로 v1.4→v1.5 프리뷰까지 부트스트랩.

---

## v1.5 Preview — 핵심 추가
### 1) Maturity Spectrum (overall/sense/feedback/release)
- 계산기: `lumen_v1_5_preview_assets/maturity_spectrum_v15_alpha.py`
- 윈도우(6h/24h): `maturity_spectrum_window_v15.py`
- 프로메테우스 지표: `metrics/maturity_spectrum*.prom` + 익스포터 `maturity_exporter_v15.py`
- 대시보드: `grafana_dashboard_v15_maturity.json` 및 통합 대시 `dashboard_v19xv15_operational_intel.json`

### 2) 통합 게이트 (ROI/SLO × Maturity)
- 스크립트: `scripts/integrated_gate_v19_v15.py`
- 정책 힌트: `scripts/maturity_to_policy_hint_v15.py`
- GH Actions: `lumen_integrated_gate_and_flipback.yaml` (선택적 플립백 포함)
- 인시던트 카드: `scripts/gate_result_card_v15.py` (Slack/Discord)

### 3) 스트리밍 연동
- Kafka 인제스터: `streaming_ingestor_v15_kafka.py`
- Loki 풀러: `loki_pull_v15.py`
- Compose 스택: `docker/docker-compose.v15.preview.yml`

### 4) 배포/관측 패키징
- Helm 차트: `helm/lumen-v15-preview` (+ pre/post **통합 게이트 Helm 훅**)
- Argo App-of-Apps: `argocd/apps/**`, 모니터링 Kustomize 포함
- 알럿 룰: `prometheus_rules/prom_rules_lumen.yaml`
- 야간 자가점검: `lumen_v15_nightly_selfcheck.yaml`, `argocd/cron/lumen-v15-selfcheck-cronworkflow.yaml`

---

## 업그레이드 가이드 (요약)
1. **이미지 빌드/푸시**: GHCR로 컨테이너 이미지 푸시 (`lumen_v15_build_and_release.yaml` 또는 `scripts/build_image_v15.sh`)
2. **차트 배포**: `helm/lumen-v15-preview` 설치 (필요시 Loki/Kafka 토글)
3. **게이트 훅 활성화**: `values.yaml`의 `gate.*` 조정 (pre/post, 임계값, 플립백)
4. **대시보드/룰**: Grafana/Prometheus에 템플릿 적용
5. **야간 자가점검**: GH Actions/Argo CronWorkflow 중 선택

---

## 호환성 / 주의사항
- Kafka 사용 시 `confluent-kafka` 런타임 의존성 필요
- Loki API 인증/경로는 환경에 맞게 설정
- Helm 훅 실패는 릴리즈 실패로 이어짐(설계상). 실제 롤백 명령은 환경에 맞게 검증 필요

---

## 로드맵 (v1.5 RC → v1.6 초안)
- 유니파이드 피드백 그래프(관계 시각화)
- maturity dH/dt 기반 예측형 게이트
- Helm 차트 App-of-Apps 통합(ingestor/exporter/gate/monitoring 싱글 릴리스)
