# 📊 Lumen Gateway 모니터링 가이드

**작성일**: 2025-10-24  
**Phase**: 5 - Monitoring & Observability

---

## 🎯 모니터링 개요

Phase 4.2에서 구현한 Redis 캐싱의 성능과 안정성을 추적하기 위한 모니터링 시스템입니다.

### 주요 목표
1. **캐시 효율성 추적** - Hit Rate 60%+ 목표
2. **성능 모니터링** - 응답 시간 <2s 유지
3. **안정성 보장** - 에러율 <1% 유지
4. **리소스 최적화** - 메모리 사용량 추적

---

## 🔗 대시보드 접근

### Cloud Monitoring Dashboard
**URL**: https://console.cloud.google.com/monitoring/dashboards/custom/0f56dda9-95eb-4b73-a478-38ace68c07d2?project=naeda-genesis

**대시보드 ID**: `0f56dda9-95eb-4b73-a478-38ace68c07d2`

### 포함된 위젯

#### 1. Cache Hit Rate (Last 24h)
- **메트릭**: `logging.googleapis.com/user/cache_hit_rate`
- **목표**: 60%+ (안정화 후)
- **해석**:
  - 40% 미만: 캐시 전략 재검토 필요
  - 40-60%: 정상 범위 (초기 단계)
  - 60%+: 우수한 캐시 효율

#### 2. Response Time (p95)
- **메트릭**: `run.googleapis.com/request_latencies`
- **목표**: <2000ms
- **해석**:
  - <500ms: 캐시 HIT (우수)
  - 500-2000ms: 정상 범위
  - >2000ms: 성능 저하 (조사 필요)

#### 3. Request Count
- **메트릭**: `run.googleapis.com/request_count`
- **그룹**: response_code_class (2xx, 4xx, 5xx)
- **해석**:
  - 2xx: 정상 요청
  - 4xx: 클라이언트 오류 (입력 검증)
  - 5xx: 서버 오류 (즉시 조사 필요)

#### 4. Error Rate
- **필터**: `response_code_class != "2xx"`
- **목표**: <1%
- **해석**:
  - <1%: 정상
  - 1-5%: 주의 필요
  - >5%: 심각 (긴급 대응)

---

## 📈 주요 메트릭 설명

### Cloud Run 기본 메트릭

| 메트릭 | 설명 | 정상 범위 |
|--------|------|-----------|
| `request_count` | 요청 수 | - |
| `request_latencies` | 응답 시간 (ms) | <2000ms |
| `container/cpu/utilization` | CPU 사용률 | <80% |
| `container/memory/utilization` | 메모리 사용률 | <80% |
| `container/instance_count` | 인스턴스 수 | 1-3 (트래픽 따라) |

### 로그 기반 메트릭

#### cache_hit_rate (수동 계산 필요)

```
cache_hit_rate = cache_hits / (cache_hits + cache_misses) * 100
```

**로그 필터링**:
- Cache HIT: `textPayload=~"[CACHE HIT]"`
- Cache MISS: `textPayload=~"[CACHE MISS]"`

---

## 🔍 로그 분석

### 캐시 로그 보기

#### 1. Cloud Logging 콘솔에서
**URL**: https://console.cloud.google.com/logs/query?project=naeda-genesis

**쿼리 예시**:

```
resource.type="cloud_run_revision"
resource.labels.service_name="lumen-gateway"
(textPayload=~"CACHE HIT" OR textPayload=~"CACHE MISS")
```

#### 2. gcloud CLI로

```bash
gcloud logging read '
  resource.type="cloud_run_revision" AND 
  resource.labels.service_name="lumen-gateway" AND 
  (textPayload=~"CACHE HIT" OR textPayload=~"CACHE MISS")
' --limit 50 --format json --project naeda-genesis
```

#### 3. PowerShell로 캐시 통계 추출

```powershell
# 최근 100개 로그에서 캐시 통계 계산
$logs = gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="lumen-gateway"' --limit 100 --format json --project naeda-genesis | ConvertFrom-Json

$cacheHits = ($logs | Where-Object { $_.textPayload -match "CACHE HIT" }).Count
$cacheMisses = ($logs | Where-Object { $_.textPayload -match "CACHE MISS" }).Count
$total = $cacheHits + $cacheMisses

if ($total -gt 0) {
    $hitRate = [math]::Round(($cacheHits / $total) * 100, 2)
    Write-Host "Cache Statistics (Last 100 logs):" -ForegroundColor Cyan
    Write-Host "  Hits: $cacheHits" -ForegroundColor Green
    Write-Host "  Misses: $cacheMisses" -ForegroundColor Yellow
    Write-Host "  Hit Rate: $hitRate%" -ForegroundColor Magenta
}
```

---

## 🔔 알림 정책 (향후 구현)

### 1. High Response Time Alert
- **조건**: p95 latency > 5000ms for 5 minutes
- **액션**: 이메일 알림
- **자동 해결**: 30분 후

### 2. High Error Rate Alert
- **조건**: Error rate > 5% for 3 minutes
- **액션**: 이메일 + SMS 알림
- **자동 해결**: 30분 후

### 3. Cache Connection Failure
- **조건**: Health check `cache != "connected"`
- **액션**: 즉시 알림
- **자동 해결**: 연결 복구 시

### 알림 채널 설정 (수동)
1. Cloud Console → Monitoring → Alerting
2. "Notification Channels" 탭
3. Email/SMS 채널 추가
4. 각 Alert Policy에 채널 연결

---

## 📊 Upstash Redis 모니터링

### Upstash Console
**URL**: https://console.upstash.com/redis/careful-mustang-35050

### 주요 지표

#### 1. Commands Dashboard
- **총 commands**: 10,000/day 한도
- **현재 사용량**: ~1,600/day 예상
- **여유**: 83%

#### 2. Memory Usage
- **현재**: 3.337KB (3 keys)
- **한도**: 256 MB
- **사용률**: 0.0013%

#### 3. Connection Health
- **SSL**: Enabled
- **Timeout**: 5 seconds
- **Region**: us-central1

### 알림 설정 (Upstash)
- Daily command limit 경고: 8,000 commands
- Memory limit 경고: 200 MB

---

## 🧪 모니터링 테스트

### 1. 대시보드 데이터 생성

```powershell
# 테스트 요청 10개 전송
$url = "https://lumen-gateway-64076350717.us-central1.run.app/chat"
$messages = @(
    "Tell me about AI",
    "Explain machine learning",
    "What is deep learning?",
    "Tell me about AI",  # 캐시 HIT 유도
    "Explain machine learning",  # 캐시 HIT 유도
    "What is neural network?",
    "Tell me about AI",  # 캐시 HIT 유도
    "Define reinforcement learning",
    "What is NLP?",
    "Explain machine learning"  # 캐시 HIT 유도
)

$messages | ForEach-Object {
    $body = @{ message = $_ } | ConvertTo-Json
    Write-Host "Sending: $_" -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri $url -Method POST -Body $body -ContentType "application/json"
    Write-Host "✓ Response received" -ForegroundColor Green
    Start-Sleep -Milliseconds 500
}

Write-Host "`n✅ Test complete! Check dashboard in 1-2 minutes" -ForegroundColor Green
```

### 2. 캐시 통계 확인

```powershell
Invoke-RestMethod -Uri "https://lumen-gateway-64076350717.us-central1.run.app/cache/stats"
```

**예상 출력**:

```json
{
  "enabled": true,
  "connected": true,
  "total_keys": 6,
  "memory_used": "6.8KB",
  "total_commands": 24,
  "ttl_seconds": 3600
}
```

---

## 📅 일일 점검 체크리스트

### 매일 확인 항목 (5분)

- [ ] **대시보드 확인**
  - Cache Hit Rate 추세
  - Response Time 이상치
  - Error Rate 확인

- [ ] **Upstash 콘솔 확인**
  - Commands 사용량 (<8,000)
  - Memory 사용량 (<200MB)
  - Connection 에러 확인

- [ ] **로그 검토**
  - 최근 에러 로그 확인
  - 비정상적인 패턴 탐지

### 주간 확인 항목 (30분)

- [ ] **성능 추세 분석**
  - 7일 평균 응답 시간
  - 캐시 히트율 변화
  - 트래픽 패턴 분석

- [ ] **최적화 기회 탐색**
  - 자주 MISS되는 쿼리 식별
  - TTL 조정 필요성 검토
  - 캐시 워밍 대상 선정

### 월간 확인 항목 (2시간)

- [ ] **월간 보고서 작성**
  - 전월 대비 성능 변화
  - 비용 분석 (Gemini API calls)
  - 사용자 경험 개선 효과

- [ ] **시스템 건강성 검토**
  - Alert 발생 이력
  - 장애 대응 이력
  - 개선 사항 제안

---

## 🚨 장애 대응 플레이북

### Scenario 1: Cache Connection Failure

**증상**: Health check에서 `cache: "error"`

**대응 단계**:
1. Upstash Console에서 Redis 상태 확인
2. 로그에서 연결 오류 메시지 확인
3. 환경 변수 확인 (UPSTASH_REDIS_REST_URL, TOKEN)
4. 필요 시 Cloud Run 서비스 재시작
5. Graceful degradation 확인 (서비스 정상 작동 중)

### Scenario 2: High Response Time (>5s)

**증상**: p95 latency > 5000ms

**대응 단계**:
1. 캐시 히트율 확인 (낮으면 캐시 이슈)
2. Gemini API 상태 확인 (API 지연 가능성)
3. Cloud Run 인스턴스 스케일링 확인
4. 로그에서 느린 요청 패턴 분석
5. 필요 시 TTL 조정 또는 캐시 워밍

### Scenario 3: High Error Rate (>5%)

**증상**: 5xx 에러 급증

**대응 단계**:
1. 로그에서 에러 스택트레이스 확인
2. Gemini API 키 유효성 확인
3. Redis 연결 상태 확인
4. Cloud Run 서비스 로그 상세 분석
5. 필요 시 이전 버전으로 롤백

### Scenario 4: Memory Limit Approaching

**증상**: Upstash memory > 200MB

**대응 단계**:
1. 캐시 키 개수 확인
2. 평균 키 크기 분석
3. TTL 단축 고려 (3600s → 1800s)
4. 불필요한 캐시 키 수동 삭제
5. Upstash 유료 플랜 업그레이드 검토

---

## 🎯 성공 지표 (KPI)

### Phase 5 목표 (1개월 내)

| 지표 | 목표 | 현재 | 상태 |
|------|------|------|------|
| **Cache Hit Rate** | 60%+ | TBD | 🔄 측정 중 |
| **Avg Response Time** | <2s | 0.17s (HIT) | ✅ 달성 |
| **p95 Response Time** | <3s | TBD | 🔄 측정 중 |
| **Error Rate** | <1% | TBD | 🔄 측정 중 |
| **Uptime** | 99.9% | 100% | ✅ 달성 |

### 비용 절감 효과

```
월간 요청 예상: 30,000 requests
캐시 히트율: 60% (목표)
절감된 Gemini API 호출: 18,000 calls

API 비용 절감:
- Gemini Flash: $0.000375 per 1K tokens (입력)
- 평균 입력: 100 tokens
- 월간 절감: 18,000 * 0.1K * $0.000375 = $0.675
- 연간 절감: ~$8.10
```

**참고**: 무료 tier 사용 중이므로 실제 비용 절감보다 **응답 속도 개선**이 주요 가치

---

### Snapshot Rotation Automation

`scripts\register_snapshot_rotation_task.ps1` 스크립트를 사용하면 상태 스냅샷(`outputs\status_snapshots.jsonl`)을 일정 주기로 보관 디렉터리로 회전시킬 수 있습니다.

- `-ArchiveDir`: 보관 디렉터리 경로(기본 `D:\nas_backup\outputs\archive`)
- `-RetentionDays`: 보관 파일 유지 일수(기본 30일)
- `-Zip`: 회전 시 압축본 생성
- `-DryRun`: 이동 없이 동작만 검증
- `-AllowOnBatteries`: 배터리 전원에서도 실행/종료 허용
- `-NoWake`: 절전 모드에서 깨우지 않고 대기

```powershell
# 매일 03:15 실행, 기본 경로/보존값
powershell -NoProfile -File scripts\register_snapshot_rotation_task.ps1 -Register -Time "03:15"

# 사용자 경로 + 배터리 허용 + 즉시 드라이런 점검
powershell -NoProfile -File scripts\register_snapshot_rotation_task.ps1 `
  -Register -Time "01:00" -ArchiveDir "D:\logs\archive" -RetentionDays 45 -AllowOnBatteries -DryRun -RunNow
```

등록된 작업 상태 확인:

```powershell
powershell -NoProfile -File scripts\register_snapshot_rotation_task.ps1 -Status
```

작업을 제거하려면 `-Unregister`를 사용합니다.

---

## 📚 참고 자료

### Google Cloud Monitoring
- [Cloud Run Metrics](https://cloud.google.com/run/docs/monitoring)
- [Log-based Metrics](https://cloud.google.com/logging/docs/logs-based-metrics)
- [Alerting Policies](https://cloud.google.com/monitoring/alerts)

### Upstash Redis
- [Monitoring Guide](https://docs.upstash.com/redis/features/monitoring)
- [Free Tier Limits](https://upstash.com/pricing)

### 내부 문서
- `깃코_Phase4.2_Redis_Caching_최종완료보고서_2025-10-24.md`
- `REDIS_SETUP_GUIDE.md`

---

**작성자**: 깃코  
**최종 업데이트**: 2025-10-24  
**다음 리뷰**: 2025-10-31 (1주일 후 성능 데이터 분석)
