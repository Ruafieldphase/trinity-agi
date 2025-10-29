# Phase 4: Canary Deployment System

**Status**: 🚧 In Progress  
**Started**: 2025-10-18  
**Traffic Split**: 5% Canary / 95% Legacy

---

## 개요

Phase 4는 카나리 배포 시스템을 구축하여 신규 기능을 프로덕션 환경에 안전하게 배포할 수 있도록 합니다. 사용자 트래픽의 5%를 신규 버전(canary)으로 라우팅하고, 95%는 기존 버전(legacy)으로 유지합니다.

## 주요 컴포넌트

### 1. Canary Router (`app/routing/canary_router.py`)

사용자 ID 기반으로 결정적으로 트래픽을 분배합니다.

**특징**:

- 일관된 해싱 알고리즘 사용 (동일 사용자 → 동일 버전)
- 설정 가능한 카나리 비율 (기본 5%)
- 엔드포인트별 카나리 활성화 제어

**핵심 메서드**:

```python
CanaryRouter.get_deployment_version(user_id: str) -> DeploymentVersion
CanaryRouter.is_canary_user(user_id: str) -> bool
```

### 2. Canary Metrics Collector (`app/middleware/canary_metrics.py`)

버전별 성능 메트릭을 수집하고 비교합니다.

**추적 메트릭**:

- 요청 수 (Request Count)
- 에러율 (Error Rate)
- 평균 응답 시간 (Average Response Time)
- P95/P99 응답 시간
- 엔드포인트별 메트릭

**핵심 메서드**:

```python
collector.record_request(endpoint, method, user_id, version, status_code, response_time_ms)
collector.get_metrics_summary() -> Dict[str, Any]
collector.get_endpoint_metrics() -> Dict[str, Any]
```

### 3. Canary Deployment Config

배포 설정을 중앙에서 관리합니다.

**설정 항목**:

- `enabled`: 카나리 배포 활성화 여부
- `canary_percentage`: 카나리 트래픽 비율 (0-100)
- `endpoints_to_canary`: 카나리를 적용할 엔드포인트 목록

## 배포 전략

### 트래픽 분배

```plaintext
전체 사용자
├─ 95% → Legacy (Phase 3 안정 버전)
└─ 5%  → Canary (Phase 4 신규 기능)
```

### 사용자 라우팅

- **결정적 해싱**: MD5 해시를 사용하여 user_id를 0-99 범위로 매핑
- **일관성**: 동일 사용자는 세션 간 동일 버전 유지
- **공정성**: 5% 비율이 통계적으로 균등하게 분배됨

### 모니터링 대상 엔드포인트

```python
[
    "/api/v2/recommend/personalized",
    "/api/v2/recommend/compare",
    "/api/v2/conversations/start",
    "/api/v2/conversations/{session_id}/turn",
    "/api/v2/conversations/{session_id}",
    "/api/v2/conversations/{session_id}/close",
    "/api/v2/conversations"
]
```

## 성공 기준 (SLO)

카나리 버전이 다음 조건을 만족하면 100% 롤아웃 가능:

### 1. 에러율

- **기준**: Legacy 대비 에러율 증가 < 0.5%
- **측정**: `(canary_error_rate - legacy_error_rate) < 0.5%`

### 2. 응답 시간

- **기준**: P95 응답 시간 증가 < 10%
- **측정**: `(canary_p95 - legacy_p95) / legacy_p95 < 0.1`

### 3. 최소 데이터

- **기준**: 카나리 최소 요청 수 > 1,000
- **목적**: 통계적 유의성 확보

## 롤백 트리거

다음 조건 중 하나라도 만족하면 자동 롤백:

1. **에러율 급증**: Canary error rate > 5%
2. **응답 시간 악화**: Canary P95 > 2초
3. **가용성 저하**: Canary 가용성 < 99%

## 사용 예시

### 메트릭 조회

```python
from app.middleware.canary_metrics import get_metrics_collector

collector = get_metrics_collector()
summary = collector.get_metrics_summary()

print(f"Legacy: {summary['legacy']}")
print(f"Canary: {summary['canary']}")
print(f"Comparison: {summary['comparison']}")
```

### 카나리 비율 조정

```python
from app.routing.canary_router import get_canary_config

config = get_canary_config()
config.update_canary_percentage(10)  # 5% → 10%
```

### 엔드포인트 추가/제거

```python
config.add_endpoint("/api/v2/new_feature")
config.remove_endpoint("/api/v2/old_feature")
```

## 테스트

### 통합 테스트

```bash
pytest tests/integration/test_phase4_integration.py -v
```

**테스트 커버리지**:

- 권장사항 엔진 엔드포인트 (5 테스트)
- 다중 턴 대화 엔드포인트 (8 테스트)
- 의존성 주입 검증 (2 테스트)
- 에러 핸들링 (2 테스트)
- 성능 벤치마킹 (2 테스트)

### 로컬 테스트

```bash
# 특정 user_id로 카나리 라우팅 확인
curl -X POST http://localhost:8080/api/v2/recommend/personalized \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_canary_user",
    "query": "test query"
  }'
```

## 모니터링 대시보드

### 메트릭 요약 엔드포인트

```bash
GET /api/v2/admin/canary/metrics
```

**응답 예시**:

```json
{
  "legacy": {
    "version": "legacy",
    "request_count": 9500,
    "error_count": 5,
    "error_rate": "0.05%",
    "avg_response_time_ms": "250.00",
    "p95_response_time_ms": "450.00",
    "p99_response_time_ms": "600.00"
  },
  "canary": {
    "version": "canary",
    "request_count": 500,
    "error_count": 1,
    "error_rate": "0.20%",
    "avg_response_time_ms": "230.00",
    "p95_response_time_ms": "420.00",
    "p99_response_time_ms": "550.00"
  },
  "comparison": {
    "error_rate_difference": "+0.15%",
    "response_time_improvement": "+8.00%",
    "canary_p95_response_time": "420.00ms",
    "legacy_p95_response_time": "450.00ms",
    "traffic_split": {
      "legacy_requests": 9500,
      "canary_requests": 500,
      "legacy_percentage": "95.0%",
      "canary_percentage": "5.0%"
    }
  }
}
```

## 배포 체크리스트

### 카나리 배포 시작 전

- [ ] 모든 Phase 4 통합 테스트 통과
- [ ] 메트릭 수집기 동작 확인
- [ ] 롤백 절차 준비
- [ ] 모니터링 알림 설정 (Slack, PagerDuty)
- [ ] 카나리 비율 5%로 설정

### 카나리 배포 진행 중

- [ ] 1시간 모니터링: 에러율, 응답 시간 확인
- [ ] 6시간 모니터링: 메트릭 추이 분석
- [ ] 24시간 모니터링: 일간 패턴 검증

### 100% 롤아웃 전

- [ ] SLO 3가지 모두 만족
- [ ] 최소 1,000건 카나리 요청 처리
- [ ] 수동 E2E 테스트 통과
- [ ] 경영진 승인

## 향후 계획

### 단기 (1-2주)

- [ ] 카나리 5% → 10% 점진적 증가
- [ ] 추가 엔드포인트 카나리 적용
- [ ] Grafana 대시보드 구축

### 중기 (1개월)

- [ ] 자동 롤백 로직 구현
- [ ] A/B 테스트 프레임워크 확장
- [ ] 멀티 버전 지원 (3개 이상 버전)

### 장기 (3개월)

- [ ] 블루-그린 배포 지원
- [ ] 지역별 카나리 배포
- [ ] 실시간 트래픽 조정

---

## 참고 문서

- [Phase 3 Executive Summary](PHASE3_EXECUTIVE_SUMMARY.md)
- [CHANGELOG](../CHANGELOG.md)
- [Architecture Overview](ARCHITECTURE.md)

---

**Last Updated**: 2025-10-18  
**Author**: GitHub Copilot  
**Status**: Draft
