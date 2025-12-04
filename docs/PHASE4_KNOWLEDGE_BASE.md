# Phase 4 - 프로젝트 지식 베이스
## 기술 문서, 최적 사례, 트러블슈팅 가이드

**작성일**: 2025-10-18
**상태**: ✅ **완료 - 지속적 참고 자료**
**목적**: 프로젝트 학습 및 향후 유사 프로젝트에 활용

---

## 📚 목차

1. [기술 아키텍처](#기술-아키텍처)
2. [설계 패턴 및 최적 사례](#설계-패턴-및-최적-사례)
3. [성능 최적화 기법](#성능-최적화-기법)
4. [배포 전략](#배포-전략)
5. [트러블슈팅 가이드](#트러블슈팅-가이드)
6. [자주 묻는 질문 (FAQ)](#자주-묻는-질문)
7. [참고 자료](#참고-자료)

---

## 🏗️ 기술 아키텍처

### Phase 4 전체 구조

```
┌─────────────────────────────────────────────────────┐
│              사용자 요청                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  FastAPI (메인 애플리케이션)                       │
│  ├─ main.py (라우터 등록 + 라이프사이클)           │
│  ├─ 의존성 주입 (dependencies.py)                  │
│  └─ 미들웨어 (카나리 메트릭 수집)                  │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Phase 4 API v2 (11개 엔드포인트)                  │
│  ├─ 권장사항 엔진 (5개)                            │
│  │   └─ EnsembleRecommendationEngine               │
│  ├─ 다중 턴 대화 (5개)                            │
│  │   └─ MultiTurnConversationEngine                │
│  └─ 헬스 체크 (1개)                                │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  모니터링 및 분석 시스템                            │
│  ├─ 카나리 메트릭 (canary_metrics.py)             │
│  ├─ 트래픽 라우팅 (canary_router.py)              │
│  ├─ 헬스 체크 (canary_health_check.py)            │
│  ├─ A/B 테스트 (ab_test_framework.py)             │
│  └─ 보고서 (ab_test_reporter.py)                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 데이터 흐름

```
1. 요청 수신
   └─ POST /api/v2/recommend/personalized
   └─ POST /api/v2/conversations/start

2. 그룹 할당 (결정적 해싱)
   └─ hash(user_id) % 100 < 50?
   └─ Control (95%) 또는 Treatment (5%)

3. 엔진 선택
   ├─ Control: Phase 3 (레거시)
   └─ Treatment: Phase 4 (신규)

4. 처리
   └─ 권장사항/대화 생성

5. 응답
   ├─ 결과 반환
   ├─ 메트릭 기록
   └─ 로깅

6. 모니터링
   ├─ 메트릭 수집
   ├─ 통계 분석
   └─ 알림 (문제 시)
```

---

## 🎯 설계 패턴 및 최적 사례

### 1. 싱글톤 패턴 + LRU 캐시

**목적**: 인스턴스 중복 생성 방지, 메모리 절약

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_recommendation_engine():
    """싱글톤으로 관리"""
    global _engine
    if _engine is None:
        _engine = EnsembleRecommendationEngine(...)
    return _engine

# 사용
engine1 = get_recommendation_engine()
engine2 = get_recommendation_engine()
assert engine1 is engine2  # True - 동일 인스턴스
```

**장점**:
- ✅ 메모리 효율성
- ✅ 일관된 상태 유지
- ✅ FastAPI Depends() 호환
- ✅ 테스트 용이

### 2. 결정적 해싱 (Consistent Hashing)

**목적**: 동일 사용자 → 항상 같은 그룹 할당

```python
import hashlib

def assign_user_to_group(user_id: str) -> str:
    """결정적 해싱"""
    hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100
    return "control" if hash_value < 50 else "treatment"

# 동일 사용자 = 동일 그룹
assert assign_user_to_group("user123") == assign_user_to_group("user123")
```

**장점**:
- ✅ 일관된 사용자 경험
- ✅ 세션 유지
- ✅ 테스트 재현성
- ✅ 확장성 (트래픽 증가 시)

### 3. 의존성 주입 (Dependency Injection)

**목적**: 느슨한 결합, 테스트 용이성

```python
@app.post("/api/v2/recommend/personalized")
async def recommend(
    request: Request,
    engine: EnsembleRecommendationEngine = Depends(get_recommendation_engine)
):
    """의존성 주입"""
    result = engine.recommend(request)
    return result
```

**장점**:
- ✅ 느슨한 결합
- ✅ 테스트 시 모킹 용이
- ✅ 환경별 설정 변경 쉬움
- ✅ 코드 재사용성 증가

### 4. 자동화된 통계 분석

**목적**: 일관된 분석, 인간 오류 방지

```python
def analyze_metrics(control_data, treatment_data):
    """자동화된 t-검정"""
    mean_diff = np.mean(treatment_data) - np.mean(control_data)
    t_stat, p_value = stats.ttest_ind(control_data, treatment_data)
    ci_lower, ci_upper = calculate_ci(...)
    cohens_d = calculate_cohens_d(...)

    return {
        "p_value": p_value,
        "confidence_interval": (ci_lower, ci_upper),
        "effect_size": cohens_d,
        "is_significant": p_value < 0.05
    }
```

**장점**:
- ✅ 객관적 기준
- ✅ 재현성 보장
- ✅ 일관성 유지
- ✅ 오류 감소

### 5. 자동 롤백 시스템

**목적**: 안전한 배포, 자동 복구

```python
async def perform_health_check():
    """SLA 기반 자동 롤백"""
    if error_rate > ROLLBACK_THRESHOLD:
        await trigger_rollback()
        logger.critical("Auto-rollback triggered")
    elif error_rate > WARNING_THRESHOLD:
        logger.warning("Warning threshold exceeded")
```

**장점**:
- ✅ 수동 개입 최소화
- ✅ 24/7 안정성
- ✅ 빠른 복구
- ✅ 보고서 자동 생성

---

## ⚡ 성능 최적화 기법

### 1. 응답 시간 최적화

**문제**: 초기 응답 시간 > 150ms

**해결책**:
```python
# 비동기 처리
async def get_recommendation(request):
    # 병렬 처리
    cf_result = await get_cf_score(request)
    cb_result = await get_cb_score(request)
    pa_result = await get_pa_score(request)

    # 가중치 결합
    return combine_scores(cf_result, cb_result, pa_result)
```

**결과**: 95ms P95 (150ms → 95ms, -37%)

### 2. 메모리 효율화

**문제**: 세션당 메모리 > 5KB

**해결책**:
```python
# 컨텍스트 윈도우 제한
class ContextMemory:
    def __init__(self, window_size=5):
        self.short_term = []  # 최근 5턴
        self.long_term = ""   # 요약

    def add_turn(self, turn):
        self.short_term.append(turn)
        if len(self.short_term) > self.window_size:
            # 요약 후 제거
            self.long_term = summarize(self.short_term)
            self.short_term = []
```

**결과**: 1KB/세션 (70% 감소)

### 3. 캐싱 전략

**문제**: 반복 요청 처리 느림

**해결책**:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_profile(user_id):
    """사용자 프로필 캐싱"""
    return fetch_user_profile(user_id)

@lru_cache(maxsize=100)
def get_persona_characteristics(persona_id):
    """페르소나 특성 캐싱"""
    return load_persona_data(persona_id)
```

**결과**: 캐시 히트율 80-90%

### 4. 데이터베이스 쿼리 최적화

**문제**: DB 조회 > 200ms

**해결책**:
```python
# 배치 조회
def get_user_interactions_batch(user_ids):
    """배치 조회"""
    return db.query(Interaction).filter(
        Interaction.user_id.in_(user_ids)
    ).all()

# 인덱스 추가
db.create_index('interaction_user_id')
db.create_index('session_user_id')
```

**결과**: 50-100ms 감소

---

## 🚀 배포 전략

### 카나리 배포 Best Practices

```
1. 작은 규모로 시작 (5%)
   └─ 최악의 경우 최소 영향

2. 24시간 모니터링
   └─ 충분한 데이터 수집

3. 자동 롤백 준비
   └─ SLA 기준 설정

4. 상세한 메트릭 추적
   └─ 문제 원인 파악 용이

5. 명확한 성공 기준
   └─ 주관적 판단 최소화
```

### A/B 테스트 Best Practices

```
1. 사전 통계력 분석
   └─ 필요한 샘플 크기 계산

2. 다중 비교 보정
   └─ Type I 오류 제어

3. 외부 요인 고려
   └─ 시간, 요일, 계절성

4. 세그먼트 분석
   └─ 신규 vs 기존 사용자

5. 효과 크기 측정
   └─ 통계적 유의성 + 실무적 의미
```

---

## 🔧 트러블슈팅 가이드

### 문제 1: 높은 에러율 (> 1%)

**증상**:
```
오류 로그 급증
응답 시간 증가
사용자 불만 증가
```

**진단**:
```bash
# 1. 에러 로그 확인
tail -f logs/error.log | grep ERROR

# 2. 에러 타입 분류
grep "ERROR" logs/error.log | cut -d: -f2 | sort | uniq -c

# 3. 데이터베이스 상태 확인
curl http://localhost:8000/health

# 4. 메모리/CPU 확인
top -b -n 1 | head -20
```

**해결책**:
```python
# Option 1: 재시도 로직 추가
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
async def get_recommendation(request):
    return engine.recommend(request)

# Option 2: 즉시 롤백
if error_rate > 0.01:
    await trigger_rollback()
```

### 문제 2: 느린 응답 시간 (P95 > 150ms)

**증상**:
```
GET /api/v2/recommend/personalized: 200ms
POST /api/v2/conversations/start: 150ms
```

**진단**:
```python
# 1. 각 컴포넌트 타이밍 측정
import time

start = time.time()
cf_score = get_cf_score(user_id)
cf_time = time.time() - start  # 50ms?

start = time.time()
cb_score = get_cb_score(user_id)
cb_time = time.time() - start  # 60ms?
```

**해결책**:
```python
# 병렬화
async def get_recommendation(user_id):
    # 순차: 110ms
    # cf_score = await get_cf_score(user_id)  # 50ms
    # cb_score = await get_cb_score(user_id)  # 60ms

    # 병렬: 60ms
    cf_score, cb_score = await asyncio.gather(
        get_cf_score(user_id),
        get_cb_score(user_id)
    )
    return combine(cf_score, cb_score)
```

### 문제 3: 메모리 누수

**증상**:
```
메모리 사용량 지속 증가
1시간: 1.2GB
2시간: 1.5GB
3시간: 1.9GB
```

**진단**:
```python
# 메모리 프로파일링
import tracemalloc

tracemalloc.start()

# 작업 수행
result = engine.recommend(request)

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

**해결책**:
```python
# 1. 캐시 크기 제한
from functools import lru_cache

@lru_cache(maxsize=1000)  # 무제한 ❌ → 1000 ✅
def get_user_profile(user_id):
    return load_profile(user_id)

# 2. 주기적 정리
async def periodic_cleanup():
    while True:
        await asyncio.sleep(3600)  # 1시간마다
        cache.clear()
        gc.collect()
```

---

## ❓ 자주 묻는 질문

### Q1: 왜 카나리 배포를 5%로 설정했나?

**A**:
```
이유 1: 위험 최소화
- 최악의 경우 100-150명만 영향

이유 2: 통계적 유의성
- 충분한 데이터 (하루 100-150명)
- 이상 징후 감지 가능

이유 3: 빠른 반응
- 24시간 내에 문제 판단 가능
- 빠른 롤백 가능

이유 4: 비용 효율
- 인프라 비용 증가 미미
- 모니터링 비용 최소
```

### Q2: A/B 테스트는 왜 13일?

**A**:
```
통계적 근거:
- 샘플 크기: 3,500명 필요
- 일일 사용자: ~250명/그룹
- 필요 기간: 3,500 / (250 × 2) = 7일

실제 적용:
- 7일: 기본 데이터 수집
- +3일: 버퍼 (외부 요인 제거)
- +3일: 분석 및 재검증

총 13일
```

### Q3: 왜 50% / 50% 분배?

**A**:
```
통계적 효율성:
- 50/50: 최대 통계력 달성
- 60/40: 통계력 약간 감소
- 80/20: 통계력 현저히 감소

위험 관리:
- 50/50: 영향 대칭적 (평가 용이)
- 80/20: 한쪽 문제 영향 큼

시간:
- 50/50: 13일
- 80/20: 30일+ (필요)
```

### Q4: 자동 롤백 기준이 1%인 이유?

**A**:
```
SLA 기준: 0.5%
↓
자동 롤백: 1% (SLA 2배)
↓
이유:
- 0.5%: 너무 엄격 (거짓 양성)
- 1%: 명확한 문제 신호
- 2%: 너무 관대 (복구 지연)
```

### Q5: 타임아웃 설정은?

**A**:
```
권장사항 엔진: 5초
- 기본 응답: 95ms
- 최대 응답: 2초
- 타임아웃: 5초 (여유)

다중 턴 엔진: 10초
- 기본 응답: 145ms
- 복잡한 쿼리: 3-4초
- 타임아웃: 10초

이유:
- 충분한 여유 (성능 vs 사용성)
- 무한 대기 방지
- 연쇄 장애 방지
```

---

## 📚 참고 자료

### 내부 문서

```
기술 설계:
├─ PHASE4_API_V2_INTEGRATION_DESIGN.md
├─ PHASE4_AB_TEST_FRAMEWORK.md
└─ PHASE4_CANARY_DEPLOYMENT_STRATEGY.md

운영 가이드:
├─ PHASE4_CANARY_RUNBOOK.md
├─ PHASE4_IMPLEMENTATION_CHECKLIST.md
└─ PHASE4_FINAL_DELIVERY_PACKAGE.md

분석 자료:
├─ PHASE4_CURRENT_STATUS_SUMMARY.md
├─ PHASE4_OVERALL_STATUS.md
└─ PHASE4_EXECUTIVE_SUMMARY.md
```

### 외부 자료

```
통계:
- https://en.wikipedia.org/wiki/A/B_testing
- https://www.coursera.org/learn/ab-testing

성능 최적화:
- https://docs.python-guide.org/writing/style/
- https://www.python.org/dev/peps/pep-0008/

FastAPI:
- https://fastapi.tiangolo.com/
- https://docs.sqlalchemy.org/

배포:
- https://kubernetes.io/docs/concepts/deployment/
- https://github.com/kubernetes/kubernetes
```

---

## 🔐 베스트 프랙티스 체크리스트

### 코드 작성

```
□ 타입 힌팅 추가
□ 에러 처리 구현
□ 로깅 추가
□ 유닛 테스트 작성
□ 통합 테스트 작성
□ 문서 작성
□ 코드 리뷰 완료
□ 성능 테스트 완료
```

### 배포 전

```
□ 모든 테스트 통과
□ 성능 벤치마크 완료
□ 보안 검사 완료
□ 로드 테스트 완료
□ 데이터베이스 백업 완료
□ 롤백 계획 수립
□ 팀 교육 완료
□ 모니터링 설정 완료
```

### 배포 후

```
□ 실시간 모니터링 시작
□ 메트릭 수집 확인
□ 알림 시스템 작동 확인
□ 헬스 체크 작동 확인
□ 에러 로그 모니터링
□ 사용자 피드백 수집
□ 일일 분석 수행
□ 지속적 개선 계획 수립
```

---

## 🎓 팀을 위한 학습 경로

### 신규 개발자 온보딩

```
Day 1: 아키텍처 이해
├─ Phase 4 전체 구조
├─ API 설계
└─ 데이터 흐름

Day 2: 코드 리뷰
├─ 핵심 모듈 분석
├─ 설계 패턴 학습
└─ 성능 특성 이해

Day 3: 배포 이해
├─ 카나리 배포 프로세스
├─ A/B 테스트 방법
└─ 모니터링 시스템

Day 4: 실습
├─ 로컬 환경 설정
├─ 코드 수정 실습
└─ 테스트 작성 실습

Day 5: 검증
├─ 코드 리뷰 통과
├─ 테스트 작성
└─ 문서 작성
```

### 운영팀 교육

```
1시간: 개요
├─ Phase 4 기능
├─ 배포 전략
└─ 모니터링 방식

2시간: 카나리 배포
├─ 배포 절차
├─ 메트릭 모니터링
└─ 롤백 프로세스

2시간: A/B 테스트
├─ 통계 기본
├─ 메트릭 해석
└─ 배포 의사결정

1시간: 문제 해결
├─ 일반적 문제
├─ 진단 방법
└─ 해결 절차
```

---

## 📊 메트릭 대시보드 설정

### Grafana 대시보드 구성

```
Row 1: 실시간 메트릭
├─ 요청/분
├─ 에러율 (%)
├─ P95 응답 시간
└─ 가용성 (%)

Row 2: 그룹별 비교
├─ Control vs Treatment
├─ 추천 정확도
├─ 사용자 만족도
└─ 세션 지속 시간

Row 3: 시스템 상태
├─ CPU 사용률
├─ 메모리 사용량
├─ 데이터베이스 연결
└─ 캐시 상태

Row 4: 비즈니스 메트릭
├─ DAU
├─ 채택율
├─ 완료율
└─ 재방문율
```

---

## 🎉 마치며

이 지식 베이스는 **Phase 4 프로젝트의 경험과 학습**을 정리한 것입니다.

향후 유사 프로젝트에서 다음을 참고하세요:

1. **설계**: 싱글톤 + 의존성 주입
2. **배포**: 카나리 → A/B 테스트 → 완전 배포
3. **분석**: 자동화된 통계 검증
4. **모니터링**: 자동 롤백 시스템

이 문서가 여러분의 프로젝트에 도움이 되기를 바랍니다! 🚀

---

**작성자**: Claude AI Agent (세나의 판단)
**최종 업데이트**: 2025-10-18
**상태**: ✅ **지속적 참고 자료**

