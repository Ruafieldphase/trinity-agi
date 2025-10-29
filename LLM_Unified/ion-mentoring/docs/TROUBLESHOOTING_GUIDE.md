# 트러블슈팅 가이드 (8시간 작업)

## 📋 개요

**목표**: 운영 중 발생 가능한 문제와 해결 방법 정리
**범위**: API, 데이터베이스, 캐시, 모니터링, 배포
**사용자**: 운영팀, 개발팀, DevOps

---

## 🔍 문제 진단 플로우차트

```
문제 발생
│
├─ API 응답 없음?
│  ├─ → Cloud Run 상태 확인
│  ├─ → 로그 확인
│  └─ → 기본 검사 (1단계)
│
├─ 느린 응답?
│  ├─ → 응답 시간 분석
│  ├─ → 데이터베이스 쿼리 확인
│  └─ → 성능 문제 (2단계)
│
├─ 높은 에러율?
│  ├─ → 에러 로그 분석
│  ├─ → 외부 의존성 확인
│  └─ → 에러 문제 (3단계)
│
├─ 리소스 부족?
│  ├─ → CPU/메모리 확인
│  ├─ → 스케일링 필요
│  └─ → 리소스 문제 (4단계)
│
└─ 배포 실패?
   ├─ → 배포 로그 확인
   ├─ → 이미지 검사
   └─ → 배포 문제 (5단계)
```

---

## 🚨 Incident Levels

| 레벨 | 영향도 | 응답 시간 | 우선순위 | 예제 |
|------|--------|---------|---------|------|
| **P1** | 서비스 다운 | 즉시 | 🔴 긴급 | 모든 요청 실패 |
| **P2** | 심각한 기능 장애 | 15분 | 🟠 높음 | 에러율 > 5% |
| **P3** | 부분 기능 장애 | 1시간 | 🟡 중간 | 특정 기능만 오류 |
| **P4** | 경미한 문제 | 1일 | 🟢 낮음 | 사소한 버그 |

---

## 1️⃣ 기본 검사

### 서비스 상태 확인

```bash
# Cloud Run 서비스 상태
gcloud run services list --project=$GCP_PROJECT_ID
gcloud run services describe ion-api --region=us-central1 --project=$GCP_PROJECT_ID

# 최근 배포 확인
gcloud run services describe ion-api \
  --region=us-central1 \
  --format='value(spec.template.spec.containers[0].image)' \
  --project=$GCP_PROJECT_ID

# 서비스 로그 (최근 100줄)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ion-api" \
  --limit=100 \
  --format=json \
  --project=$GCP_PROJECT_ID | jq '.[] | "\(.timestamp): \(.severity) - \(.jsonPayload.message)"'

# 헬스 체크
curl -i https://api.ion-mentoring.com/health
# 예상: HTTP 200, Content-Type: application/json

# 서비스 메트릭
gcloud monitoring time-series list \
  --filter='metric.type=run.googleapis.com/request_count AND resource.labels.service_name=ion-api' \
  --project=$GCP_PROJECT_ID
```

### 네트워크 연결 확인

```bash
# DNS 해석
nslookup api.ion-mentoring.com
dig api.ion-mentoring.com

# 포트 접근성
nc -zv api.ion-mentoring.com 443

# SSL 인증서
openssl s_client -connect api.ion-mentoring.com:443 -servername api.ion-mentoring.com

# HTTP 헤더 확인
curl -i -X OPTIONS https://api.ion-mentoring.com/chat \
  -H "Origin: https://app.ion-mentoring.com"
```

### 보안 정책 확인

```bash
# Cloud Armor 정책 확인
gcloud compute security-policies describe ion-api-armor \
  --project=$GCP_PROJECT_ID

# 차단된 요청 로그
gcloud logging read "resource.type=security_policy AND jsonPayload.enforcement_level=DENY" \
  --limit=50 \
  --project=$GCP_PROJECT_ID
```

---

## 2️⃣ API/응답 문제

### P1: 서비스 완전 다운

**증상**: 모든 요청이 실패, HTTP 502/503

**진단**:
```bash
# 1. 서비스 상태 확인
gcloud run services describe ion-api --region=us-central1 --project=$GCP_PROJECT_ID

# 2. 최근 배포 확인
gcloud run revisions list --service=ion-api --region=us-central1 --project=$GCP_PROJECT_ID

# 3. 에러 로그 확인
gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR" \
  --limit=100 \
  --project=$GCP_PROJECT_ID

# 4. 리소스 사용량
gcloud monitoring time-series list \
  --filter='metric.type=run.googleapis.com/container_memory_utilization' \
  --project=$GCP_PROJECT_ID
```

**해결 방법**:

```bash
# 옵션 1: 이전 리비전으로 롤백
PREVIOUS_REVISION=$(gcloud run revisions list \
  --service=ion-api \
  --limit=2 \
  --format='value(REVISION)' | tail -1)

gcloud run services update-traffic ion-api \
  --to-revisions=$PREVIOUS_REVISION=100 \
  --region=us-central1 \
  --project=$GCP_PROJECT_ID

# 옵션 2: 서비스 재배포
gcloud run deploy ion-api \
  --image=gcr.io/$GCP_PROJECT_ID/ion-api:latest \
  --region=us-central1 \
  --project=$GCP_PROJECT_ID

# 옵션 3: 리소스 제한 증가
gcloud run services update ion-api \
  --memory=2Gi \
  --cpu=2 \
  --timeout=120 \
  --region=us-central1 \
  --project=$GCP_PROJECT_ID
```

### P2: 높은 에러율 (> 5%)

**증상**: 많은 요청이 실패 (HTTP 500, 503)

**진단**:
```bash
# 에러율 확인
gcloud logging read "resource.type=cloud_run_revision" \
  --format='table(timestamp,httpRequest.status)' \
  --limit=200 \
  --project=$GCP_PROJECT_ID | \
  awk '{print $3}' | \
  sort | uniq -c | sort -rn

# 특정 에러 상세
gcloud logging read "resource.type=cloud_run_revision AND httpRequest.status>=500" \
  --format='value(jsonPayload.message)' \
  --limit=50 \
  --project=$GCP_PROJECT_ID
```

**일반적 원인**:

| 원인 | 증상 | 해결 |
|------|------|------|
| 데이터베이스 다운 | PostgreSQL 연결 에러 | DB 상태 확인, 재부팅 |
| 메모리 부족 | Out of Memory 에러 | 메모리 증가 또는 스케일 |
| 외부 API 오류 | timeout, 503 에러 | 재시도 로직, 타임아웃 증가 |
| 설정 오류 | 초기화 실패 | 환경 변수 확인 |

### P3: 특정 엔드포인트만 실패

**진단**:
```bash
# 엔드포인트별 에러율
gcloud logging read "resource.type=cloud_run_revision" \
  --format='table(timestamp,httpRequest.requestUrl,httpRequest.status)' \
  --limit=500 \
  --project=$GCP_PROJECT_ID | \
  awk '{print $3, $4}' | \
  sort | uniq -c

# 특정 경로 로그
gcloud logging read "resource.type=cloud_run_revision AND httpRequest.requestUrl=~/.*\/chat.*/" \
  --format='value(jsonPayload.message)' \
  --limit=50 \
  --project=$GCP_PROJECT_ID
```

**해결**:
```bash
# 1. 코드 확인 및 수정
# app/main.py에서 해당 엔드포인트 검사

# 2. 입력 데이터 검증
# 테스트: curl -X POST https://api.ion-mentoring.com/chat \
#   -H "Content-Type: application/json" \
#   -d '{"message":"test","user_id":"test"}'

# 3. 재배포
git push origin main  # CI/CD가 자동 배포
```

---

## 2️⃣ 성능 문제

### P2: 느린 응답 (P95 > 5s)

**증상**: 사용자가 느린 응답 보고, P95 > 5초

**진단**:
```bash
# 응답 시간 분석 (BigQuery)
bq query --use_legacy_sql=false '
SELECT
  TIMESTAMP_TRUNC(timestamp, MINUTE) as minute,
  APPROX_QUANTILES(CAST(latency_ms AS INT64), 100)[OFFSET(95)] as p95_latency,
  COUNT(*) as request_count
FROM `'$GCP_PROJECT_ID'.cloud_logging.requests_*`
WHERE DATE(_TABLE_SUFFIX) = CURRENT_DATE()
  AND endpoint = "/chat"
GROUP BY minute
ORDER BY minute DESC
LIMIT 60
'

# 느린 쿼리 찾기
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.query_time_ms >= 1000" \
  --limit=50 \
  --project=$GCP_PROJECT_ID
```

**원인 분석**:

| 원인 | 확인 방법 | 해결 |
|------|---------|------|
| DB 성능 | `EXPLAIN ANALYZE` | 인덱스 추가, 쿼리 최적화 |
| 외부 API 느림 | 타임아웃 로그 | 타임아웃 증가, 캐시 추가 |
| 메모리 부족 | GC 로그 | 메모리 증가, 캐시 정리 |
| 높은 트래픽 | 요청 수 급증 | 자동 스케일, 속도 제한 |

**해결**:

```bash
# 1. 데이터베이스 쿼리 최적화
# Cloud SQL 인스턴스 접속
gcloud sql connect ion-db --user=postgres

# 느린 쿼리 분석
SELECT
  query,
  calls,
  mean_exec_time,
  total_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

# 인덱스 추가
CREATE INDEX idx_users_id ON users(id);
CREATE INDEX idx_chat_session_id ON chat_history(session_id);

# 2. 캐시 추가
# Redis 설정 (config/prod.yaml)
cache:
  enabled: true
  type: "redis"
  ttl_seconds: 3600

# 3. 스케일링
gcloud run services update ion-api \
  --min-instances=2 \
  --max-instances=100 \
  --region=us-central1 \
  --project=$GCP_PROJECT_ID
```

### P3: 메모리 누수 의심

**진단**:
```bash
# 메모리 사용 트렌드
gcloud monitoring time-series list \
  --filter='metric.type=run.googleapis.com/container_memory_utilization' \
  --project=$GCP_PROJECT_ID | jq '.timeSeries[].points | sort_by(.interval.end_time)'

# Python 메모리 프로파일
pip install memory-profiler
python -m memory_profiler app/main.py
```

**해결**:
```python
# app/main.py에서 메모리 누수 확인
import tracemalloc

tracemalloc.start()

# 문제 코드 실행
...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

---

## 3️⃣ 데이터베이스 문제

### P1: 데이터베이스 다운

**증상**: 데이터베이스 연결 실패

**진단**:
```bash
# Cloud SQL 상태
gcloud sql instances describe ion-db --project=$GCP_PROJECT_ID

# 연결 시도
gcloud sql connect ion-db --user=postgres

# 로그 확인
gcloud sql operations list --instance=ion-db --limit=20 --project=$GCP_PROJECT_ID
```

**해결**:
```bash
# 1. 인스턴스 상태 확인
gcloud sql instances describe ion-db --project=$GCP_PROJECT_ID | grep state

# 2. 재시작
gcloud sql instances restart ion-db --project=$GCP_PROJECT_ID

# 3. 백업에서 복구 (필요시)
gcloud sql backups list --instance=ion-db --limit=5 --project=$GCP_PROJECT_ID

# 최근 백업에서 복구
BACKUP_ID=$(gcloud sql backups list \
  --instance=ion-db \
  --limit=1 \
  --format='value(name)' \
  --project=$GCP_PROJECT_ID)

gcloud sql backups restore $BACKUP_ID \
  --backup-instance=ion-db \
  --target-instance=ion-db-restored \
  --project=$GCP_PROJECT_ID
```

### P2: 데이터베이스 디스크 가득 참

**증상**: 디스크 사용률 > 90%, 쓰기 오류

**진단**:
```bash
# 디스크 사용량
gcloud sql instances describe ion-db \
  --format='value(settings.settings.storageAutoResize,settings.settings.storageAutoResizeLimit)' \
  --project=$GCP_PROJECT_ID

# 데이터베이스 크기
gcloud sql connect ion-db --user=postgres << 'EOF'
SELECT
  datname,
  pg_size_pretty(pg_database.datlength) AS size
FROM pg_database
ORDER BY pg_database.datlength DESC;
EOF

# 테이블 크기
SELECT
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname='public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**해결**:
```bash
# 1. 자동 디스크 확장 활성화
gcloud sql instances patch ion-db \
  --enable-auto-resize \
  --auto-resize-limit=100 \
  --project=$GCP_PROJECT_ID

# 2. 인스턴스 업그레이드 (수동)
gcloud sql instances patch ion-db \
  --tier=db-custom-4-16384 \
  --project=$GCP_PROJECT_ID

# 3. 오래된 데이터 정리
gcloud sql connect ion-db --user=postgres << 'EOF'
-- 오래된 로그 삭제
DELETE FROM activity_logs WHERE created_at < NOW() - INTERVAL '90 days';

-- 미사용 세션 정리
DELETE FROM user_sessions WHERE last_activity < NOW() - INTERVAL '30 days';

-- 인덱스 재구성
REINDEX TABLE users;

-- 진공 정리
VACUUM FULL;
EOF
```

### P3: 느린 데이터베이스 쿼리

**진단**:
```bash
# 느린 쿼리 로그 활성화
gcloud sql instances patch ion-db \
  --database-flags=log_min_duration_statement=1000 \
  --project=$GCP_PROJECT_ID

# 느린 쿼리 확인
gcloud logging read "resource.type=cloudsql_database AND jsonPayload.duration_ms >= 1000" \
  --limit=50 \
  --project=$GCP_PROJECT_ID
```

**최적화**:
```sql
-- 쿼리 실행 계획 분석
EXPLAIN ANALYZE
SELECT * FROM chat_history
WHERE user_id = 'user123'
ORDER BY created_at DESC
LIMIT 100;

-- 인덱스 추가
CREATE INDEX CONCURRENTLY idx_chat_user_time
ON chat_history(user_id, created_at DESC);

-- 통계 업데이트
ANALYZE chat_history;

-- 인덱스 효율성 확인
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_tup_read DESC;
```

---

## 4️⃣ 캐시/Redis 문제

### P2: Redis 다운 또는 응답 느림

**진단**:
```bash
# Redis 상태 확인
redis-cli ping
# 응답: PONG (정상)

# 메모리 사용량
redis-cli info memory

# 느린 명령 로그
redis-cli slowlog get 10

# 키 수 확인
redis-cli dbsize
```

**해결**:
```bash
# 1. Redis 재시작
docker restart redis-container

# 또는 Memorystore
gcloud redis instances list --project=$GCP_PROJECT_ID

# 2. 메모리 정리
redis-cli FLUSHDB  # 주의: 모든 데이터 삭제

# 또는 선택적 정리
redis-cli EVICT ALLKEYS_LRU

# 3. 인스턴스 크기 증가
gcloud redis instances upgrade ion-redis \
  --size=2 \
  --project=$GCP_PROJECT_ID
```

---

## 5️⃣ 배포 문제

### P1: 배포 실패

**증상**: 배포가 실패하거나 극히 느림

**진단**:
```bash
# 최근 배포 상태
gcloud run services describe ion-api \
  --region=us-central1 \
  --project=$GCP_PROJECT_ID | grep -A5 "Latest"

# Cloud Build 로그
gcloud builds log $(gcloud builds list --limit=1 --format='value(id)') \
  --project=$GCP_PROJECT_ID

# 이미지 빌드 확인
gcloud container images list --project=$GCP_PROJECT_ID

# 최근 이미지
gcloud container images list-tags gcr.io/$GCP_PROJECT_ID/ion-api --limit=10
```

**해결**:

```bash
# 1. 로컬에서 빌드 테스트
docker build -t gcr.io/$GCP_PROJECT_ID/ion-api:test .

# 2. 이미지 테스트
docker run -p 8080:8080 gcr.io/$GCP_PROJECT_ID/ion-api:test

# 3. 수동 배포
gcloud run deploy ion-api \
  --image=gcr.io/$GCP_PROJECT_ID/ion-api:latest \
  --region=us-central1 \
  --project=$GCP_PROJECT_ID

# 4. 배포 로그 상세
gcloud run deploy ion-api \
  --image=gcr.io/$GCP_PROJECT_ID/ion-api:latest \
  --region=us-central1 \
  --project=$GCP_PROJECT_ID \
  --log \
  --verbose
```

### P2: 배포 후 서비스 다운

**증상**: 새 버전 배포 후 에러 발생

**해결**:
```bash
# 1. 즉시 롤백
gcloud run services update-traffic ion-api \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=us-central1 \
  --project=$GCP_PROJECT_ID

# 2. 문제 확인
gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR" \
  --limit=100 \
  --project=$GCP_PROJECT_ID

# 3. 환경 변수 확인
gcloud run services describe ion-api \
  --region=us-central1 \
  --format='value(spec.template.spec.containers[0].env)' \
  --project=$GCP_PROJECT_ID

# 4. Canary 배포로 재시도 (10% 트래픽)
gcloud run services update-traffic ion-api \
  --to-revisions=NEW_REVISION=10,STABLE_REVISION=90 \
  --region=us-central1 \
  --project=$GCP_PROJECT_ID
```

---

## 6️⃣ 모니터링/알림 문제

### P3: 알림이 오지 않음

**진단**:
```bash
# 알림 규칙 확인
gcloud alpha monitoring policies list --project=$GCP_PROJECT_ID

# 특정 정책 상세
gcloud alpha monitoring policies describe POLICY_ID --project=$GCP_PROJECT_ID

# 통보 채널 확인
gcloud alpha monitoring channels list --project=$GCP_PROJECT_ID
```

**해결**:
```bash
# 1. 통보 채널 테스트
gcloud alpha monitoring channels create \
  --display-name="Test Channel" \
  --type=email \
  --channel-labels=email_address=test@example.com \
  --project=$GCP_PROJECT_ID

# 2. 임계값 조정
gcloud alpha monitoring policies update POLICY_ID \
  --condition-threshold-value=10 \
  --project=$GCP_PROJECT_ID

# 3. 정책 재활성화
gcloud alpha monitoring policies update POLICY_ID \
  --enable \
  --project=$GCP_PROJECT_ID
```

---

## 📋 체크리스트: 정기 유지보수

### 일일 작업
- [ ] 서비스 상태 확인
- [ ] 에러율 모니터링
- [ ] 알림 검토
- [ ] 로그 분석

### 주간 작업
- [ ] 성능 메트릭 검토
- [ ] 데이터베이스 상태 확인
- [ ] 캐시 효율성 분석
- [ ] 보안 이벤트 검토

### 월간 작업
- [ ] 전체 시스템 점검
- [ ] 백업 테스트
- [ ] 복구 드릴
- [ ] 용량 계획 검토

### 분기별 작업
- [ ] 성능 최적화
- [ ] 보안 감시
- [ ] 아키텍처 검토
- [ ] 비용 최적화

---

## 📞 긴급 연락처

| 역할 | 이름 | 전화 | 이메일 |
|------|------|------|--------|
| **On-Call Engineer** | TBD | +1 (555) 123-4567 | oncall@ion-mentoring.com |
| **Database DBA** | TBD | +1 (555) 123-4568 | dba@ion-mentoring.com |
| **DevOps Lead** | TBD | +1 (555) 123-4569 | devops@ion-mentoring.com |

---

## 📚 추가 자료

- [Google Cloud Logging](https://cloud.google.com/logging/docs)
- [Cloud Run Troubleshooting](https://cloud.google.com/run/docs/troubleshooting/debugging)
- [PostgreSQL Monitoring](https://www.postgresql.org/docs/current/monitoring-stats.html)
- [Redis Command Reference](https://redis.io/commands/)

---

## 📅 다음 단계

✅ **Pre-commit hooks 설정 완료** (3시간)
✅ **WAF/Cloud Armor 설정 완료** (6시간)
✅ **추가 보안 테스트 개발 완료** (4시간)
✅ **Grafana 대시보드 설정 완료** (8시간)
✅ **트러블슈팅 가이드 완료** (8시간)
➡️ **Task 6: 재해 복구 계획 작성** (6시간)

총 소요 시간: Phase 2 **90시간** 중 **29시간** 완료 ✅
