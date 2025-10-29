# 자동 백업 및 복구 절차 가이드 (2시간 작업)

## 📋 개요

**목표**: 데이터 손실 방지 및 신속한 복구 능력 확보
**현재 상태**: ⚠️ 없음 - 백업 정책 미설정
**목표 상태**: ✅ 자동 일일 백업, 7일 보존, RTO/RPO 정의

---

## 🎯 백업 목표 (RTO/RPO)

| 메트릭 | 목표 | 설명 |
|--------|------|------|
| **RTO** (Recovery Time Objective) | **1시간** | 서비스 복구까지 최대 1시간 |
| **RPO** (Recovery Point Objective) | **1일** | 최대 1일의 데이터 손실 허용 |
| **보존 기간** | **7일** | 7일간 백업 보관 |
| **백업 주기** | **매일 자정 UTC** | 자동 일일 백업 |

---

## 🏗️ 백업 대상

### 1. 데이터베이스 (Cloud SQL)
- ✅ PostgreSQL 데이터베이스 전체
- ✅ 자동 백업: 매일 자정
- ✅ 보존: 7일

### 2. 애플리케이션 설정
- ✅ Kubernetes ConfigMaps
- ✅ Google Secret Manager 비밀
- ✅ Cloud Storage 설정

### 3. 캐시 (Redis)
- ✅ Redis 데이터 (선택사항)
- ✅ 영구화: 디스크 저장
- ✅ 중요도: 낮음 (다시 생성 가능)

### 4. 애플리케이션 코드
- ✅ Git 리포지토리 (GitHub)
- ✅ Docker 이미지 (Container Registry)

---

## ✅ Cloud SQL 자동 백업 설정

### Step 1: GCP 프로젝트 설정

```bash
# 프로젝트 ID 설정
export GCP_PROJECT_ID="your-project-id"
export INSTANCE_NAME="ion-db"
export REGION="us-central1"

gcloud config set project $GCP_PROJECT_ID
```

### Step 2: Cloud SQL 인스턴스 확인

```bash
# 기존 인스턴스 확인
gcloud sql instances describe $INSTANCE_NAME --project=$GCP_PROJECT_ID

# 또는 나열
gcloud sql instances list --project=$GCP_PROJECT_ID
```

### Step 3: 자동 백업 정책 설정

```bash
# Cloud SQL 자동 백업 활성화
gcloud sql instances patch $INSTANCE_NAME \
  --backup-start-time=00:00 \
  --enable-bin-log \
  --retained-backups-count=7 \
  --transaction-log-retention-days=7 \
  --project=$GCP_PROJECT_ID

# 설정 확인
gcloud sql instances describe $INSTANCE_NAME \
  --format="value(settings.backupConfiguration)" \
  --project=$GCP_PROJECT_ID
```

**설정 상세**:
- `--backup-start-time=00:00`: 매일 자정 UTC 백업 시작
- `--enable-bin-log`: 바이너리 로그 활성화 (Point-in-time 복구)
- `--retained-backups-count=7`: 7개 백업 보관
- `--transaction-log-retention-days=7`: 트랜잭션 로그 7일 보존

### Step 4: 백업 확인

```bash
# 백업 목록 조회
gcloud sql backups list \
  --instance=$INSTANCE_NAME \
  --project=$GCP_PROJECT_ID

# 최근 백업 상세 정보
gcloud sql backups describe <BACKUP_ID> \
  --backup-instance=$INSTANCE_NAME \
  --project=$GCP_PROJECT_ID
```

---

## 🔄 복구 절차

### Scenario 1: 전체 데이터베이스 복구 (완전한 인스턴스 손실)

#### Step 1: 새 인스턴스 생성

```bash
# 새 Cloud SQL 인스턴스 생성
gcloud sql instances create ion-db-restored \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --region=$REGION \
  --backup-start-time=00:00 \
  --enable-bin-log \
  --project=$GCP_PROJECT_ID
```

#### Step 2: 백업에서 복구

```bash
# 최근 백업 ID 찾기
BACKUP_ID=$(gcloud sql backups list \
  --instance=$INSTANCE_NAME \
  --limit=1 \
  --format='value(name)' \
  --project=$GCP_PROJECT_ID)

# 백업에서 복구
gcloud sql backups restore $BACKUP_ID \
  --backup-instance=$INSTANCE_NAME \
  --backup-configuration=default \
  --target-instance=ion-db-restored \
  --project=$GCP_PROJECT_ID
```

#### Step 3: 데이터 검증

```bash
# 복구된 데이터베이스 접근
gcloud sql connect ion-db-restored \
  --user=postgres \
  --project=$GCP_PROJECT_ID

# SQL 프롬프트에서
SELECT COUNT(*) FROM personas;
SELECT COUNT(*) FROM conversations;
```

#### Step 4: 트래픽 전환 (필요시)

```bash
# Cloud SQL 프록시 업데이트 또는
# 애플리케이션 DATABASE_HOST 환경 변수 변경

# 기존 인스턴스 삭제 (데이터 확인 후)
gcloud sql instances delete $INSTANCE_NAME \
  --project=$GCP_PROJECT_ID

# 복구된 인스턴스 이름 변경
# (CLI로는 불가능 - Google Cloud Console에서 처리)
```

### Scenario 2: Point-in-Time 복구 (특정 시점 데이터)

```bash
# 특정 시점으로 복구 (예: 2024-01-15 14:30:00 UTC)
gcloud sql backups restore <BACKUP_ID> \
  --backup-instance=$INSTANCE_NAME \
  --backup-configuration=default \
  --target-instance=ion-db-pitr \
  --point-in-time="2024-01-15T14:30:00Z" \
  --project=$GCP_PROJECT_ID

# 또는 Cloud SQL 콘솔에서 "복구" 선택 후 시간 지정
```

### Scenario 3: 특정 테이블만 복구

```bash
# 1. 임시 데이터베이스 생성 및 복구
gcloud sql backups restore <BACKUP_ID> \
  --backup-instance=$INSTANCE_NAME \
  --target-instance=ion-db-temp \
  --project=$GCP_PROJECT_ID

# 2. 프롬프트에서 테이블 dump
gcloud sql connect ion-db-temp \
  --user=postgres \
  --project=$GCP_PROJECT_ID \
  --database=ion_db \
  -- pg_dump --table=table_name > table_backup.sql

# 3. 원본 데이터베이스로 복원
psql -h <original-db-ip> -U postgres ion_db < table_backup.sql

# 4. 임시 인스턴스 삭제
gcloud sql instances delete ion-db-temp \
  --project=$GCP_PROJECT_ID
```

---

## 🛡️ Secret Manager 백업 (구성 정보)

### Backup Secrets

```bash
# 모든 비밀 백업
mkdir -p backups/secrets
for secret in $(gcloud secrets list --format='value(name)' --project=$GCP_PROJECT_ID); do
  echo "Backing up secret: $secret"
  gcloud secrets versions access latest \
    --secret=$secret \
    --project=$GCP_PROJECT_ID > backups/secrets/$secret.txt
done

# 보안 스토리지에 저장 (암호화된 드라이브 또는 비공개 클라우드 스토리지)
```

### Restore Secrets

```bash
# 백업에서 비밀 복원
for secret_file in backups/secrets/*.txt; do
  secret_name=$(basename $secret_file .txt)
  echo "Restoring secret: $secret_name"
  cat $secret_file | gcloud secrets create $secret_name \
    --data-file=- \
    --project=$GCP_PROJECT_ID 2>/dev/null || echo "Secret already exists"
done
```

---

## 📋 백업 스케줄 및 감시

### 백업 스케줄 설정 (Cloud Scheduler)

```bash
# Cloud Scheduler 작업 생성 (백업 검증)
gcloud scheduler jobs create pubsub verify-backup \
  --location=$REGION \
  --schedule="0 2 * * *" \
  --topic=backup-verification \
  --message-body='{"action":"verify_backup"}' \
  --project=$GCP_PROJECT_ID

# Cloud Function으로 백업 검증 실행
# (다음 섹션 참조)
```

### 백업 검증 Cloud Function

**파일**: `functions/verify_backup.py`

```python
"""Google Cloud Function - 백업 검증"""

from google.cloud import sql_v1
from google.cloud import logging as cloud_logging
import json
from datetime import datetime, timedelta

def verify_backup(request):
    """
    매일 백업 검증 함수

    Cloud Scheduler에서 호출됨
    """
    client = sql_v1.SqlBackupsServiceClient()
    logging_client = cloud_logging.Client()
    log = logging_client.logger('backup-verification')

    project_id = "your-project-id"
    instance_name = "ion-db"

    try:
        # 최근 24시간 내 백업 확인
        backups = client.list(
            project="projects/{}/instances/{}".format(project_id, instance_name)
        )

        recent_backups = []
        now = datetime.utcnow()
        for backup in backups:
            created_time = backup.window_start_time
            if created_time and (now - created_time).total_seconds() < 86400:
                recent_backups.append(backup)

        if not recent_backups:
            log.error("⚠️ No backups found in last 24 hours", severity="WARNING")
            return json.dumps({
                "status": "warning",
                "message": "No recent backups"
            }), 200

        # 가장 최근 백업 정보
        latest = recent_backups[0]
        log.log_struct({
            "status": "success",
            "latest_backup_time": latest.window_start_time.isoformat(),
            "backup_type": latest.type_,
            "backup_size_bytes": latest.backup_configuration.get('size_bytes', 'unknown')
        }, severity="INFO")

        return json.dumps({
            "status": "success",
            "message": f"Latest backup: {latest.window_start_time}",
            "backup_count": len(recent_backups)
        }), 200

    except Exception as e:
        log.error(f"❌ Backup verification failed: {str(e)}", severity="ERROR")
        return json.dumps({
            "status": "error",
            "message": str(e)
        }), 500
```

---

## 💾 로컬 개발용 백업

### Docker Volume 백업 (개발용)

```bash
# PostgreSQL 컨테이너에서 로컬로 백업
docker exec ion-db-dev pg_dump -U postgres ion_db > backups/local_backup_$(date +%Y%m%d_%H%M%S).sql

# 또는 전체 데이터 볼륨 백업
docker run --rm -v ion_db_volume:/data -v $(pwd):/backup \
  alpine tar czf /backup/volume_backup_$(date +%Y%m%d).tar.gz -C /data .
```

### 로컬 복구 (개발용)

```bash
# 백업에서 복구
docker exec -i ion-db-dev psql -U postgres ion_db < backups/local_backup_YYYYMMDD_HHMMSS.sql

# 또는 새 컨테이너에서
docker run -d --name ion-db-restore \
  -v ion_db_restore:/var/lib/postgresql/data \
  postgres:15

docker exec -i ion-db-restore psql -U postgres < backups/local_backup.sql
```

---

## 📊 백업 체크리스트

### 배포 전 확인
- [ ] Cloud SQL 자동 백업 활성화
- [ ] 백업 스케줄: 매일 자정 UTC
- [ ] 보존 기간: 7일
- [ ] 바이너리 로그 활성화
- [ ] 트랜잭션 로그: 7일 보존

### 배포 후 검증
- [ ] 백업 목록 확인
- [ ] 복구 테스트 실행
- [ ] 복구 시간 측정 (RTO)
- [ ] 데이터 정합성 검증 (RPO)

### 정기 검증 (월 1회)
- [ ] 백업 목록 확인
- [ ] 최근 백업 크기 확인 (이상 탐지)
- [ ] 복구 테스트 실행
- [ ] Point-in-time 복구 테스트

---

## 🚨 복구 시나리오별 SOP

### 📌 Incident 1: 데이터베이스 인스턴스 다운

**발생**: Cloud SQL 인스턴스 장애
**RTO**: 1시간
**RPO**: 1일

**절차**:
1. 문제 확인 (Console 또는 Monitoring)
2. 최근 백업 확인
3. 새 인스턴스 생성
4. 백업에서 복구
5. 애플리케이션 DB 엔드포인트 변경
6. 헬스체크 확인

### 📌 Incident 2: 실수로 데이터 삭제

**발생**: 잘못된 DELETE 쿼리 실행
**RTO**: 30분
**RPO**: 1일 이전

**절차**:
1. 삭제 시간 확인
2. Point-in-time 복구 설정
3. 임시 인스턴스 생성
4. 필요한 데이터 추출
5. 원본 데이터베이스에 복원

### 📌 Incident 3: 디스크 용량 초과

**발생**: 데이터베이스 디스크 가득 찬 상황
**RTO**: 30분
**RPO**: 0 (무손실)

**절차**:
1. 인스턴스 업그레이드 (더 큰 디스크)
2. 또는 데이터 정리 (이전 로그 삭제)
3. 모니터링 설정 (디스크 사용량 >= 80%)

---

## 📅 복구 테스트 일정

```
매월 1일: 전체 백업 복구 테스트
- 새 인스턴스 생성
- 최근 백업에서 복구
- 데이터 검증
- 성능 테스트
- 인스턴스 삭제

매월 15일: Point-in-time 복구 테스트
- 특정 시점 지정
- 임시 인스턴스 생성
- 복구 시간 측정
- 데이터 정합성 검증
```

---

## 📞 문제 해결

### 문제: "Backup not found"

**원인**: 백업이 아직 생성되지 않음

**해결**:
1. 백업 스케줄 확인
2. 자동 백업 정책 재설정
3. 수동 백업 생성

```bash
gcloud sql backups create \
  --instance=$INSTANCE_NAME \
  --project=$GCP_PROJECT_ID
```

### 문제: "복구 실패 - 공간 부족"

**원인**: 대상 인스턴스 디스크 용량 부족

**해결**:
1. 더 큰 인스턴스 생성
2. 또는 기존 인스턴스 업그레이드 후 복구

### 문제: "네트워크 연결 실패"

**원인**: 복구된 인스턴스에 접근 불가

**해결**:
1. VPC/방화벽 규칙 확인
2. Cloud SQL Proxy 실행
3. IP 화이트리스트 확인

---

## 📋 배포 후 모니터링

### Cloud Monitoring 대시보드 생성

```bash
# Cloud Monitoring 알림 설정
gcloud alpha monitoring policies create \
  --notification-channels=[CHANNEL_ID] \
  --display-name="Database Backup Verification" \
  --condition-display-name="No backups in 24h" \
  --condition-threshold-value=0 \
  --condition-threshold-duration=3600s
```

### Cloud Logging 쿼리

```sql
-- 백업 생성 로그 확인
resource.type="cloudsql_database"
AND protoPayload.methodName="cloudsql.instances.backups.create"

-- 복구 작업 확인
resource.type="cloudsql_database"
AND protoPayload.methodName="cloudsql.instances.backups.restore"

-- 백업 실패 확인
resource.type="cloudsql_database"
AND severity="ERROR"
```

---

## 📅 다음 단계

✅ **CORS 보안 강화 완료** (0.5시간)
✅ **Google Secret Manager 통합 완료** (4시간)
✅ **자동 백업 및 복구 절차 완료** (2시간)
➡️ **Task 4: 모니터링 및 알림 설정** (4시간)

총 소요 시간: Phase 1 **11시간** 중 **6.5시간** 완료 ✅
