# Lumen v1.1 — Incident Playbooks

> 각 플레이북은 *탐지(Detect) → 진단(Diagnose) → 완화(Mitigate) → 복구(Recover) → 사후(Review)* 순서로 정리.

---

## 1) Latency Spike (p95 > 500ms)
**Detect**
- Grafana: Latency 패널 상승 / Alert `LumenHighLatencyP95` firing
- Slack: WARNING/CRITICAL 메시지

**Diagnose**
- Prometheus: 최근 `throughput_rps`, `error_rate`, `phase_diff_value` 확인
- Proof Ledger: 직전 적용 이벤트 확인

**Mitigate (immediate)**
```bash
make scenario-latency        # 리허설 / 재현
# 또는 즉시 쓰로틀/서킷 적용
export PLUGIN_MODE=shell     # or k8s/http
python tools/adaptive_feedback/resonance_executor.py --proposals=proposals.json --state=weights_state.json
```

**Recover**
- 정상화 후 `python tools/adaptive_feedback/resonance_rollback.py`
- `feedback_active_adjustments` 가 0으로 내려오는지 확인

**Review**
- `feedback_rules_v2.yaml`의 임계/쿨다운 튜닝
- 대시보드에 Annotation(적용/롤백) 확인

---

## 2) Error Rate Spike (error_rate > 3%)
**Detect**
- Alert `LumenHighErrorRate`

**Diagnose**
- 최근 배포 여부, 외부 의존성 latency 확인
- `coherence_value` 동반 하락 여부

**Mitigate**
- `throttle_noncritical_tasks`, `enable_circuit_breaker` 액션 강화
- 필요 시 트래픽 분산/롤백

**Recover & Review**
- 원인분석과 히스테리시스/쿨다운 재검토

---

## 3) Coherence Drop (< 0.55, 3m)
**Mitigate**
- `scale_down_creative_band_weight`, `increase_safety_weight` 가이드라인대로 적용
- 장기적으로 `observer_field.yaml` 가중치/임계치 조정

---

## 4) Plugin Failure (k8s/http/shell 적용 실패)
**Detect**
- Executor 로그에서 plugin 실패 메시지
**Actions**
- `plugins.yaml` 템플릿 변수 확인 (`SERVICE`, `K8S_NAMESPACE`, 토큰 등)
- 해당 모드에서 수동 명령 재시도
- 일시적으로 `PLUGIN_MODE=shell`로 폴백

---

## 5) Monitoring Plane Degradation (Grafana/Prometheus/Alertmanager)
**Prometheus 다운**
- `docker compose logs prometheus` → 구성 파일 마운트/권한 확인
**Grafana 다운**
- 프로비저닝 경로/권한 확인, admin 패스워드 초기화
**Alertmanager 다운**
- `alertmanager.yml` 템플릿 구문/웹훅 URL 확인

---

## 6) Slack Delivery Issues
- 웹훅 URL 재발급/교체
- Alertmanager `routes` 및 `inhibit_rules` 확인
- 임시로 `slack-default`로 단일 라우팅

---

## 7) Rollback Not Happening
- `rollbacks.json` 만료 시각/남은 TTL 확인
- `resonance_rollback.py` 주기 호출(cron/systemd) 재확인
- 규칙 엔진 `exit` 조건 과도/완화 여부 점검

---

## 8) Ledger/Audit Review
- `proof_ledger.jsonl` 타임라인으로 사건 재구성
- 릴리즈/대시보드 스냅샷과 대조

