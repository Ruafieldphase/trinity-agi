# Week 3 Day 3: Cloud Run Deployment

**날짜**: 2025-10-17  
**작업 시간**: 14:00-18:00  
**목표**: Docker 이미지를 Google Cloud Run에 배포하여 프로덕션 환경 구축

---

## 📋 목차

- 사전 준비
- GCP 프로젝트 설정
- Artifact Registry 구성
- Docker 이미지 푸시
- Cloud Run 배포
- Secret Manager 연동
- 배포 검증
- 문제 해결
- 다음 단계

---

## ✅ 사전 준비

### 완료된 작업 (Day 1-2)

- ✅ FastAPI REST API 구현 (67 tests passing)
- ✅ Docker 이미지 빌드 (487MB)
- ✅ 로컬 컨테이너 테스트 완료

### 필요한 도구

```powershell
# Google Cloud SDK 설치 확인
gcloud version

# Docker 설치 확인
docker version

# 로그인 확인
gcloud auth list
```

### 환경 변수 준비

`.env.production` 파일 생성:

```bash
ENVIRONMENT=production
PORT=8080
LOG_LEVEL=INFO

# Vertex AI 설정
VERTEX_PROJECT_ID=your-gcp-project-id
VERTEX_LOCATION=us-central1
VERTEX_MODEL=gemini-1.5-flash-002

# 인증 (Cloud Run에서는 Secret Manager 사용)
# GOOGLE_APPLICATION_CREDENTIALS는 Secret으로 관리
```

---

## 🔧 GCP 프로젝트 설정

### 1. 프로젝트 확인 및 설정

```powershell
# 현재 프로젝트 확인
gcloud config get-value project

# 프로젝트 설정 (필요 시)
gcloud config set project YOUR_PROJECT_ID

# 프로젝트 정보 확인
gcloud projects describe YOUR_PROJECT_ID
```

### 2. 필요한 API 활성화

```powershell
# Cloud Run API
gcloud services enable run.googleapis.com

# Artifact Registry API
gcloud services enable artifactregistry.googleapis.com

# Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Vertex AI API (이미 활성화되어 있을 것)
gcloud services enable aiplatform.googleapis.com

# Cloud Logging API
gcloud services enable logging.googleapis.com
```

**예상 시간**: 2-3분 (API 활성화)

### 3. 기본 리전 설정

```powershell
# Cloud Run 리전 설정
gcloud config set run/region us-central1

# Artifact Registry 리전 설정
gcloud config set artifacts/location us-central1
```

---

## 📦 Artifact Registry 구성

### 1. Docker 리포지토리 생성

```powershell
# 리포지토리 생성
gcloud artifacts repositories create ion-api `
  --repository-format=docker `
  --location=us-central1 `
  --description="Ion API Docker images for Cloud Run"
```

**예상 결과**:

```text
Created repository [ion-api].
```

### 2. Docker 인증 구성

```powershell
# Artifact Registry에 Docker 인증
gcloud auth configure-docker us-central1-docker.pkg.dev
```

**예상 출력**:

```text
Adding credentials for: us-central1-docker.pkg.dev
Docker configuration file updated.
```

### 3. 리포지토리 확인

```powershell
# 생성된 리포지토리 목록
gcloud artifacts repositories list --location=us-central1
```

---

## 🚀 Docker 이미지 푸시

### 1. 이미지 태깅

```powershell
# 프로젝트 ID 가져오기
$PROJECT_ID = gcloud config get-value project

# 로컬 이미지에 Artifact Registry 태그 추가
docker tag ion-api:latest `
  us-central1-docker.pkg.dev/$PROJECT_ID/ion-api/ion-api:latest

# 버전 태그도 추가 (선택 사항)
docker tag ion-api:latest `
  us-central1-docker.pkg.dev/$PROJECT_ID/ion-api/ion-api:v1.0.0
```

### 2. 이미지 푸시

```powershell
# latest 태그 푸시
docker push us-central1-docker.pkg.dev/$PROJECT_ID/ion-api/ion-api:latest

# 버전 태그 푸시 (선택 사항)
docker push us-central1-docker.pkg.dev/$PROJECT_ID/ion-api/ion-api:v1.0.0
```

**예상 시간**: 2-5분 (네트워크 속도에 따라)

**예상 출력**:

```text
The push refers to repository [us-central1-docker.pkg.dev/your-project/ion-api/ion-api]
abc123def456: Pushed
...
latest: digest: sha256:... size: 2839
```

### 3. 이미지 확인

```powershell
# Artifact Registry 이미지 목록
gcloud artifacts docker images list `
  us-central1-docker.pkg.dev/$PROJECT_ID/ion-api
```

---

## ☁️ Cloud Run 배포

### 1. Service Account 생성 (권장)

```powershell
# Service Account 생성
gcloud iam service-accounts create ion-api-runner `
  --display-name="Ion API Cloud Run Service Account"

# Vertex AI 사용자 역할 부여
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:ion-api-runner@$PROJECT_ID.iam.gserviceaccount.com" `
  --role="roles/aiplatform.user"

# Secret Manager 접근 역할
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:ion-api-runner@$PROJECT_ID.iam.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
```

### 2. 첫 배포 (Development 모드)

먼저 Mock 클라이언트로 배포하여 기본 동작을 확인합니다:

```powershell
gcloud run deploy ion-api `
  --image us-central1-docker.pkg.dev/$PROJECT_ID/ion-api/ion-api:latest `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --set-env-vars="ENVIRONMENT=development,PORT=8080" `
  --memory=512Mi `
  --cpu=1 `
  --max-instances=10 `
  --service-account="ion-api-runner@$PROJECT_ID.iam.gserviceaccount.com"
```

**파라미터 설명**:

- `--allow-unauthenticated`: 공개 액세스 허용 (프로토타입용, 나중에 제한 가능)
- `--memory=512Mi`: 메모리 512MB 할당
- `--cpu=1`: 1 vCPU 할당
- `--max-instances=10`: 최대 10개 인스턴스 (비용 제어)

**예상 시간**: 2-3분 (첫 배포)

**예상 출력**:

```text
Deploying container to Cloud Run service [ion-api] in project [your-project] region [us-central1]
✓ Deploying... Done.
  ✓ Creating Revision...
  ✓ Routing traffic...
Done.
Service [ion-api] revision [ion-api-00001-xyz] has been deployed and is serving 100 percent of traffic.
Service URL: https://ion-api-abc123-uc.a.run.app
```

### 3. 배포 확인

```powershell
# 서비스 정보 확인
gcloud run services describe ion-api --region=us-central1

# 서비스 URL 가져오기
$SERVICE_URL = gcloud run services describe ion-api `
  --region=us-central1 `
  --format="value(status.url)"

Write-Host "Service URL: $SERVICE_URL"
```

---

## 🔐 Secret Manager 연동

프로덕션 환경에서는 Vertex AI 인증 정보를 Secret Manager로 관리합니다.

### 1. Secret 생성

```powershell
# 서비스 계정 키 파일이 있다면
gcloud secrets create vertex-ai-credentials `
  --data-file="path/to/your-service-account-key.json" `
  --replication-policy="automatic"

# 또는 Application Default Credentials 사용 (권장)
# Cloud Run의 Service Account가 직접 Vertex AI 호출
```

### 2. Secret 접근 권한 부여

```powershell
# Service Account에 Secret 읽기 권한
gcloud secrets add-iam-policy-binding vertex-ai-credentials `
  --member="serviceAccount:ion-api-runner@$PROJECT_ID.iam.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
```

### 3. Cloud Run에 Secret 마운트

```powershell
# Production 모드로 재배포 (Secret 포함)
gcloud run deploy ion-api `
  --image us-central1-docker.pkg.dev/$PROJECT_ID/ion-api/ion-api:latest `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --set-env-vars="ENVIRONMENT=production,PORT=8080,VERTEX_PROJECT_ID=$PROJECT_ID,VERTEX_LOCATION=us-central1,VERTEX_MODEL=gemini-1.5-flash-002" `
  --update-secrets="GOOGLE_APPLICATION_CREDENTIALS=vertex-ai-credentials:latest" `
  --memory=512Mi `
  --cpu=1 `
  --max-instances=10 `
  --service-account="ion-api-runner@$PROJECT_ID.iam.gserviceaccount.com"
```

**주의**: `--update-secrets`는 기존 배포를 업데이트할 때 사용합니다.

---

## ✅ 배포 검증

### 1. Health Check

```powershell
# Health endpoint 테스트
$SERVICE_URL = gcloud run services describe ion-api `
  --region=us-central1 `
  --format="value(status.url)"

Invoke-RestMethod -Uri "$SERVICE_URL/health"
```

**예상 응답**:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "pipeline_ready": true
}
```

### 2. Chat Endpoint 테스트

```powershell
# Development 모드 (Mock 클라이언트)
Invoke-RestMethod -Uri "$SERVICE_URL/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"message":"안녕하세요"}'
```

**예상 응답** (Development):

```json
{
  "content": "Mock response for development",
  "persona_used": "Elro",
  "resonance_key": "curious-burst-inquiry",
  "confidence": 0.8,
  "metadata": {
    "rhythm": {},
    "tone": {},
    "routing": {}
  }
}
```

**예상 응답** (Production with Vertex AI):

```json
{
  "content": "안녕하세요! 무엇을 도와드릴까요?",
  "persona_used": "Lua",
  "resonance_key": "warm-steady-presence",
  "confidence": 0.95,
  "metadata": {
    "rhythm": {
      "pace": "moderate",
      "avg_sentence_length": 8
    },
    "tone": {
      "primary": "friendly",
      "confidence": 0.9
    },
    "routing": {
      "secondary_persona": null
    }
  }
}
```

### 3. Swagger UI 확인

```powershell
# 브라우저에서 열기
Start-Process "$SERVICE_URL/docs"
```

### 4. 로그 확인

```powershell
# 최근 로그 확인
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ion-api" `
  --limit=50 `
  --format=json
```

또는 Cloud Console에서:

```text
https://console.cloud.google.com/run/detail/us-central1/ion-api/logs
```

---

## 🛠️ 문제 해결

### 문제 1: 배포 실패 - Permission Denied

**증상**:

```text
ERROR: (gcloud.run.deploy) PERMISSION_DENIED: Permission 'run.services.create' denied
```

**원인**: gcloud 사용자가 Cloud Run 권한이 없음

**해결**:

```powershell
# Cloud Run Admin 역할 부여
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="user:YOUR_EMAIL@gmail.com" `
  --role="roles/run.admin"
```

---

### 문제 2: 이미지 푸시 실패 - Authentication Required

**증상**:

```text
denied: Permission "artifactregistry.repositories.uploadArtifacts" denied
```

**원인**: Docker가 Artifact Registry에 인증되지 않음

**해결**:

```powershell
# Docker 인증 재설정
gcloud auth configure-docker us-central1-docker.pkg.dev

# 또는 gcloud auth 재로그인
gcloud auth login
```

---

### 문제 3: Cloud Run 서비스가 시작되지 않음

**증상**:

```text
ERROR: Revision 'ion-api-00001-xyz' is not ready and cannot serve traffic.
```

**원인**: 컨테이너가 health check 실패 또는 포트 바인딩 오류

**해결**:

```powershell
# 로그 확인
gcloud logging read "resource.type=cloud_run_revision" --limit=20

# 일반적인 원인:
# 1. PORT 환경 변수가 8080으로 설정되어 있는지 확인
# 2. Health check endpoint (/health)가 정상 응답하는지 확인
# 3. 컨테이너가 0.0.0.0:8080에 바인딩되는지 확인
```

---

### 문제 4: Vertex AI 호출 실패

**증상**:

```text
ERROR: Failed to call Vertex AI: Permission denied
```

**원인**: Service Account에 Vertex AI 권한 없음

**해결**:

```powershell
# Vertex AI User 역할 부여
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:ion-api-runner@$PROJECT_ID.iam.gserviceaccount.com" `
  --role="roles/aiplatform.user"

# 재배포 (Service Account 설정 확인)
gcloud run deploy ion-api --service-account="ion-api-runner@$PROJECT_ID.iam.gserviceaccount.com" ...
```

---

## 📊 배포 후 체크리스트

- [ ] Health endpoint 200 OK
- [ ] Chat endpoint 200 OK (Mock 또는 실제 응답)
- [ ] Swagger UI 접근 가능
- [ ] 로그에 에러 없음
- [ ] Service Account 권한 확인
- [ ] Secret Manager 연동 (Production 시)
- [ ] 메모리/CPU 사용량 모니터링
- [ ] 응답 시간 < 3초 (cold start 제외)

---

## 🎯 최종 목표 달성 기준

| 항목             | 목표               | 상태 |
| ---------------- | ------------------ | ---- |
| Cloud Run 배포   | 성공               | ⏳   |
| Public URL 접근  | 가능               | ⏳   |
| Health check     | 200 OK             | ⏳   |
| Chat endpoint    | 정상 응답          | ⏳   |
| Vertex AI 연동   | Production 모드    | ⏳   |
| Secret Manager   | 인증 정보 보호     | ⏳   |
| Service Account  | 최소 권한 부여     | ⏳   |
| 로그 및 모니터링 | Cloud Logging 확인 | ⏳   |

---

## 🚀 다음 단계: Day 4-5

### Day 4: Production Features

- Cloud Logging 구조화
- Cloud Monitoring 대시보드
- Rate Limiting 적용
- CORS 정책 제한
- Security Headers 추가

### Day 5: CI/CD Pipeline

- GitHub Actions 워크플로우
- 자동 빌드 및 배포
- 알림 설정
- 부하 테스트

---

## 📚 참고 자료

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Artifact Registry Guide](https://cloud.google.com/artifact-registry/docs)
- [Secret Manager Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)
- [Cloud Run Service Account](https://cloud.google.com/run/docs/securing/service-identity)
- [Vertex AI Authentication](https://cloud.google.com/vertex-ai/docs/authentication)

## 9. Deployment Results

### Actual Deployment Output

**Service Information:**

- Service Name: `ion-api`
- Revision: `ion-api-00001-txw`
- Service URL: `https://ion-api-64076350717.us-central1.run.app`
- Region: `us-central1`
- Project: `naeda-genesis`

**Deployment Configuration:**

- Image: `us-central1-docker.pkg.dev/naeda-genesis/ion-api/ion-api:latest`
- Memory: 512Mi
- CPU: 1
- Max Instances: 10
- Service Account: `ion-api-runner@naeda-genesis.iam.gserviceaccount.com`
- Environment: development (Mock Vertex AI)

### Validation Results

**Health Check:**

```powershell
PS> $SERVICE_URL = "https://ion-api-64076350717.us-central1.run.app"
PS> Invoke-RestMethod -Uri "$SERVICE_URL/health"

status  version pipeline_ready
------  ------- --------------
healthy 1.0.0             True
```

**Chat Endpoint:**

```powershell
PS> Invoke-RestMethod -Uri "$SERVICE_URL/chat" -Method POST -ContentType "application/json" -Body '{"message":"안녕하세요"}'

content       : Mock response for development
persona_used  : Elro
resonance_key : curious-burst-inquiry
confidence    : 0.8
metadata      : @{rhythm=; tone=; routing=}
```

**Cloud Run Logs:**

```text
TIMESTAMP                    SEVERITY  TEXT_PAYLOAD
2025-10-17T12:23:30.525263Z  INFO      169.254.169.126:17268 - "POST /chat HTTP/1.1" 200 OK
2025-10-17T12:23:30.524805Z            Response generated with persona: Elro
2025-10-17T12:23:30.524313Z            Received chat request: 안녕하세요
2025-10-17T12:23:20.113461Z  INFO      169.254.169.126:6620 - "GET /health HTTP/1.1" 200 OK
```

**Swagger UI:**
Access at: `https://ion-api-64076350717.us-central1.run.app/docs`

### Lessons Learned

1. **PORT Environment Variable**: Cloud Run automatically sets `PORT` environment variable, so don't include it in `--set-env-vars`. The container will receive `PORT=8080` automatically.

2. **Deployment Speed**: Total deployment time was approximately 30 seconds from image push to service ready.

3. **Mock Client**: Development environment successfully uses Mock Vertex AI client, allowing full API validation without GCP credentials.

4. **Service Account**: Properly configured IAM roles (`aiplatform.user`, `secretmanager.secretAccessor`) are essential for production mode with real Vertex AI.

5. **Logs**: Cloud Logging automatically captures all stdout/stderr from the container, making debugging straightforward.

---

**Day 3 Completion Criteria:**
✅ Cloud Run deployment successful  
✅ Public URL accessible: `https://ion-api-64076350717.us-central1.run.app`  
✅ API endpoints working (health + chat validated)  
✅ Development mode deployed with Mock Vertex AI  
✅ Logs captured and verified  
✅ Swagger UI accessible at `/docs`

**Production Deployment (Optional):**
For production mode with real Vertex AI, follow Section 6 to create Secret Manager secret and redeploy with `ENVIRONMENT=production`.

---

**다음 문서**: [DAY4_PRODUCTION_FEATURES.md](./DAY4_PRODUCTION_FEATURES.md) (예정)  
**이전 문서**: [DAY2_DOCKER_CONTAINERIZATION.md](./DAY2_DOCKER_CONTAINERIZATION.md)  
**Week 3 개요**: [WEEK3_KICKOFF.md](./WEEK3_KICKOFF.md)
