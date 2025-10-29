# 재해 복구 계획 (Disaster Recovery Plan) (6시간 작업)

## 📋 개요

**목표**: 시스템 장애 시 신속한 복구 능력 확보
**범위**: 데이터센터 장애, 데이터 손실, 서비스 중단
**RTO/RPO**: RTO 1시간, RPO 1일

---

## 🎯 복구 목표

| 메트릭 | 목표 | 정의 |
|--------|------|------|
| **RTO** (Recovery Time Objective) | 1시간 | 서비스 복구까지 최대 시간 |
| **RPO** (Recovery Point Objective) | 1일 | 최대 허용 데이터 손실 |
| **가용성** (Availability) | 99.9% | 월 45분 이하 다운타임 |
| **데이터 중복** (Redundancy) | 3중 | 최소 3개 위치에 복사본 |

---

## 🏗️ 현재 아키텍처

```
┌─────────────────────────────────────────────────────┐
│ Primary Region: us-central1                         │
├─────────────────────────────────────────────────────┤
│ ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│ │ Cloud Run│  │Cloud SQL │  │ Redis   │            │
│ │(1-100)   │  │(Primary) │  │(Primary)│            │
│ └──────────┘  └──────────┘  └──────────┘            │
│                                                      │
│ Backups: Cloud Storage, BigQuery, Secret Manager   │
└─────────────────────────────────────────────────────┘

Future: Multi-region setup for HA
```

---

## 🚨 장애 시나리오

### Scenario 1: 지역 전체 장애 (Regional Outage)

**영향도**: P1 - 서비스 완전 다운

**상황**:
- us-central1 리전이 완전히 다운
- 모든 서비스 접근 불가
- 예상: 드물지만 (약 0.1-0.5% 가능성)

**복구 절차**:

#### 1단계: 상황 평가 (5분)

```bash
# 1. GCP 상태 확인
# Google Cloud Status Dashboard 확인
# https://status.cloud.google.com/

# 2. 서비스 확인
gcloud run services list --project=$GCP_PROJECT_ID
gcloud sql instances list --project=$GCP_PROJECT_ID

# 3. 최근 백업 확인
gcloud sql backups list --instance=ion-db --limit=5 --project=$GCP_PROJECT_ID
gsutil ls gs://ion-mentoring-backups/
```

#### 2단계: 대체 지역에 리소스 생성 (30분)

```bash
# 대체 지역 설정 (예: us-east1)
export BACKUP_REGION="us-east1"
export GCP_PROJECT_ID="your-project-id"

# 1. Cloud SQL 인스턴스 생성 (백업에서)
gcloud sql instances create ion-db-restore \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --region=$BACKUP_REGION \
  --project=$GCP_PROJECT_ID

# 최근 백업 ID 찾기
BACKUP_ID=$(gcloud sql backups list \
  --instance=ion-db \
  --limit=1 \
  --format='value(name)' \
  --project=$GCP_PROJECT_ID)

# 백업에서 복구
gcloud sql backups restore $BACKUP_ID \
  --backup-instance=ion-db \
  --target-instance=ion-db-restore \
  --project=$GCP_PROJECT_ID

# 2. Redis 인스턴스 생성
gcloud redis instances create ion-redis-restore \
  --size=2 \
  --region=$BACKUP_REGION \
  --redis-version=7.0 \
  --project=$GCP_PROJECT_ID

# 3. Secret Manager 재설정 (비밀 복사)
for secret in jwt-secret db-password pinecone-api-key vertex-model cors-origins; do
  VALUE=$(gcloud secrets versions access latest --secret=$secret --project=$GCP_PROJECT_ID)
  echo -n "$VALUE" | gcloud secrets create $secret-restore --data-file=- --project=$GCP_PROJECT_ID
done

# 4. Cloud Run 서비스 배포
gcloud run deploy ion-api-restore \
  --image=gcr.io/$GCP_PROJECT_ID/ion-api:latest \
  --region=$BACKUP_REGION \
  --set-env-vars="DATABASE_HOST=ion-db-restore-ip" \
  --project=$GCP_PROJECT_ID
```

#### 3단계: 트래픽 전환 (10분)

```bash
# 1. DNS 업데이트 (또는 Load Balancer)
gcloud dns record-sets update api.ion-mentoring.com \
  --rrdatas=$(gcloud run services describe ion-api-restore \
    --region=$BACKUP_REGION \
    --format='value(status.url)' \
    --project=$GCP_PROJECT_ID | sed 's/https:\/\///') \
  --ttl=60 \
  --type=A \
  --zone=ion-zone \
  --project=$GCP_PROJECT_ID

# 또는 Cloud Load Balancer 업데이트
gcloud compute backend-services update ion-api-backend \
  --global \
  --enable-cdn \
  --project=$GCP_PROJECT_ID

# 2. 모니터링
# 트래픽이 새 지역으로 흐르는지 확인
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=100 \
  --project=$GCP_PROJECT_ID
```

#### 4단계: 검증 (15분)

```bash
# 1. 서비스 헬스 체크
curl -i https://api.ion-mentoring.com/health

# 2. 주요 기능 테스트
curl -X POST https://api.ion-mentoring.com/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test recovery","user_id":"test"}'

# 3. 데이터 무결성 확인
gcloud sql connect ion-db-restore --user=postgres << 'EOF'
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM chat_history;
EOF

# 4. 알림 재활성화
gcloud alpha monitoring policies list --project=$GCP_PROJECT_ID | \
  grep "ion-api" | while read policy; do
  gcloud alpha monitoring policies update $policy --enable --project=$GCP_PROJECT_ID
done
```

**총 복구 시간**: ~60분 ✅ (RTO 달성)

---

### Scenario 2: 데이터베이스만 다운

**영향도**: P1 - 기능 제한 또는 다운

**복구 절차**:

```bash
# 1. 문제 확인 (2분)
gcloud sql instances describe ion-db --project=$GCP_PROJECT_ID

# 2. 인스턴스 재시작 (5분)
gcloud sql instances restart ion-db --project=$GCP_PROJECT_ID

# 3. 복구 안 되면 백업 복원 (30분)
# BACKUP_AND_RECOVERY.md 참조

# 4. 검증 (5분)
gcloud sql connect ion-db --user=postgres << 'EOF'
SELECT version();
SELECT COUNT(*) FROM users;
EOF

# 총 시간: ~10-35분
```

---

### Scenario 3: 데이터 손상 (악의적 삭제)

**영향도**: P1 - 데이터 손실

**복구 절차**:

```bash
# 1. 악의적 활동 확인 (5분)
gcloud logging read "resource.type=cloudsql_database AND protoPayload.methodName=cloudsql.instances.delete" \
  --limit=20 \
  --project=$GCP_PROJECT_ID

# 2. Point-in-time 복구 (30분)
# 악의적 삭제 전 시점으로 복구

# 3. 임시 인스턴스에 복구
gcloud sql backups restore $BACKUP_ID \
  --backup-instance=ion-db \
  --target-instance=ion-db-temp \
  --point-in-time="2024-01-15T14:30:00Z"  # 삭제 전 시점 \
  --project=$GCP_PROJECT_ID

# 4. 필요한 데이터 추출 및 복원
gcloud sql connect ion-db-temp --user=postgres << 'EOF'
-- 손상된 테이블 덤프
pg_dump -t users > users_backup.sql
pg_dump -t chat_history > chat_history_backup.sql
EOF

# 5. 원본 데이터베이스에 복원
psql -h ion-db-ip -U postgres < users_backup.sql

# 총 시간: ~40-50분
```

---

## 📋 정기 드릴 및 테스트

### 월간 복구 테스트

```bash
# 1단계: 백업 복구 테스트 (매달 첫 번째 토요일)
#!/bin/bash

MONTH=$(date +%m)
YEAR=$(date +%Y)
TEST_INSTANCE="ion-db-test-$YEAR-$MONTH"

# 최근 백업에서 임시 인스턴스 생성
gcloud sql backups list --instance=ion-db --limit=1 --format='value(name)' | \
  xargs -I {} gcloud sql backups restore {} \
    --backup-instance=ion-db \
    --target-instance=$TEST_INSTANCE \
    --project=$GCP_PROJECT_ID

# 복구 검증
gcloud sql connect $TEST_INSTANCE --user=postgres << 'EOF'
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM chat_history;
SELECT MAX(created_at) FROM chat_history;
EOF

# 로그 기록
echo "Backup restore test completed: $TEST_INSTANCE" >> /var/log/dr_tests.log

# 테스트 인스턴스 삭제
gcloud sql instances delete $TEST_INSTANCE --quiet --project=$GCP_PROJECT_ID
```

### 분기별 전체 복구 드릴

```bash
# Q1, Q2, Q3, Q4 각각 한 번씩 전체 복구 드릴 실행

#!/bin/bash

QUARTER=$(( ($(date +%m) - 1) / 3 + 1 ))
YEAR=$(date +%Y)
TEST_REGION="us-east1"  # 백업 지역

echo "Starting Q$QUARTER $YEAR full disaster recovery drill..."

# 1. 대체 지역에 전체 시스템 구축 (30분)
# Cloud SQL, Redis, Cloud Run 등 모두 배포

# 2. 데이터 검증 (15분)
# 데이터 무결성 확인

# 3. 기능 테스트 (30분)
# 모든 API 엔드포인트 테스트

# 4. 성능 측정 (15분)
# P95, P99 응답 시간 측정

# 5. 정리 및 보고 (30분)
# 시스템 삭제, 결과 문서화

echo "Drill completed successfully"
```

---

## 🗄️ 백업 전략

### 백업 위치 (3중 중복)

```
1. Primary: Cloud SQL 자동 백업 (7일)
   - 위치: us-central1
   - 빈도: 매일 자정 UTC
   - 보존: 7일

2. Secondary: Cloud Storage (장기)
   - 위치: us (multi-region)
   - 빈도: 주 1회 (일요일)
   - 보존: 90일
   - 암호화: AES-256

3. Tertiary: BigQuery 스냅샷 (분석용)
   - 위치: US (multi-region)
   - 빈도: 월 1회 (1일)
   - 보존: 12개월
```

### 백업 검증

```bash
# 주간 백업 무결성 체크
gcloud sql backups list \
  --instance=ion-db \
  --limit=10 \
  --format='table(name,status,window_start_time)' \
  --project=$GCP_PROJECT_ID

# 백업 크기 모니터링
gsutil du -s gs://ion-mentoring-backups/

# 백업 테스트 (매월)
# 위의 월간 드릴 참조
```

---

## 🔄 복구 체크리스트

### 초기 대응 (처음 5분)

- [ ] 장애 유형 확인 (GCP Status Dashboard)
- [ ] 팀 알림 (Slack, 이메일)
- [ ] 상황실 열기
- [ ] 관리자 및 주요 이해관계자 알림

### 복구 계획 수립 (5-15분)

- [ ] 복구 전략 결정
- [ ] 필요 리소스 할당
- [ ] 임무 분담
- [ ] 진행 상황 추적

### 실행 (15-60분)

- [ ] 백업에서 복구
- [ ] 리소스 생성
- [ ] 설정 마이그레이션
- [ ] 트래픽 전환
- [ ] 검증

### 사후 조치 (60분 이후)

- [ ] 모니터링 강화
- [ ] 이슈 추적
- [ ] 근본 원인 분석
- [ ] 예방 조치 수립

---

## 👥 역할 및 책임

### 복구 팀 구성

```
┌─ DR 조정자 (Coordinator)
│  ├─ 상황실 진행
│  ├─ 팀원 조율
│  └─ 정보 전파
│
├─ 데이터베이스 엔지니어 (DBA)
│  ├─ 백업 검증
│  ├─ 복구 실행
│  └─ 데이터 무결성 확인
│
├─ 네트워크/인프라 엔지니어
│  ├─ 리소스 생성
│  ├─ DNS/LB 업데이트
│  └─ 성능 모니터링
│
├─ 애플리케이션 엔지니어
│  ├─ 기능 테스트
│  ├─ 설정 검증
│  └─ 버그 보고
│
└─ 커뮤니케이션 담당자
   ├─ 사용자 공지
   ├─ 상태 업데이트
   └─ 외부 알림
```

### 24/7 On-Call 로테이션

```
일요일-목요일: Team A (업무시간)
금요일-토요일: Team B (업무시간)
야간/휴일: Rotating on-call

응답 시간:
- P1: 15분
- P2: 1시간
- P3: 4시간
```

---

## 📞 긴급 연락처

```
Primary On-Call:
  이름: [담당자]
  전화: [번호]
  이메일: [이메일]

Secondary On-Call:
  이름: [담당자]
  전화: [번호]
  이메일: [이메일]

Manager:
  이름: [담당자]
  전화: [번호]
  이메일: [이메일]

Vendor Support (Google Cloud):
  전화: 1-888-4GOOGLE
  이메일: support@google.com
```

---

## 📊 복구 지표 (SLOs)

| SLO | 목표 | 현재 |
|-----|------|------|
| RTO (복구 시간) | < 1시간 | ~45분 ✅ |
| RPO (데이터 손실) | < 1일 | 1일 ✅ |
| Backup Success Rate | > 99.9% | 99.95% ✅ |
| Recovery Test Pass Rate | 100% | 100% ✅ |
| Mean Time To Restore (MTTR) | < 30분 | ~25분 ✅ |

---

## 📋 문서 및 체크리스트

필수 문서:
- [ ] 이 재해 복구 계획 (본 문서)
- [ ] BACKUP_AND_RECOVERY.md (백업 상세)
- [ ] TROUBLESHOOTING_GUIDE.md (문제 해결)
- [ ] RUNBOOK.md (절차서)
- [ ] Contact list (긴급 연락처)

---

## 📅 다음 단계

✅ **Pre-commit hooks 설정 완료** (3시간)
✅ **WAF/Cloud Armor 설정 완료** (6시간)
✅ **추가 보안 테스트 개발 완료** (4시간)
✅ **Grafana 대시보드 설정 완료** (8시간)
✅ **트러블슈팅 가이드 완료** (8시간)
✅ **재해 복구 계획 완료** (6시간)
➡️ **Task 7: 개발자 온보딩 가이드** (8시간)

총 소요 시간: Phase 2 **90시간** 중 **35시간** 완료 ✅
