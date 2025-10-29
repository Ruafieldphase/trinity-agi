# 🔍 배포 전 최종 검증 체크리스트

배포 48시간 전부터 배포 당일까지 수행할 최종 확인 사항

**목표**: 배포 위험도 최소화, 무중단 서비스 보장
**실행자**: 기술 리드 + 운영팀
**소요 시간**: 2시간

---

## 📋 배포 48시간 전 (Day -2)

### 1️⃣ 코드 최종 검증

#### 테스트 재확인
```bash
# 모든 테스트 실행
pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

# 예상 결과
# - 121개 테스트 모두 통과 ✅
# - 커버리지 88.10% 이상 ✅
# - 에러 0개 ✅
```

**체크항목**:
- [ ] 단위 테스트 (80+) 통과
- [ ] 통합 테스트 (18) 통과
- [ ] E2E 테스트 (23) 통과
- [ ] 커버리지 88%+ 확인

#### 코드 품질 검사
```bash
# Ruff (Linting)
ruff check app/ --config pyproject.toml

# Black (Format)
black --check app/ tests/

# MyPy (Type checking)
mypy app/ --strict

# 예상: 모두 통과
```

**체크항목**:
- [ ] Ruff 경고 0개
- [ ] Black 포맷 OK
- [ ] MyPy 오류 0개

---

### 2️⃣ 환경 설정 최종 검증

#### 환경 변수 확인
```bash
# 모든 환경 변수 확인
echo $ENVIRONMENT                  # production
echo $CONFIG_PATH                  # config/prod.yaml
echo $VERTEX_PROJECT_ID            # [설정됨]
echo $VERTEX_LOCATION              # us-central1
echo $VERTEX_MODEL                 # gemini-1.5-flash-002
echo $GOOGLE_APPLICATION_CREDENTIALS  # [설정됨]
```

**체크항목**:
- [ ] ENVIRONMENT = production
- [ ] CONFIG_PATH 설정됨
- [ ] VERTEX_PROJECT_ID 설정됨
- [ ] 보안 키 모두 설정됨

#### 설정 파일 최종 검증
```bash
# 각 설정 파일 검증
cat config/prod.yaml | grep -E "^[a-z_]+:" | head -20

# 핵심 설정 확인
grep -E "(database|redis|rate_limit|timeout)" config/prod.yaml
```

**체크항목**:
- [ ] prod.yaml 정상 형식
- [ ] database 설정 OK
- [ ] redis 설정 OK
- [ ] timeout 설정 적절

---

### 3️⃣ 배포 인프라 최종 확인

#### Cloud Run 설정 재확인
```bash
# 현재 서비스 상태 확인
gcloud run services describe ion-api-prod \
  --region us-central1 \
  --format="table(status, config.template.spec.containerSpec.image)"

# 확인사항:
# - 이미지: gcr.io/PROJECT/ion-api:latest
# - 메모리: 1Gi
# - CPU: 1
```

**체크항목**:
- [ ] 현재 이미지 정상
- [ ] 메모리 1Gi 설정
- [ ] CPU 1 설정
- [ ] 타임아웃 600초 설정

#### 데이터베이스 연결 확인
```bash
# Cloud SQL 프록시 상태
gcloud sql instances describe ion-db-prod \
  --format="table(state, databaseVersion)"

# 백업 상태 확인
gcloud sql backups list --instance=ion-db-prod --limit=3
```

**체크항목**:
- [ ] DB 인스턴스 상태: RUNNABLE
- [ ] 최근 백업 확인
- [ ] 연결 테스트 성공

#### 캐시 (Redis) 확인
```bash
# Memorystore 상태
gcloud redis instances describe ion-cache-prod \
  --region=us-central1 \
  --format="table(state)"

# 메모리 사용 확인
gcloud redis instances describe ion-cache-prod \
  --region=us-central1 \
  --format="value(size_gb)"
```

**체크항목**:
- [ ] Redis 인스턴스 READY
- [ ] 메모리 충분 (1GB+)

---

### 4️⃣ 모니터링 대시보드 최종 확인

#### Google Cloud Console 대시보드
```bash
# 대시보드 확인
gcloud monitoring dashboards list --filter="displayName:ION*"

# 예상: 3개 대시보드 (성능, 에러, 비즈니스)
```

**체크항목**:
- [ ] 성능 메트릭 대시보드 활성화
- [ ] 에러 모니터링 대시보드 활성화
- [ ] 알림 정책 활성화

#### 알림 규칙 확인
```bash
# 활성 알림 정책
gcloud alpha monitoring policies list \
  --filter="displayName:ION*"

# 예상: 5+ 알림 정책
```

**체크항목**:
- [ ] Critical 알림 설정 (P95 > 5s)
- [ ] Error 알림 설정 (에러율 > 10%)
- [ ] Warning 알림 설정 (P95 > 3s)

---

## 📋 배포 24시간 전 (Day -1)

### 1️⃣ 최종 연습 배포

#### 스테이징 배포 최종 확인
```bash
# 최신 스테이징 상태 확인
gcloud run services describe ion-api-staging \
  --region us-central1

# 스테이징에서 E2E 테스트 실행
curl https://ion-api-staging.run.app/health

# 샘플 채팅 테스트
curl -X POST https://ion-api-staging.run.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "최종 배포 전 테스트"}'
```

**체크항목**:
- [ ] 스테이징 헬스 체크 OK
- [ ] 샘플 요청 응답 정상
- [ ] 로그 출력 정상

---

### 2️⃣ 팀 최종 확인

#### 개발팀 확인
```
□ 담당자: [이름]
□ 연락처: [번호]
□ 상태: 배포 준비 완료
□ 이슈: 없음
```

#### 운영팀 확인
```
□ 담당자: [이름]
□ 연락처: [번호]
□ 모니터링: 준비 완료
□ 긴급 대응: 준비 완료
```

#### 보안팀 확인
```
□ 담당자: [이름]
□ 보안 감사: 완료
□ 신고 채널: 활성화
□ 이슈: 없음
```

**체크항목**:
- [ ] 모든 담당자 확인 완료
- [ ] 연락처 확인 완료
- [ ] 긴급 상황 대응 계획 수립

---

### 3️⃣ 배포 계획 최종 리뷰

#### 배포 일정 확인
```
배포 날짜: 2025년 10월 21일 (월) ✓
배포 시간: 10:00 ~ 12:00 (KST) ✓
배포 담당: [이름] ✓
백업 담당: [이름] ✓
```

#### 롤백 계획 확인
```
롤백 대상: ion-api-prod (이전 버전)
롤백 시간: < 5분
롤백 테스트: 완료됨 ✓
```

**체크항목**:
- [ ] 배포 시간 팀원 모두 확인
- [ ] 롤백 계획 문서 준비
- [ ] 롤백 테스트 완료

---

### 4️⃣ 커뮤니케이션 최종 확인

#### 고객 지원팀 공지
```
[ ] 배포 예정 공지
[ ] 예상 다운타임: 0분 (무중단)
[ ] 문제 발생 시 연락처 제공
[ ] FAQ 준비
```

#### 내부 팀 공지
```
[ ] Slack #announcements 공지
[ ] 이메일 공지
[ ] 모바일 온콜 시스템 활성화
[ ] 대기실 준비
```

**체크항목**:
- [ ] 고객 공지 완료
- [ ] 내부 공지 완료
- [ ] 온콜 팀 대기 상태

---

## 🔴 배포 당일 (Day 0)

### 1️⃣ 배포 1시간 전 (T-60분)

#### 최종 상태 확인
```bash
# 현재 프로덕션 상태
gcloud run services describe ion-api-prod \
  --region us-central1 \
  --format="table(status, config.template.metadata.generation)"

# 로그 확인 (이상 없는지)
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity="ERROR"' \
  --limit=20
```

**체크항목**:
- [ ] 프로덕션 정상 작동 중
- [ ] 에러 로그 없음
- [ ] 성능 메트릭 정상

#### 팀 최종 대기
```
[ ] 배포 담당자: 스탠바이 ✓
[ ] 운영팀: 모니터링 준비 ✓
[ ] 개발팀: 롤백 준비 ✓
[ ] 보안팀: 대기 중 ✓
```

---

### 2️⃣ 배포 실행 (T+0분)

#### 배포 명령 실행
```bash
# 새 이미지 빌드 및 푸시
docker build -t gcr.io/PROJECT/ion-api:v1.2.3 .
docker push gcr.io/PROJECT/ion-api:v1.2.3

# Cloud Run 배포 (카나리 - 10% 트래픽)
gcloud run deploy ion-api-prod \
  --image gcr.io/PROJECT/ion-api:v1.2.3 \
  --traffic LATEST=10,PREVIOUS=90 \
  --region us-central1 \
  --no-traffic-initially
```

**체크항목**:
- [ ] 배포 명령 실행
- [ ] 배포 상태 확인 중
- [ ] 초기 에러 모니터링

---

### 3️⃣ 배포 후 모니터링 (T+30분)

#### 즉시 모니터링
```bash
# 새 버전 상태 확인
gcloud run services describe ion-api-prod \
  --format="table(status.latestRevisionName)"

# 에러율 확인
gcloud logging read \
  'severity="ERROR" AND resource.labels.service_name="ion-api-prod"' \
  --limit=50
```

**모니터링 항목**:
- [ ] 배포된 리비전 정상 작동
- [ ] 에러율 < 1%
- [ ] 응답 시간 < 2초 (P95)

#### 트래픽 점진적 전환
```bash
# 10분 후: 트래픽 50% 전환
gcloud run deploy ion-api-prod \
  --traffic LATEST=50,PREVIOUS=50 \
  --region us-central1

# 모니터링 (10분)
sleep 600

# 30분 후: 트래픽 100% 전환
gcloud run deploy ion-api-prod \
  --traffic LATEST=100 \
  --region us-central1
```

**체크항목**:
- [ ] 트래픽 50% 전환 후 정상
- [ ] 에러 증가 없음
- [ ] 성능 저하 없음
- [ ] 트래픽 100% 전환 완료

---

### 4️⃣ 최종 검증 (T+90분)

#### 기능 검증
```bash
# 헬스 체크
curl https://ion-api-prod.run.app/health

# 채팅 기능 (각 페르소나)
for persona in "Lua" "Elro" "Riri" "Nana"; do
  curl -X POST https://ion-api-prod.run.app/chat \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"테스트 - $persona\"}"
done

# API 문서 확인
curl https://ion-api-prod.run.app/docs
```

**체크항목**:
- [ ] 헬스 체크 200 OK
- [ ] 모든 페르소나 정상 응답
- [ ] API 문서 접근 가능

#### 성능 검증
```bash
# 응답 시간 확인
gcloud logging read \
  'resource.type="cloud_run_revision" AND jsonPayload.process_time_ms' \
  --limit=100 \
  --format json | \
  jq '[.[].jsonPayload.process_time_ms] | {p50: .[length*0.5], p95: .[length*0.95], p99: .[length*0.99]}'
```

**성능 목표**:
- [ ] P50 < 1초
- [ ] P95 < 2초
- [ ] P99 < 5초

#### 팀 최종 확인
```
[ ] 배포 담당자: 배포 성공 확인 ✓
[ ] 운영팀: 모니터링 상태 정상 ✓
[ ] 개발팀: 롤백 준비 완료 (필요시) ✓
[ ] 보안팀: 이상 없음 ✓
```

---

## ✅ 최종 배포 완료 (T+120분)

### 사후 조치

#### 배포 완료 공지
```bash
# Slack에 배포 완료 공지
# 고객 지원팀에 배포 완료 안내
# 팀에 최종 리포트 공유
```

**공지 항목**:
- [ ] 배포 성공 공지
- [ ] 성능 메트릭 요약
- [ ] 향후 계획 안내

#### 모니터링 전환
```bash
# 24시간 모니터링 시작
# Slack #production-alerts 채널 활성화
# 온콜 팀 대기 시스템 가동
```

**모니터링**:
- [ ] 24/7 모니터링 시작
- [ ] 알림 시스템 활성화
- [ ] 로깅 정상 작동

---

## 🔙 롤백 판단 기준

### 즉시 롤백 (< 5분)

```
다음 중 하나라도 발생 시:
□ 에러율 > 50%
□ P95 응답 시간 > 10초
□ 메모리 > 900MB
□ 주요 기능 작동 안 함
□ 데이터 손상 발생
```

### 관찰 롤백 (5-30분)

```
다음 중 하나라도 지속 시:
□ 에러율 > 10%
□ P95 응답 시간 > 5초
□ 메모리 > 800MB
□ 성능 지표 급격한 저하
```

---

## 📊 최종 체크리스트 통합

### 배포 48시간 전
- [ ] 모든 테스트 통과 (121/121)
- [ ] 코드 품질 검사 완료
- [ ] 환경 설정 최종 확인
- [ ] 배포 인프라 준비 완료
- [ ] 모니터링 대시보드 활성화

### 배포 24시간 전
- [ ] 스테이징 최종 배포 확인
- [ ] 팀 최종 확인 완료
- [ ] 배포 계획 리뷰 완료
- [ ] 커뮤니케이션 완료
- [ ] 롤백 계획 검증

### 배포 당일
- [ ] 배포 1시간 전 최종 상태 확인
- [ ] 배포 실행 완료
- [ ] 트래픽 점진적 전환 완료
- [ ] 최종 검증 완료
- [ ] 배포 완료 공지

---

**배포 전 최종 검증 완료 체크리스트** ✅

이 체크리스트를 따르면 배포 위험도를 최소화하고 안정적인 배포를 보장할 수 있습니다.
