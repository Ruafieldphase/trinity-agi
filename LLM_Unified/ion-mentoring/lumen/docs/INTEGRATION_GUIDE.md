# Lumen 시스템 통합 계획서

**날짜**: 2025년 10월 25일  
**프로젝트**: ION Mentoring API + Lumen Monitoring System 통합  
**목표**: 루멘의 성숙도/ROI/SLO 모니터링 시스템을 Cloud Run 환경에 맞게 적응 및 통합

---

## 🎯 통합 목표

### 핵심 가치
1. **성능 최적화**: Redis 캐싱 효과 자동 측정 및 피드백
2. **비용 관리**: ROI Gate로 예산 초과 자동 감지 및 알림
3. **안정성 보장**: SLO 모니터링으로 서비스 품질 실시간 추적
4. **운영 자동화**: Maturity Spectrum으로 시스템 성숙도 측정

### 측정 가능한 성과
- 비용 절감: 목표 $200/month 달성 및 유지
- 성능 개선: 캐시 히트율 >80%, 레이턴시 <100ms
- 안정성: 가용성 >99.5%, 에러율 <0.1%
- 운영 효율: 수동 개입 감소 >70%

---

## 📊 현재 상태 분석

### ION 시스템 (현재)

```
인프라:
- Cloud Run: ion-api (Main), ion-api-canary (Canary)
- Redis: Cloud Memorystore (10.234.163.115:6379)
- Lumen Gateway: 로컬 프록시 (localhost:8080)
- VPC: ion-redis-connector (Serverless VPC Access)

모니터링:
- Cloud Logging: 로그 수집
- Cloud Monitoring: 기본 메트릭 (요청 수, 레이턴시, 에러율)
- 수동 대시보드: GCP Console에서 확인

문제점:
- 모니터링이 수동적 (실시간 알림 부족)
- 비용/성능 게이트 없음 (예산 초과 감지 느림)
- 캐싱 효과 측정 어려움 (수동 분석)
- 롤백 자동화 없음 (수동 개입 필요)
```

### Lumen 시스템 (원본, Kubernetes 기반)

```
핵심 컴포넌트:
- Maturity Exporter: 시스템 성숙도 측정 (v1.5-v1.8)
- ROI Gate: 투자 대비 효과 측정 및 게이트 결정
- SLO Exporter: 서비스 수준 목표 추적
- Feedback Graph: 메트릭 간 피드백 루프 생성
- Adaptive Policy: 자동 임계값 조정

모니터링 스택:
- Prometheus: 메트릭 수집 및 저장
- Grafana: 대시보드 시각화
- Loki: 로그 수집 및 분석
- Alertmanager: 알림 규칙 및 라우팅

운영 자동화:
- CI/CD: GitHub Actions + ArgoCD
- Nightly Self-check: 자동 검증
- Release Gate: 품질 게이트 통과 확인
- Auto Rollback: 실패 시 자동 복구

장점:
- 완전 자동화된 모니터링 및 알림
- ROI/SLO 기반 의사결정 자동화
- 피드백 루프로 지속적 개선
- 성숙도 측정으로 시스템 진화 추적
```

---

## 🔄 통합 전략

### Phase 1: 핵심 컴포넌트 추출 및 적응
**기간**: 1-2일  
**목표**: Kubernetes → Cloud Run 환경 변환

#### 1.1 Maturity Exporter (성숙도 측정)
- **원본**: `maturity_exporter_v15.py` (Kubernetes Pod 메트릭 기반)
- **적응**: Cloud Run 리비전 메트릭으로 변환

  ```python
  # 측정 항목
  - 배포 빈도 (Cloud Run 리비전 생성 횟수)
  - 평균 레이턴시 (Cloud Run 요청 레이턴시)
  - 에러율 (4xx, 5xx 비율)
  - 가용성 (Uptime)
  - 캐시 히트율 (Redis 통계)
  - 비용 효율성 (비용/요청 비율)
  ```

- **출력**: JSON 형식 성숙도 스코어 (0-100)
- **저장**: `lumen/exporters/maturity_exporter_cloudrun.py`

#### 1.2 ROI Gate (투자 대비 효과 게이트)
- **원본**: `roi_gate_decider_v19.py` (ROI 임계값 기반 게이트)
- **적응**: GCP 비용 API + 성능 메트릭

  ```python
  # ROI 계산
  ROI = (성능 개선 가치 - 추가 비용) / 추가 비용
  
  # 예시
  Redis 비용: $9.36/month
  요청 비용 절감: $200/month (80% 캐싱 효과)
  ROI = ($200 - $9.36) / $9.36 = 2036% ✅
  
  # 게이트 조건
  - ROI > 500%: PASS
  - 300% < ROI < 500%: WARN
  - ROI < 300%: FAIL (롤백 권장)
  ```

- **저장**: `lumen/gates/roi_gate_cloudrun.py`

#### 1.3 SLO Exporter (서비스 수준 목표)
- **원본**: `slo_exporter_v19.py` (Prometheus 메트릭 기반)
- **적응**: Cloud Monitoring API

  ```python
  # SLO 정의
  - 가용성: >99.5% (월간 최대 3.6시간 다운타임)
  - 레이턴시: P95 <200ms, P99 <500ms
  - 에러율: <0.1% (1000 요청당 1개 이하)
  - 캐시 히트율: >80%
  
  # 알림 조건
  - 가용성 <99%: CRITICAL
  - 레이턴시 P99 >1000ms: WARNING
  - 에러율 >1%: CRITICAL
  - 캐시 히트율 <70%: WARNING
  ```

- **저장**: `lumen/exporters/slo_exporter_cloudrun.py`

#### 1.4 Feedback Graph (피드백 루프)
- **원본**: `feedback_graph_core_v17.py` (메트릭 간 인과관계 그래프)
- **적응**: Redis 캐싱 피드백 루프

  ```python
  # 피드백 루프 예시
  1. 캐시 히트율 감소 감지
  2. Redis TTL 증가 제안
  3. 자동 적용 또는 승인 요청
  4. 효과 측정 (히트율 개선 확인)
  5. 학습 데이터로 저장
  
  # 자동 조정 항목
  - Redis TTL (60s → 300s)
  - L1 캐시 크기 (1000 → 2000 entries)
  - Cold Start 대응 (min_instances 조정)
  ```

- **저장**: `lumen/monitoring/feedback_loop_redis.py`

---

### Phase 2: 모니터링 시스템 통합
**기간**: 2-3일  
**목표**: Prometheus/Grafana → Cloud Monitoring 변환

#### 2.1 메트릭 변환

| Lumen (Prometheus) | ION (Cloud Monitoring) |
|-------------------|----------------------|
| `lumen_maturity_score` | `custom/maturity_score` |
| `lumen_roi_percent` | `custom/roi_percentage` |
| `lumen_slo_availability` | `custom/slo_availability` |
| `lumen_cache_hit_rate` | `custom/cache_hit_rate` |
| `lumen_cost_per_request` | `custom/cost_per_request` |

#### 2.2 대시보드 생성
- **원본**: `grafana_dashboard_v19_prod_roi.json` 등
- **변환**: Cloud Monitoring Dashboard YAML
- **구성**:
  1. 성숙도 스코어 (Maturity Score)
  2. ROI 트렌드 (ROI Trend)
  3. SLO 달성률 (SLO Achievement)
  4. 캐시 성능 (Cache Performance)
  5. 비용 효율성 (Cost Efficiency)
- **저장**: `lumen/dashboards/cloud_monitoring_dashboard.yaml`

#### 2.3 알림 규칙 생성

```yaml
# 예시: ROI 하락 알림
alert: ROI_Degradation
condition: custom/roi_percentage < 300
duration: 15m
notification:
  - slack: #ion-alerts
  - email: ruafieldphase@gmail.com
action: 
  - 자동 조사 시작
  - 롤백 권장 메시지

# 예시: 캐시 히트율 저하 알림
alert: Cache_HitRate_Low
condition: custom/cache_hit_rate < 70
duration: 10m
notification:
  - slack: #ion-alerts
action:
  - Redis TTL 자동 증가
  - 피드백 그래프 업데이트
```

---

### Phase 3: 예산/성능 게이트 통합
**기간**: 1-2일  
**목표**: GCP Budget Alert + ROI Gate + 자동 롤백

#### 3.1 GCP Budget Alert 설정

```python
# budget_alert_setup.py
import google.cloud.billing_budgets_v1

budget = {
    "display_name": "ION API Monthly Budget",
    "budget_filter": {
        "projects": ["projects/naeda-genesis"],
        "services": ["services/cloud-run", "services/redis"]
    },
    "amount": {
        "specified_amount": {"units": 200}  # $200/month
    },
    "threshold_rules": [
        {"threshold_percent": 0.8, "spend_basis": "CURRENT_SPEND"},  # 80% = $160
        {"threshold_percent": 0.9, "spend_basis": "CURRENT_SPEND"},  # 90% = $180
        {"threshold_percent": 1.0, "spend_basis": "CURRENT_SPEND"},  # 100% = $200
    ],
    "notifications_rule": {
        "pubsub_topic": "projects/naeda-genesis/topics/budget-alerts",
        "monitoring_notification_channels": ["slack-webhook"]
    }
}
```

#### 3.2 ROI Gate 통합

```python
# roi_gate_integration.py
class ROIGate:
    def check(self):
        # 1. 현재 비용 조회
        current_cost = get_billing_cost(days=30)
        
        # 2. 성능 개선 가치 계산
        cache_savings = calculate_cache_savings()
        
        # 3. ROI 계산
        roi = (cache_savings - redis_cost) / redis_cost
        
        # 4. 게이트 결정
        if roi > 5.0:  # 500%
            return "PASS", "ROI excellent"
        elif roi > 3.0:  # 300%
            return "WARN", "ROI acceptable"
        else:
            return "FAIL", "ROI insufficient, consider rollback"
        
        # 5. Slack 알림
        send_slack_notification(roi, decision)
        
        # 6. 자동 조치
        if decision == "FAIL":
            trigger_rollback_recommendation()
```

#### 3.3 자동 롤백 로직

```python
# auto_rollback.py
def auto_rollback_decision():
    # 조건 체크
    if (
        slo_availability < 99.0 or
        error_rate > 1.0 or
        roi < 3.0 or
        cost > budget_threshold
    ):
        # 롤백 권장
        send_alert("Auto rollback recommended")
        
        # 수동 승인 대기 (5분)
        if not manual_approval_received(timeout=300):
            # 자동 롤백 실행
            execute_rollback()
            log_rollback_event()
            send_slack_notification("Auto rollback completed")
```

---

### Phase 4: 피드백 루프 통합
**기간**: 2-3일  
**목표**: Redis 캐싱 자동 최적화

#### 4.1 피드백 수집

```python
# feedback_collector.py
class FeedbackCollector:
    def collect_metrics(self):
        return {
            "cache_hit_rate": get_cache_hit_rate(),
            "latency_p95": get_latency_percentile(95),
            "latency_p99": get_latency_percentile(99),
            "error_rate": get_error_rate(),
            "cost_per_request": get_cost_per_request(),
            "redis_memory_used": get_redis_memory(),
        }
    
    def analyze_trends(self, days=7):
        # 7일간 트렌드 분석
        metrics = []
        for day in range(days):
            metrics.append(self.collect_metrics())
        
        return {
            "hit_rate_trend": calculate_trend(metrics, "cache_hit_rate"),
            "latency_trend": calculate_trend(metrics, "latency_p95"),
            "cost_trend": calculate_trend(metrics, "cost_per_request"),
        }
```

#### 4.2 자동 조정 정책

```python
# adaptive_policy.py
class AdaptivePolicy:
    def adjust_cache_ttl(self):
        hit_rate = get_cache_hit_rate()
        
        if hit_rate < 70:
            # 히트율 낮음 → TTL 증가
            new_ttl = min(current_ttl * 1.5, 3600)
            update_redis_ttl(new_ttl)
            log_adjustment("TTL increased", current_ttl, new_ttl)
        
        elif hit_rate > 90:
            # 히트율 매우 높음 → TTL 감소 (메모리 절약)
            new_ttl = max(current_ttl * 0.8, 300)
            update_redis_ttl(new_ttl)
            log_adjustment("TTL decreased", current_ttl, new_ttl)
    
    def adjust_min_instances(self):
        cold_start_rate = get_cold_start_rate()
        cost = get_current_cost()
        
        if cold_start_rate > 10 and cost < budget * 0.8:
            # Cold Start 많고 예산 여유 있음 → min_instances 증가
            update_cloud_run_config(min_instances=1)
            log_adjustment("min_instances increased to 1")
        
        elif cost > budget * 0.9:
            # 예산 초과 위험 → min_instances 감소
            update_cloud_run_config(min_instances=0)
            log_adjustment("min_instances decreased to 0")
```

---

## 📁 디렉터리 구조

```
LLM_Unified/ion-mentoring/lumen/
├── exporters/
│   ├── maturity_exporter_cloudrun.py      # 성숙도 측정 (Cloud Run 적응)
│   ├── slo_exporter_cloudrun.py           # SLO 추적 (Cloud Monitoring)
│   ├── roi_exporter_cloudrun.py           # ROI 계산 (GCP Billing API)
│   └── __init__.py
├── gates/
│   ├── roi_gate_cloudrun.py               # ROI 게이트 (예산 기반)
│   ├── maturity_gate.py                   # 성숙도 게이트
│   ├── slo_gate.py                        # SLO 게이트
│   └── __init__.py
├── monitoring/
│   ├── feedback_loop_redis.py             # Redis 피드백 루프
│   ├── adaptive_policy.py                 # 자동 조정 정책
│   ├── metrics_collector.py               # 메트릭 수집기
│   └── __init__.py
├── dashboards/
│   ├── cloud_monitoring_dashboard.yaml    # Cloud Monitoring 대시보드
│   ├── maturity_dashboard.json            # 성숙도 대시보드
│   └── roi_slo_dashboard.json             # ROI/SLO 대시보드
├── scripts/
│   ├── setup_lumen_monitoring.sh          # 초기 설정 스크립트
│   ├── deploy_dashboards.sh               # 대시보드 배포
│   ├── test_roi_gate.sh                   # ROI 게이트 테스트
│   └── manual_rollback.sh                 # 수동 롤백 스크립트
└── docs/
    ├── INTEGRATION_GUIDE.md               # 통합 가이드 (이 문서)
    ├── LUMEN_RUNBOOK.md                   # 운영 가이드
    ├── ROI_GATE_REFERENCE.md              # ROI 게이트 레퍼런스
    └── SLO_DEFINITIONS.md                 # SLO 정의
```

---

## 🚀 실행 계획

### Week 1: 핵심 컴포넌트 구축
- Day 1-2: Maturity/ROI/SLO Exporter 개발
- Day 3-4: ROI Gate 및 자동 롤백 로직 구현
- Day 5: 통합 테스트

### Week 2: 모니터링 통합
- Day 1-2: Cloud Monitoring 메트릭 및 대시보드
- Day 3-4: 알림 규칙 및 Slack 통합
- Day 5: GCP Budget Alert 설정

### Week 3: 피드백 루프 및 최적화
- Day 1-2: 피드백 루프 구현
- Day 3-4: Adaptive Policy 구현
- Day 5: 7일 검증 시작

### Week 4: 검증 및 문서화
- Day 1-5: 7일 검증 데이터 수집
- Day 6-7: 최종 평가 및 문서화

---

## ✅ 성공 기준

### 기능 요구사항
- [x] Maturity Exporter 정상 작동 (스코어 0-100 출력)
- [ ] ROI Gate 통합 (GCP Billing API 연동)
- [ ] SLO Exporter 정상 작동 (가용성, 레이턴시, 에러율)
- [ ] Feedback Loop 구현 (Redis TTL 자동 조정)
- [ ] Cloud Monitoring 대시보드 배포
- [ ] Slack 알림 연동
- [ ] 자동 롤백 로직 작동

### 성능 목표
- [ ] 비용: $200/month 이하 유지
- [ ] 캐시 히트율: >80%
- [ ] 레이턴시 P95: <200ms
- [ ] 가용성: >99.5%
- [ ] 에러율: <0.1%

### 운영 효율
- [ ] 수동 개입 감소: >70%
- [ ] 알림 정확도: >90% (False Positive <10%)
- [ ] 자동 조정 성공률: >80%

---

## 📚 참고 자료

### 루멘 원본 문서
- `ChatGPT-Lumen v1.7 복원 진행.md` - Track A/B/C 전환
- `ChatGPT-Lumen v1.5 quick start.md` - 초기 설정 가이드
- `RELEASE_NOTES_v1_7_FINAL.md` - v1.7 릴리즈 노트

### ION 시스템 문서
- `docs/phase14_plan.md` - Phase 14 비용 최적화 계획
- `깃코_Phase14_Redis캐싱_활성화_완료_2025-10-25.md` - Redis 캐싱 완료 보고서

### GCP 문서
- Cloud Monitoring API
- Cloud Billing API
- Budget Alerts
- Cloud Run Monitoring

---

**다음 단계**: Phase 1 시작 - Maturity Exporter 개발
