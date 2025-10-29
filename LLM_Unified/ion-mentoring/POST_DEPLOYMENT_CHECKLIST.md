# 배포 후 체크리스트 및 대시보드 설정

프로덕션 배포 후 처음 24시간, 1주일, 1개월 동안 수행할 작업들입니다.

**목표**: 배포 안정성 확보 및 성능 기준 검증

---

## 🚀 배포 당일 (Day 0)

### 배포 직후 (T+30분)

#### 1. 기본 상태 확인
```bash
# Cloud Run 상태 확인
gcloud run services describe ion-api-prod \
  --region us-central1 \
  --format="table(status.latestRevisionName, status.latestReadyRevisionName)"

# 헬스 체크
curl https://ion-api-prod.run.app/health

# 간단한 채팅 테스트
curl -X POST https://ion-api-prod.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

#### 2. 모니터링 활성화 확인
```bash
# 로그 스트리밍 시작
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ion-api-prod" \
  --follow --limit 50

# 메트릭 수집 확인
gcloud monitoring metrics list \
  --filter='metric.type=run.googleapis.com/*'
```

#### 3. Slack 알림 확인
- [ ] Slack #production-alerts에 배포 알림 수신됨
- [ ] 초기 에러 없음 확인

### 배포 후 1시간 (T+60분)

#### 성능 메트릭 검증
```bash
# 응답 시간 확인 (목표: P95 < 2s)
gcloud logging read \
  'resource.type="cloud_run_revision" AND jsonPayload.process_time_ms > 2000' \
  --limit 20 --format json | \
  jq '.[] | .jsonPayload.process_time_ms'

# 에러율 확인 (목표: < 1%)
gcloud logging read \
  'severity="ERROR" AND resource.labels.service_name="ion-api-prod"' \
  --limit 20
```

**체크리스트**:
- [ ] P95 응답 시간 < 2초 확인
- [ ] 에러율 < 1% 확인
- [ ] 메모리 사용 < 500MB 확인
- [ ] CPU 사용 < 80% 확인

### 배포 후 2시간 (T+120분)

#### 팀 공지
- [ ] 배포 성공 공지 (Slack #announcements)
- [ ] 초기 메트릭 요약 공유
- [ ] 모니터링 담당자 확정

---

## 📊 배포 후 24시간 (Day 1)

### 오전 체크 (배포 +12시간)

#### 1. 성능 메트릭 수집
```bash
# 지난 12시간 평균 응답 시간
gcloud logging read \
  'resource.type="cloud_run_revision" AND jsonPayload.process_time_ms' \
  --limit 1000 \
  --format json | \
  jq '[.[].jsonPayload.process_time_ms] | add/length'

# 요청 수 및 에러율
gcloud logging read \
  'resource.type="cloud_run_revision"' \
  --limit 1000 \
  --format json | \
  jq 'group_by(.jsonPayload.status_code) | map({code: .[0].jsonPayload.status_code, count: length})'
```

#### 2. 데이터 검증
- [ ] 데이터베이스 연결 정상
- [ ] 캐시 (Redis) 작동 정상
- [ ] 외부 API (Vertex AI) 응답 정상

#### 3. 사용자 피드백 모니터링
- [ ] 고객 지원팀 피드백 없음
- [ ] 에러 로그 분석
- [ ] 수상한 패턴 없음

**체크리스트**:
- [ ] 평균 응답 시간 1-2초
- [ ] 에러율 < 0.5%
- [ ] 메모리 안정적
- [ ] 사용자 이슈 없음

### 오후 체크 (배포 +18시간)

#### 성능 프로파일링
```bash
# 느린 요청 식별 (P95)
gcloud logging read \
  'resource.type="cloud_run_revision" AND jsonPayload.process_time_ms > 1500' \
  --format json | \
  jq '.[] | {persona: .jsonPayload.persona_used, time: .jsonPayload.process_time_ms}' | \
  sort | uniq -c | sort -rn
```

#### 페르소나별 성능
```bash
# 페르소나별 응답 시간
gcloud logging read \
  'resource.type="cloud_run_revision"' \
  --format json | \
  jq 'group_by(.jsonPayload.persona_used) | map({persona: .[0].jsonPayload.persona_used, avg_time: (map(.jsonPayload.process_time_ms) | add/length), count: length})'
```

**체크리스트**:
- [ ] 모든 페르소나 정상 작동
- [ ] 성능 편차 없음 (모든 페르소나 유사 성능)
- [ ] 느린 요청 패턴 식별

### 저녁 체크 (배포 +24시간)

#### 최종 리포트 작성
```
배포 후 24시간 성과 리포트
━━━━━━━━━━━━━━━━━━━━━━━━━━
총 요청 수:        [X,XXX]
성공률:            [XX.X]%
평균 응답 시간:    [X.Xs]
P95 응답 시간:     [X.Xs]
메모리 사용:       [XXX]MB
에러 수:           [XX]

주요 발견사항:
- ✓/⚠️ [내용]
- ✓/⚠️ [내용]
```

---

## 📈 배포 후 1주일 (Week 1)

### 월요일: 성과 분석
```bash
# 주간 성능 요약
gcloud logging read \
  'resource.type="cloud_run_revision"' \
  --limit 10000 \
  --format json | \
  jq '{
    total_requests: length,
    success_rate: (map(select(.jsonPayload.status_code < 400)) | length / length * 100),
    avg_response_time: (map(.jsonPayload.process_time_ms) | add / length),
    p95_response_time: (map(.jsonPayload.process_time_ms) | sort | .[length * 0.95]),
    error_count: (map(select(.jsonPayload.status_code >= 400)) | length)
  }'
```

### 주간 체크리스트

#### 1️⃣ 성능 (월-수)
- [ ] P95 응답 시간 < 2초 유지
- [ ] 에러율 < 1% 유지
- [ ] 메모리 누수 없음 (안정적 증가)
- [ ] CPU 사용률 일관성 있음

#### 2️⃣ 안정성 (목-금)
- [ ] 특이사항 없음
- [ ] 자동 복구 작동 확인
- [ ] 롤백 불필요
- [ ] 사용자 이슈 없음

#### 3️⃣ 데이터 (금)
- [ ] 데이터 일관성 확인
- [ ] 메모리 상태 정상
- [ ] 캐시 효율 확인

### 금요일: 주간 리포트

```markdown
# Week 1 배포 후 리포트

## 📊 성능 메트릭
- 총 요청: [X,XXX]
- 성공률: [XX.XX]%
- 평균 응답: [X.Xs]
- P95 응답: [X.Xs]
- 에러 수: [XX]

## 🟢 정상 상태 지표
- ✅ 응답 시간 목표 달성
- ✅ 에러율 목표 달성
- ✅ 메모리 안정적
- ✅ CPU 일관성 있음

## 🟡 주의 사항
- [있으면 기재]

## ✅ 다음 주 계획
- 성능 최적화 (캐싱)
- 모니터링 대시보드 고도화
- 팀 교육 (운영 절차)
```

---

## 🎯 배포 후 1개월 (Month 1)

### 주간 체크 (매주 금요일)

#### 성능 트렌드 분석
```
응답 시간 추이:
Week 1: P95 = 1.8s ✓
Week 2: P95 = 1.85s ✓
Week 3: P95 = 1.9s ✓
Week 4: P95 = 1.95s ⚠️

→ 경미한 증가 추세, 모니터링 필요
→ 캐싱 또는 쿼리 최적화 적용 예정
```

### 월간 체크 (Month 1 말)

#### 종합 평가
```
기간: 2025-10-21 ~ 2025-11-18

✅ 성공 지표
- 가용성: 99.9%+
- 에러율: < 0.5%
- P95 응답: < 2s 유지
- 메모리 누수: 없음

⚠️ 개선 필요
- [있으면 기재]

🚀 다음 단계
- 성능 최적화 적용
- 리팩토링 시작 (PersonaOrchestrator)
- 기능 확대 (선택)
```

---

## 📊 모니터링 대시보드 설정

### Google Cloud Console 대시보드

#### 1. 성능 메트릭 대시보드
```yaml
대시보드 이름: "ION API - 성능"

위젯:
  - 응답 시간 (P50, P95, P99)
  - 요청/분
  - 에러율
  - 메모리 사용
  - CPU 사용률
  - 인스턴스 수
```

#### 2. 에러 모니터링 대시보드
```yaml
대시보드 이름: "ION API - 에러"

위젯:
  - 에러율 추이
  - 에러 유형별 분포
  - 페르소나별 에러율
  - 상위 에러 메시지
  - 에러 빈도
```

#### 3. 비즈니스 메트릭 대시보드
```yaml
대시보드 이름: "ION API - 비즈니스"

위젯:
  - 일일 활성 사용자
  - 페르소나별 요청 분포
  - 평균 세션 길이
  - 사용자별 요청 분포
  - 시간대별 트래픽
```

### Slack 알림 설정

#### 알림 규칙
```yaml
Critical:
  - P95 > 5초
  - 에러율 > 10%
  - 메모리 > 800MB
  → #production-alerts (즉시)

Warning:
  - P95 > 3초
  - 에러율 > 5%
  - 메모리 > 600MB
  → #production-alerts (1시간마다)

Info:
  - 배포 완료
  - 백업 완료
  - 일일 요약
  → #production-logs (매일 아침)
```

---

## 🛠️ 즉시 최적화 작업 (Week 2)

### 성능 최적화 Phase 1

#### 응답 캐싱 (고우선도)
```python
# app/cache.py (신규)
from functools import lru_cache
import hashlib

class ResponseCache:
    def __init__(self, ttl: int = 1800):
        self.cache = {}
        self.ttl = ttl

    def get_key(self, message: str) -> str:
        return hashlib.md5(message.encode()).hexdigest()

    def get(self, key: str):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
        return None

    def set(self, key: str, value: str):
        self.cache[key] = (value, time.time())

# app/main.py 수정
cache = ResponseCache()

@app.post("/chat")
async def chat(request: ChatRequest):
    cache_key = cache.get_key(request.message)

    # 캐시 히트
    if cached := cache.get(cache_key):
        return cached

    # 캐시 미스
    response = await process_request(request)
    cache.set(cache_key, response)
    return response
```

**예상 개선**: 응답 시간 5-10% 단축, 반복 쿼리 90% 감소

#### 배치 로깅 (고우선도)
```python
# app/batch_logger.py (신규)
class BatchLogger:
    def __init__(self, batch_size: int = 50):
        self.buffer = []
        self.batch_size = batch_size

    def add_log(self, entry: Dict):
        self.buffer.append(entry)
        if len(self.buffer) >= self.batch_size:
            self.flush()

    def flush(self):
        if self.buffer:
            # 배치 전송
            send_to_gcp_logging(self.buffer)
            self.buffer = []
```

**예상 개선**: 로깅 오버헤드 50% 감소

---

## 🔄 자동 복구 설정

### 자동 재시작 (Auto-restart)
```bash
# Cloud Run 자동 재시작 설정
gcloud run deploy ion-api-prod \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 100 \
  --health-check-enabled \
  --health-check-path /health \
  --health-check-timeout 10s
```

### 자동 스케일링 확인
```bash
# 스케일링 정책 확인
gcloud run services describe ion-api-prod \
  --region us-central1 \
  --format="table(status.traffic)"
```

---

## ✅ 최종 체크리스트

### 배포 당일
- [ ] 기본 상태 확인 완료
- [ ] 모니터링 활성화 확인
- [ ] 팀 공지 완료

### 배포 후 24시간
- [ ] 성능 메트릭 확인
- [ ] 데이터 검증 완료
- [ ] 사용자 이슈 없음 확인

### 배포 후 1주일
- [ ] 주간 리포트 작성 완료
- [ ] 트렌드 분석 완료
- [ ] 개선 계획 수립

### 배포 후 1개월
- [ ] 월간 리포트 작성
- [ ] 성능 최적화 적용
- [ ] 향후 계획 수립

---

**배포 후 성공적인 안정화를 위한 철저한 모니터링과 빠른 피드백 루프 구축이 핵심입니다.** ✅
