# Phase 4 - 카나리 배포 전략 (Day 4-7)
## 5% 사용자를 대상으로 한 안전한 프로덕션 배포

**작성일**: 2025-10-18
**배포 일정**: 2025-10-22 (Day 4) ~ 2025-10-28 (Day 7)
**목표**: 프로덕션 환경에서 Phase 4 기능 안정성 검증

---

## 📋 카나리 배포 개요

### 배포 전략

```
┌─────────────────────────────────────────────────┐
│ 카나리 배포 (Canary Deployment)                 │
├─────────────────────────────────────────────────┤
│                                                 │
│ ◇ Phase 3 (기존)    : 95% 트래픽              │
│   ├─ ResonanceRouter 사용                      │
│   ├─ 기존 추천 로직                           │
│   └─ 안정성 검증됨 ✅                          │
│                                                 │
│ ◈ Phase 4 (신규)    : 5% 트래픽 (카나리)     │
│   ├─ EnsembleRecommendationEngine 사용         │
│   ├─ MultiTurnConversationEngine 사용          │
│   └─ 실시간 모니터링 🔍                        │
│                                                 │
│ 메트릭 수집: 모든 요청/응답                    │
│ 비율 계산: 95% vs 5% 비교 분석                │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 목표

**기술적 목표**:
- ✅ 에러율 < 0.5% 확인
- ✅ 응답 시간 P95 < 100ms 확인
- ✅ 가용성 > 99.95% 확인
- ✅ 메모리 안정성 검증

**비즈니스 목표**:
- ✅ 신규 기능 정상 작동 확인
- ✅ 사용자 피드백 수집
- ✅ 이슈 조기 발견
- ✅ 다음 단계 (A/B 테스트) 준비

---

## 🏗️ 배포 인프라 설정

### 1. 트래픽 라우팅 설정

**구현 위치**: `app/api/v2_phase4_routes.py` 또는 별도 라우팅 미들웨어

```python
# 카나리 배포 라우터
import random
from enum import Enum

class DeploymentVersion(Enum):
    LEGACY = "legacy"      # Phase 3 (95%)
    CANARY = "canary"      # Phase 4 (5%)

def get_deployment_version(user_id: str) -> DeploymentVersion:
    """
    사용자 ID를 기반으로 배포 버전 결정

    결정적 해싱으로 동일 사용자는 항상 같은 버전으로 라우팅됨

    Args:
        user_id: 사용자 고유 ID

    Returns:
        DeploymentVersion: LEGACY 또는 CANARY
    """
    # 사용자 ID 기반 결정적 분배
    hash_value = hash(user_id) % 100

    if hash_value < 5:  # 5% 확률
        return DeploymentVersion.CANARY
    else:
        return DeploymentVersion.LEGACY

# 엔드포인트에서 사용
@router.post("/api/v2/recommend/personalized")
async def recommend_personalized(
    request: PersonalizedRecommendationRequest,
    db: Database = Depends(get_db)
):
    """개인화 추천 - 카나리 배포"""

    deployment = get_deployment_version(request.user_id)

    if deployment == DeploymentVersion.CANARY:
        # Phase 4 엔진 사용
        result = await get_recommendation_engine().recommend(request)
        metrics.record_recommendation(
            user_id=request.user_id,
            version="canary",
            result=result
        )
    else:
        # Phase 3 레거시 사용
        result = await legacy_recommender.recommend(request)
        metrics.record_recommendation(
            user_id=request.user_id,
            version="legacy",
            result=result
        )

    return result
```

### 2. 메트릭 수집 미들웨어

**파일**: `app/middleware/canary_metrics.py` (신규)

```python
from datetime import datetime
from typing import Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

class CanaryMetricsMiddleware:
    """카나리 배포 메트릭 수집 미들웨어"""

    def __init__(self):
        self.metrics = {
            "legacy": {
                "request_count": 0,
                "error_count": 0,
                "total_response_time_ms": 0,
                "responses": []
            },
            "canary": {
                "request_count": 0,
                "error_count": 0,
                "total_response_time_ms": 0,
                "responses": []
            }
        }

    async def __call__(self, request: Request, call_next):
        """미들웨어 실행"""
        start_time = time.time()

        # 요청 처리
        try:
            response = await call_next(request)
            response_time_ms = (time.time() - start_time) * 1000

            # 메트릭 기록
            version = request.state.get("deployment_version", "legacy")
            self._record_metrics(version, response.status_code, response_time_ms)

            # 응답 헤더에 메타데이터 추가
            response.headers["X-Deployment-Version"] = version
            response.headers["X-Response-Time-Ms"] = str(response_time_ms)

            return response
        except Exception as e:
            # 에러 메트릭 기록
            version = request.state.get("deployment_version", "legacy")
            self._record_error(version, str(e))
            raise

    def _record_metrics(self, version: str, status_code: int, response_time_ms: float):
        """메트릭 기록"""
        self.metrics[version]["request_count"] += 1
        self.metrics[version]["total_response_time_ms"] += response_time_ms

        if status_code >= 400:
            self.metrics[version]["error_count"] += 1

        self.metrics[version]["responses"].append({
            "timestamp": datetime.now().isoformat(),
            "status_code": status_code,
            "response_time_ms": response_time_ms
        })

    def _record_error(self, version: str, error_msg: str):
        """에러 기록"""
        self.metrics[version]["error_count"] += 1
        logger.error(f"Error in {version} deployment: {error_msg}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """메트릭 요약"""
        summary = {}

        for version, data in self.metrics.items():
            request_count = data["request_count"]
            error_count = data["error_count"]
            total_time = data["total_response_time_ms"]

            summary[version] = {
                "request_count": request_count,
                "error_count": error_count,
                "error_rate": (error_count / request_count * 100) if request_count > 0 else 0,
                "avg_response_time_ms": (total_time / request_count) if request_count > 0 else 0
            }

        return summary
```

### 3. 헬스 체크 및 자동 롤백

**파일**: `app/health/canary_health_check.py` (신규)

```python
from enum import Enum
from typing import Dict, Any
import asyncio

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class CanaryHealthCheck:
    """카나리 배포 헬스 체크"""

    # SLA 기준
    SLA_ERROR_RATE = 0.5  # 0.5%
    SLA_P95_RESPONSE_TIME = 100  # ms
    SLA_AVAILABILITY = 99.95  # %

    def __init__(self, metrics_middleware: CanaryMetricsMiddleware):
        self.metrics = metrics_middleware
        self.check_interval = 60  # 1분마다 확인

    async def run_continuous_health_check(self):
        """지속적인 헬스 체크"""
        while True:
            status = await self.perform_health_check()

            if status == HealthStatus.UNHEALTHY:
                logger.critical("❌ Canary deployment is UNHEALTHY - initiating rollback")
                await self.trigger_rollback()
            elif status == HealthStatus.DEGRADED:
                logger.warning("⚠️ Canary deployment is DEGRADED - monitoring closely")
            else:
                logger.info("✅ Canary deployment is HEALTHY")

            await asyncio.sleep(self.check_interval)

    async def perform_health_check(self) -> HealthStatus:
        """헬스 체크 수행"""
        metrics = self.metrics.get_metrics_summary()
        canary_metrics = metrics.get("canary", {})

        # 요청 수가 충분한지 확인 (최소 10개)
        if canary_metrics.get("request_count", 0) < 10:
            return HealthStatus.HEALTHY  # 데이터 부족 - 계속 모니터링

        error_rate = canary_metrics.get("error_rate", 0)
        avg_response_time = canary_metrics.get("avg_response_time_ms", 0)

        # SLA 확인
        checks = {
            "error_rate": error_rate <= self.SLA_ERROR_RATE,
            "response_time": avg_response_time <= self.SLA_P95_RESPONSE_TIME
        }

        # 결과 판단
        all_passed = all(checks.values())
        if all_passed:
            return HealthStatus.HEALTHY

        failed_checks = [k for k, v in checks.items() if not v]
        if len(failed_checks) == 1:
            logger.warning(f"Degraded: {failed_checks[0]} exceeded SLA")
            return HealthStatus.DEGRADED
        else:
            logger.error(f"Unhealthy: {', '.join(failed_checks)} exceeded SLA")
            return HealthStatus.UNHEALTHY

    async def trigger_rollback(self):
        """자동 롤백 트리거"""
        # 1. 카나리 배포 비활성화
        # 2. 모든 트래픽을 레거시로 라우팅
        # 3. 롤백 이벤트 로깅
        # 4. 알림 전송

        logger.critical("🔄 Rolling back canary deployment...")

        # 배포 설정 업데이트
        # (실제 구현은 환경에 따라 다름)

        # 알림 전송
        await self._send_alert({
            "severity": "CRITICAL",
            "message": "Canary deployment rolled back due to health check failure",
            "metrics": self.metrics.get_metrics_summary()
        })

    async def _send_alert(self, alert_data: Dict[str, Any]):
        """알림 전송 (Slack, Email 등)"""
        # Slack 웹훅 또는 다른 알림 채널로 전송
        logger.error(f"ALERT: {alert_data}")
```

---

## 📊 모니터링 및 메트릭

### 1. 수집할 메트릭

#### 기술적 메트릭

```
카나리 배포 (Phase 4):
├─ 요청 수
├─ 에러율 (%)
├─ 응답 시간 (P50, P95, P99)
├─ 처리량 (RPS)
├─ 메모리 사용량
├─ CPU 사용률
└─ 외부 API 호출 성공률

레거시 배포 (Phase 3):
├─ 요청 수
├─ 에러율 (%)
├─ 응답 시간 (P50, P95, P99)
├─ 처리량 (RPS)
├─ 메모리 사용량
├─ CPU 사용률
└─ 외부 API 호출 성공률

비교 메트릭:
├─ 성능 차이 (%)
├─ 에러율 차이
├─ 응답 시간 개선도
└─ 리소스 효율성
```

#### 비즈니스 메트릭

```
추천 관련:
├─ 추천 수용률 (%)
├─ 클릭율 (CTR)
├─ 전환율 (CVR)
└─ 사용자 만족도 점수

대화 관련 (신규 기능):
├─ 세션 생성 수
├─ 평균 턴 수
├─ 대화 완료율
├─ 사용자 만족도 점수
└─ 재방문율
```

### 2. 모니터링 대시보드 설정

**파일**: `docs/PHASE4_CANARY_MONITORING_DASHBOARD.md` (별도 생성)

```
대시보드 항목:

1. 실시간 메트릭
   ├─ 지난 5분: 요청 수, 에러율, 응답 시간
   ├─ 카나리 vs 레거시 비교
   └─ SLA 상태

2. 성능 추이 (시계열)
   ├─ 에러율 추이
   ├─ 응답 시간 추이
   └─ 처리량 추이

3. 비즈니스 메트릭
   ├─ 사용자 만족도
   ├─ 기능 채택율
   └─ 이탈율

4. 알림 및 이벤트
   ├─ SLA 위반
   ├─ 높은 에러율
   ├─ 성능 저하
   └─ 자동 롤백 이벤트
```

---

## ⚙️ 배포 절차

### Day 4: 배포 실행

**시간**: 14:00 UTC (야간 트래픽 최저 시간)

**체크리스트**:

```
배포 전 (13:00-13:55):
□ 모든 서버 헬스 체크 ✅
□ 데이터베이스 상태 확인 ✅
□ 캐시 서버 상태 확인 ✅
□ 모니터링 대시보드 활성화 ✅
□ Slack 채널 활성화 ✅
□ 온콜 팀 대기 ✅

배포 중 (14:00-14:05):
□ 카나리 배포 설정 활성화 (5%)
□ 헬스 체크 시작
□ 메트릭 수집 시작
□ 실시간 모니터링 시작
□ 초기 요청 수집 (최소 10개)

배포 후 (14:05+):
□ 1시간마다 메트릭 검토
□ 에러율 모니터링
□ 응답 시간 모니터링
□ 사용자 피드백 모니터링
□ 자동 롤백 준비
```

### Day 5-6: 안정성 확인

**메트릭 검토** (매일 2회: 08:00, 14:00 UTC):

```
필수 확인 사항:

1. 에러율
   ├─ 카나리: < 0.5% ✅
   └─ 레거시: < 0.5% ✅

2. 응답 시간
   ├─ 카나리 P95: < 100ms ✅
   └─ 레거시 P95: < 100ms ✅

3. 메모리 사용
   ├─ 카나리: 안정적 ✅
   └─ 레거시: 안정적 ✅

4. 처리량
   ├─ 카나리: 정상 분배 (5%) ✅
   └─ 레거시: 정상 분배 (95%) ✅
```

### Day 7: 결과 분석 및 다음 단계

**최종 검토**:

```
성공 기준:

✅ 에러율 < 0.5%
✅ 응답 시간 P95 < 100ms
✅ 가용성 > 99.95%
✅ 사용자 피드백 긍정적
✅ 자동 롤백 미트리거

결론:
□ 카나리 배포 성공 → Day 8-21 A/B 테스트로 진행
□ 문제 발견 → 개선 후 재배포 또는 중단

다음 단계 (Day 8-21):
- 50% A/B 테스트 시작
- 통계적 유의성 검증
- 최종 배포 결정
```

---

## 🔄 롤백 절차

### 자동 롤백 조건

```
롤백이 자동으로 트리거되는 경우:

1. 에러율 > 1% (2배 SLA 초과)
   ├─ 즉시 알림
   └─ 5분 내 롤백

2. 응답 시간 P95 > 200ms (2배 SLA 초과)
   ├─ 즉시 알림
   └─ 5분 내 롤백

3. 메모리 사용 > 2GB (정상의 2배)
   ├─ 즉시 알림
   └─ 5분 내 롤백

4. 연속 10개 요청 모두 실패
   ├─ 즉시 알림
   └─ 즉시 롤백
```

### 수동 롤백 절차

**상황**: 자동 롤백이 미트리거되었으나 문제 발견

```
1단계: 알림 (즉시)
  └─ Slack #phase4-critical 채널에 메시지
  └─ 온콜 팀 호출
  └─ 매니저 알림

2단계: 진단 (1-5분)
  ├─ 문제의 근본 원인 파악
  ├─ 영향 범위 확인
  ├─ 롤백 필요성 판단
  └─ 결과 기록

3단계: 롤백 실행 (1-3분)
  ├─ 카나리 배포 비활성화
  ├─ 모든 트래픽 → 레거시로 라우팅
  ├─ 상태 확인
  └─ 완료 알림

4단계: 사후 분석 (24시간 내)
  ├─ 근본 원인 분석
  ├─ 개선 방안 수립
  ├─ 팀 공유
  └─ 문서화
```

---

## 📚 배포 런북 체크리스트

### 배포 전

- [ ] 모든 단위 테스트 통과 ✅
- [ ] 모든 통합 테스트 통과 ✅
- [ ] 성능 테스트 통과 ✅
- [ ] 코드 리뷰 완료 ✅
- [ ] 보안 검사 완료 ✅
- [ ] 카나리 배포 설정 확인 ✅
- [ ] 모니터링 대시보드 준비 ✅
- [ ] 온콜 팀 준비 ✅

### 배포 중

- [ ] 배포 시간 기록
- [ ] 초기 헬스 체크 확인
- [ ] 메트릭 수집 시작 확인
- [ ] 초기 요청 처리 확인
- [ ] 에러 모니터링 시작
- [ ] 실시간 대시보드 감시

### 배포 후 (Day 4-7)

- [ ] 일일 메트릭 검토
- [ ] 에러율 확인 (< 0.5%)
- [ ] 응답 시간 확인 (P95 < 100ms)
- [ ] 메모리 안정성 확인
- [ ] 사용자 피드백 수집
- [ ] 문제 해결 (발생 시)
- [ ] 최종 결과 정리

---

## 📝 예상 결과

### 성공 시나리오

```
Day 4: 배포 완료 ✅
├─ 초기 오류 없음
├─ 메트릭 수집 시작
└─ 모니터링 정상

Day 5-6: 안정성 확인 ✅
├─ 에러율 < 0.5%
├─ 응답 시간 양호
├─ 메모리 안정적
└─ 사용자 피드백 긍정적

Day 7: 결과 분석 ✅
├─ 모든 SLA 달성
├─ A/B 테스트 준비 완료
└─ 다음 단계 진행
```

### 실패 시나리오

```
Day 4: 배포 후 문제 발생
├─ 높은 에러율 (> 1%)
├─ 자동 롤백 트리거
└─ 원인 분석 시작

Day 5: 문제 해결
├─ 버그 수정
├─ 성능 최적화
└─ 재배포 준비

Day 6: 재배포
├─ 개선된 코드 배포
└─ 메트릭 재수집

Day 7: 재검증
├─ SLA 확인
└─ 다음 단계 결정
```

---

## 🎯 성공 기준

**카나리 배포 성공 = 다음 모든 조건 충족**:

1. ✅ 에러율 < 0.5% (지난 48시간)
2. ✅ 응답 시간 P95 < 100ms (지난 48시간)
3. ✅ 가용성 > 99.95% (지난 48시간)
4. ✅ 자동 롤백 미트리거
5. ✅ 사용자 피드백 86% 이상 긍정적
6. ✅ 추가 이슈 미발견

**이 조건들이 모두 충족되면, Day 8-21 A/B 테스트로 진행**

---

**상태**: 📋 **준비 완료 (배포 예정: 2025-10-22)**
**다음**: 🚀 **Day 4에 카나리 배포 시작**

작성자: Claude AI Agent (세나의 판단)
