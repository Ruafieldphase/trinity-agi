# Phase 14 계획: 비용 최적화 및 성능 개선 실행

**작성일**: 2025-10-24  
**단계**: Phase 14 - Cost Optimization & Performance Enhancement  
**기간**: 1-2주 예상  
**상태**: 🔄 계획 수립 완료

---

## 📊 Executive Summary

### 현황
- **Phase 13 완료**: 최적화 도구 4종 구현 및 검증
- **현재 월 비용**: **$347** (예산 $200의 173%)
- **비용 초과**: **$147** (73% 초과)
- **응답시간**: Chat 235ms (목표 200ms), Health 169ms (목표 50ms)

### Phase 14 목표
1. 🎯 **비용 절감**: $347 → **$200 이하** (42% 절감)
2. 🎯 **응답시간 개선**: Chat 235ms → **<200ms** (15% 개선)
3. 🎯 **캐시 히트율**: 0% → **>80%** (신규)

### 예상 효과
- **즉시 절감**: ~$65/월 (Canary Min Instances)
- **캐싱 절감**: 요청 비용 80% 감소 (~$0.10/월)
- **리소스 최적화**: CPU/Memory 최적화 시 ~$50/월 추가 절감
- **총 예상**: **$282 → $200** 달성 가능

---

## 🚀 Phase 14 작업 계획

### Task 1: 계획 수립 ✅
**기간**: 1일  
**상태**: ✅ 완료

**산출물**:
- Phase 14 로드맵
- Todo 리스트 (5개 작업)
- 리스크 분석 및 완화 계획

---

### Task 2: Canary Min Instances 0으로 조정
**기간**: 즉시 실행  
**예상 효과**: **~$65/월 절감**  
**리스크**: ⚠️ 낮음 (Canary는 테스트 환경)

#### 실행 계획

```bash
# 1. 현재 설정 확인
gcloud run services describe ion-api-canary \
  --region=us-central1 \
  --project=naeda-genesis \
  --format="value(spec.template.metadata.annotations['autoscaling.knative.dev/minScale'])"

# 2. Min Instances 0으로 조정
gcloud run services update ion-api-canary \
  --min-instances=0 \
  --region=us-central1 \
  --project=naeda-genesis

# 3. 변경 확인
gcloud run services describe ion-api-canary \
  --region=us-central1 \
  --project=naeda-genesis \
  --format="table(metadata.name, status.url, spec.template.spec.containers[0].resources.limits)"
```

#### 검증
- ✅ Canary 서비스 정상 동작 확인 (첫 요청 시 콜드 스타트 허용)
- ✅ Main 서비스 영향 없음 확인
- ✅ 24시간 후 비용 모니터링 도구 재실행

#### 롤백 계획

```bash
# 문제 발생 시 즉시 롤백
gcloud run services update ion-api-canary \
  --min-instances=1 \
  --region=us-central1 \
  --project=naeda-genesis
```

---

### Task 3: Redis 캐싱 활성화
**기간**: 1주  
**예상 효과**: 요청 비용 80% 감소, 응답시간 50% 단축  
**리스크**: ⚠️ 중간 (캐시 불일치 가능성)

#### 3.1 Redis 인스턴스 구성 (Day 1-2)

```bash
# Memorystore for Redis 생성 (Basic Tier, 1GB)
gcloud redis instances create ion-cache \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=basic \
  --project=naeda-genesis

# 연결 정보 확인
gcloud redis instances describe ion-cache \
  --region=us-central1 \
  --project=naeda-genesis
```

**예상 비용**: ~$33/월 (Basic 1GB)  
**순 절감**: 요청 비용 감소 > Redis 비용

#### 3.2 캐싱 로직 구현 (Day 3-5)

**캐시 키 구조**:

```
cache:{endpoint}:{hash(request_body)}
예: cache:chat:a3f9c2b1
```

**TTL 전략**:
- Chat 엔드포인트: 1시간 (3600초)
- 유사 쿼리: 6시간 (21600초)
- Health Check: 캐싱 안 함

**구현 파일**: `app/core/cache.py`

```python
import redis
import hashlib
import json
from typing import Optional, Any

class CacheManager:
    def __init__(self, redis_host: str, redis_port: int = 6379):
        self.client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        
    def _generate_key(self, endpoint: str, request_data: dict) -> str:
        """Generate cache key from request"""
        data_str = json.dumps(request_data, sort_keys=True)
        hash_obj = hashlib.sha256(data_str.encode())
        return f"cache:{endpoint}:{hash_obj.hexdigest()[:12]}"
    
    def get(self, endpoint: str, request_data: dict) -> Optional[str]:
        """Get cached response"""
        key = self._generate_key(endpoint, request_data)
        try:
            return self.client.get(key)
        except redis.RedisError as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, endpoint: str, request_data: dict, response: str, ttl: int = 3600):
        """Cache response with TTL"""
        key = self._generate_key(endpoint, request_data)
        try:
            self.client.setex(key, ttl, response)
        except redis.RedisError as e:
            print(f"Cache set error: {e}")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            info = self.client.info("stats")
            return {
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except redis.RedisError:
            return {}
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0
```

**Chat 엔드포인트 수정**: `app/api/v2/chat.py`

```python
from app.core.cache import CacheManager
import os

# Redis 연결 초기화 (환경 변수)
cache = CacheManager(
    redis_host=os.getenv("REDIS_HOST", "localhost"),
    redis_port=int(os.getenv("REDIS_PORT", "6379"))
)

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # 캐시 조회
    cache_key_data = {
        "user_id": request.user_id,
        "query": request.query,
        "options": request.options
    }
    
    cached_response = cache.get("chat", cache_key_data)
    if cached_response:
        return JSONResponse(
            content=json.loads(cached_response),
            headers={"X-Cache": "HIT"}
        )
    
    # LLM 호출 (캐시 미스)
    response = await generate_response(request)
    
    # 응답 캐싱
    cache.set("chat", cache_key_data, json.dumps(response), ttl=3600)
    
    return JSONResponse(
        content=response,
        headers={"X-Cache": "MISS"}
    )
```

#### 3.3 캐싱 모니터링 엔드포인트 추가 (Day 6)

```python
@router.get("/cache/stats")
async def cache_stats():
    """Cache statistics endpoint"""
    stats = cache.get_stats()
    return {
        "hit_rate": stats.get("hit_rate", 0),
        "keyspace_hits": stats.get("keyspace_hits", 0),
        "keyspace_misses": stats.get("keyspace_misses", 0),
        "target_hit_rate": 80.0
    }
```

#### 3.4 테스트 및 검증 (Day 7)

```bash
# 1. 캐시 미스 테스트
curl -X POST https://ion-api-64076350717.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","query":"Hello"}' \
  -i | grep "X-Cache"
# 예상: X-Cache: MISS

# 2. 캐시 히트 테스트 (즉시 재요청)
curl -X POST https://ion-api-64076350717.us-central1.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","query":"Hello"}' \
  -i | grep "X-Cache"
# 예상: X-Cache: HIT

# 3. 캐시 통계 확인
curl https://ion-api-64076350717.us-central1.run.app/cache/stats
# 예상: {"hit_rate": 50.0, ...}
```

**성공 기준**:
- ✅ 캐시 히트율 >80% (7일 평균)
- ✅ 응답시간 50% 단축 (캐시 히트 시)
- ✅ 요청 비용 80% 감소

---

### Task 4: 비용 절감 효과 검증
**기간**: Task 2-3 완료 후 24-48시간  
**도구**: `monitor_gcp_costs.ps1`

#### 검증 시나리오

```powershell
# 1. 초기 비용 (베이스라인)
powershell -File scripts/monitor_gcp_costs.ps1 `
  -ProjectId "naeda-genesis" `
  -Days 7 `
  -MonthlyBudget 200 `
  -OutputJson "outputs/cost_baseline.json"
# 예상: $347

# 2. Canary Min 0 적용 후 (24시간 후)
powershell -File scripts/monitor_gcp_costs.ps1 `
  -ProjectId "naeda-genesis" `
  -Days 1 `
  -MonthlyBudget 200 `
  -OutputJson "outputs/cost_after_canary.json"
# 예상: $282 (-$65)

# 3. 캐싱 활성화 후 (7일 후)
powershell -File scripts/monitor_gcp_costs.ps1 `
  -ProjectId "naeda-genesis" `
  -Days 7 `
  -MonthlyBudget 200 `
  -OutputJson "outputs/cost_after_cache.json"
# 목표: $200 이하
```

#### 검증 메트릭

| 메트릭 | 초기 | Canary Min 0 | 캐싱 활성화 | 목표 |
|--------|------|--------------|-------------|------|
| 월 비용 | $347 | $282 | $200 | <$200 |
| 예산 대비 | 173% | 141% | 100% | <100% |
| Main 비용 | $249 | $249 | $199 | <$150 |
| Canary 비용 | $98 | $33 | $1 | <$50 |

---

### Task 5: 예산 알림 시스템 구축
**기간**: 1-2일  
**목적**: 비용 초과 조기 감지

#### 5.1 GCP Budget Alert 설정

```bash
# Cloud Console 사용 (gcloud CLI로는 제한적)
# URL: https://console.cloud.google.com/billing/budgets?project=naeda-genesis

# 예산 구성
# 1. 예산 이름: "ION API Monthly Budget"
# 2. 예산 금액: $200 USD
# 3. 알림 임계값:
#    - 80% ($160): ⚠️ Warning
#    - 100% ($200): 🔴 Critical
#    - 120% ($240): 🚨 Emergency
# 4. 알림 대상:
#    - 이메일: [프로젝트 소유자]
#    - Pub/Sub (선택): cloud-billing-alerts
```

#### 5.2 Slack 알림 통합 (선택)
**파일**: `scripts/budget_alert_slack.ps1`

```powershell
param(
    [Parameter(Mandatory=$true)]
    [decimal]$CurrentSpend,
    
    [Parameter(Mandatory=$true)]
    [decimal]$BudgetAmount,
    
    [string]$SlackWebhook = $env:SLACK_WEBHOOK_URL
)

$usagePercent = [math]::Round(($CurrentSpend / $BudgetAmount) * 100, 1)

$color = switch ($usagePercent) {
    {$_ -ge 120} { "danger" }
    {$_ -ge 100} { "danger" }
    {$_ -ge 80} { "warning" }
    default { "good" }
}

$emoji = switch ($usagePercent) {
    {$_ -ge 120} { ":rotating_light:" }
    {$_ -ge 100} { ":red_circle:" }
    {$_ -ge 80} { ":warning:" }
    default { ":white_check_mark:" }
}

$payload = @{
    text = "$emoji Budget Alert: $usagePercent% used"
    attachments = @(
        @{
            color = $color
            fields = @(
                @{
                    title = "Current Spend"
                    value = "`$$CurrentSpend"
                    short = $true
                }
                @{
                    title = "Budget"
                    value = "`$$BudgetAmount"
                    short = $true
                }
                @{
                    title = "Usage"
                    value = "$usagePercent%"
                    short = $true
                }
                @{
                    title = "Remaining"
                    value = "`$$([math]::Max($BudgetAmount - $CurrentSpend, 0))"
                    short = $true
                }
            )
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri $SlackWebhook -Method Post -Body $payload -ContentType "application/json"
```

#### 5.3 자동 모니터링 (Scheduled Task)

```powershell
# 매일 오전 9시 비용 확인 및 Slack 알림
$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File D:\nas_backup\LLM_Unified\ion-mentoring\scripts\monitor_gcp_costs.ps1 -ProjectId naeda-genesis -Days 1 -MonthlyBudget 200"

$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM

Register-ScheduledTask `
  -TaskName "ION_Daily_Cost_Check" `
  -Action $action `
  -Trigger $trigger `
  -Description "Check ION API daily costs and send Slack alert if over budget"
```

---

## 🎯 성공 기준

### 비용 목표
- ✅ 월 비용 **<$200** (현재 $347에서 42% 절감)
- ✅ 예산 대비 **<100%** (현재 173%에서 개선)
- ✅ Canary 비용 **<$50** (현재 $98에서 절감)

### 성능 목표
- ✅ Chat 응답시간 P95 **<200ms** (현재 311ms)
- ✅ 캐시 히트율 **>80%** (신규)
- ✅ 서비스 가용성 **>99.9%** (유지)

### 모니터링 목표
- ✅ 예산 알림 **80%, 100%, 120%** 임계값 설정
- ✅ 일일 비용 리포트 자동화
- ✅ Slack 통합 (선택)

---

## ⚠️ 리스크 분석 및 완화

### 리스크 1: Canary 콜드 스타트
**발생 확률**: 높음  
**영향도**: 낮음  
**완화 방안**:
- Canary는 테스트 환경이므로 첫 요청 지연 허용
- Main 서비스는 Min 1 유지하여 프로덕션 영향 없음
- 필요 시 즉시 롤백 (1분 내)

### 리스크 2: 캐시 불일치
**발생 확률**: 중간  
**영향도**: 중간  
**완화 방안**:
- TTL 1시간으로 제한 (짧은 주기)
- 캐시 무효화 API 제공 (`POST /cache/invalidate`)
- 사용자 피드백 루프 (캐시 미스 강제 옵션)

### 리스크 3: Redis 장애
**발생 확률**: 낮음  
**영향도**: 중간  
**완화 방안**:
- Redis 연결 실패 시 자동 fallback (캐시 미사용)
- Timeout 2초로 제한 (응답시간 영향 최소화)
- Redis 장애 알림 (Prometheus + Alertmanager)

### 리스크 4: 비용 초과
**발생 확률**: 낮음 (Redis 비용 추가)  
**영향도**: 낮음  
**완화 방안**:
- Redis Basic 1GB: ~$33/월 (예산 포함)
- 예상 순 절감: -$65 (Canary) + $33 (Redis) = **-$32/월**
- 예산 알림으로 조기 감지

---

## 📅 타임라인

### Week 1: 즉시 비용 절감
**Day 1** (오늘):
- ✅ Phase 14 계획 수립
- ⏳ Canary Min Instances 0 설정
- ⏳ 초기 비용 베이스라인 측정

**Day 2**:
- Redis 인스턴스 생성
- 캐싱 로직 구현 시작

**Day 3-4**:
- 캐싱 로직 완성
- 로컬 테스트

**Day 5**:
- 캐싱 배포 (Canary → Main)
- 캐시 통계 모니터링

**Day 6-7**:
- 캐시 히트율 모니터링 (목표 >80%)
- 비용 절감 효과 검증

### Week 2: 예산 알림 및 검증
**Day 8**:
- GCP Budget Alert 설정
- Slack 통합 (선택)

**Day 9-10**:
- 자동 모니터링 설정
- 7일 비용 데이터 수집

**Day 11-12**:
- 최종 검증 및 보고서 작성
- Phase 14 완료

---

## 📊 예상 결과

### 비용 절감 시나리오

```
초기 (Phase 13):
  Main: $249/월
  Canary: $98/월
  Total: $347/월 (예산 대비 173%)

Week 1 완료 (Canary Min 0):
  Main: $249/월
  Canary: $33/월 (Min 0, Redis 추가)
  Total: $282/월 (예산 대비 141%)
  절감: -$65/월

Week 2 완료 (캐싱 활성화):
  Main: $199/월 (요청 비용 80% 감소)
  Canary: $1/월 (최소 사용)
  Total: $200/월 (예산 대비 100%)
  절감: -$147/월 (42% 절감)
```

### 성능 개선 시나리오

```
캐시 히트 시:
  응답시간: 235ms → 50ms (78% 개선)
  
캐시 미스 시:
  응답시간: 235ms (변동 없음)
  
평균 (히트율 80%):
  응답시간: 87ms (63% 개선)
```

---

## 🔄 다음 단계 (Phase 15 예상)

Phase 14 완료 후 고려사항:

1. **LLM 모델 최적화**
   - Gemini 1.5 Pro → Flash 전환
   - max_output_tokens: 512 제한
   - 추가 응답시간 단축 및 비용 절감

2. **Health Check 최적화**
   - 불필요한 DB 조회 제거
   - Redis 연결 캐싱
   - 목표: 169ms → <50ms

3. **리소스 최적화**
   - CPU: 2 vCPU → 1 vCPU (성능 테스트 후)
   - Memory: 1Gi → 512Mi
   - 추가 ~$50/월 절감 가능

---

**Phase 14 계획 완료** - 즉시 실행 준비 완료! 🚀
