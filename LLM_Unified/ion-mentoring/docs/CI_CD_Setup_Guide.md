# GitHub Actions CI/CD 설정 가이드

## 📋 개요

이 문서는 ION API의 GitHub Actions CI/CD 파이프라인 설정 방법을 설명합니다.

## 🔐 1단계: Workload Identity Federation 설정

### 1.1 Workload Identity Pool 생성

```bash
# GCP 프로젝트 설정
export PROJECT_ID="naeda-genesis"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export POOL_NAME="github-actions-pool"
export PROVIDER_NAME="github-actions-provider"
export SERVICE_ACCOUNT_NAME="github-actions-sa"
export REPO_FULL_NAME="Ruafieldphase/LLM_Unified"

# Workload Identity Pool 생성
gcloud iam workload-identity-pools create $POOL_NAME \
  --project=$PROJECT_ID \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Workload Identity Provider 생성
gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool=$POOL_NAME \
  --display-name="GitHub Actions Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository_owner=='Ruafieldphase'" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### 1.2 Service Account 생성 및 권한 부여

```bash
# Service Account 생성
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
  --display-name="GitHub Actions Service Account" \
  --project=$PROJECT_ID

# Cloud Run 배포 권한 부여
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Storage 권한 (Docker 이미지 푸시)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Service Account User 권한 (Cloud Run에 필요)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Workload Identity 바인딩
gcloud iam service-accounts add-iam-policy-binding \
  "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${REPO_FULL_NAME}"
```

### 1.3 Workload Identity Provider 정보 출력

```bash
# Provider의 전체 이름 출력 (GitHub Secrets에 추가할 값)
gcloud iam workload-identity-pools providers describe $PROVIDER_NAME \
  --project=$PROJECT_ID \
  --location="global" \
  --workload-identity-pool=$POOL_NAME \
  --format="value(name)"

# 결과 예시:
# projects/123456789/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider
```

## 🔑 2단계: GitHub Secrets 설정

GitHub 저장소의 Settings → Secrets and variables → Actions에서 다음 secrets를 추가:

### 필수 Secrets

| Secret 이름 | 값 | 설명 |
|------------|-----|------|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/[PROJECT_NUMBER]/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider` | 위에서 출력한 Provider 전체 이름 |
| `GCP_SERVICE_ACCOUNT` | `github-actions-sa@naeda-genesis.iam.gserviceaccount.com` | Service Account 이메일 |
| `VERTEX_AI_PROJECT_ID` | `naeda-genesis` | GCP 프로젝트 ID |

### 선택적 Secrets (Secret Manager 사용 시)

```bash
# Vertex AI 인증 정보를 Secret Manager에 저장
gcloud secrets create VERTEX_AI_PROJECT_ID \
  --data-file=<(echo -n "naeda-genesis") \
  --project=$PROJECT_ID

# Service Account에 Secret 접근 권한 부여
gcloud secrets add-iam-policy-binding VERTEX_AI_PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

# Google Application Credentials JSON 저장 (필요한 경우)
gcloud secrets create GOOGLE_APPLICATION_CREDENTIALS_JSON \
  --data-file=/path/to/service-account-key.json \
  --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding GOOGLE_APPLICATION_CREDENTIALS_JSON \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

## 🚀 3단계: 워크플로우 테스트

### 3.1 Staging 배포 (자동)

`develop` 브랜치에 push하면 자동으로 staging 환경에 배포됩니다:

```bash
git checkout develop
git merge main
git push origin develop
```

### 3.2 Production 배포 (자동)

`main` 브랜치에 push하면 자동으로 production 환경에 배포됩니다:

```bash
git checkout main
git merge develop
git push origin main
```

### 3.3 수동 배포 (Manual Trigger)

GitHub Actions 탭에서 "Deploy ION API to Cloud Run" 워크플로우를 선택하고 "Run workflow" 버튼 클릭:

1. Branch 선택 (main 또는 develop)
2. Environment 선택 (staging 또는 production)
3. "Run workflow" 클릭

## 📊 4단계: 모니터링

### 4.1 배포 상태 확인

- GitHub Actions 탭에서 워크플로우 실행 상태 확인
- Summary 섹션에서 배포 정보 확인 (Service URL, Image Tag 등)

### 4.2 Health Check

배포 후 자동으로 health check가 실행되지만, 수동으로도 확인 가능:

```bash
# Staging
curl https://ion-api-staging-[PROJECT_NUMBER].us-central1.run.app/health

# Production
curl https://ion-api-[PROJECT_NUMBER].us-central1.run.app/health
```

### 4.3 Cloud Run 로그 확인

```bash
# Staging 로그
gcloud run services logs read ion-api-staging \
  --region=us-central1 \
  --limit=50

# Production 로그
gcloud run services logs read ion-api \
  --region=us-central1 \
  --limit=50
```

## 🔄 5단계: 롤백 절차

### 5.1 이전 버전으로 롤백

```bash
# 이전 리비전 목록 확인
gcloud run revisions list \
  --service=ion-api \
  --region=us-central1

# 특정 리비전으로 롤백
gcloud run services update-traffic ion-api \
  --region=us-central1 \
  --to-revisions=[REVISION_NAME]=100
```

### 5.2 워크플로우 재실행

GitHub Actions 탭에서 실패한 워크플로우의 "Re-run all jobs" 클릭

## 📝 워크플로우 상세 설명

### Jobs 구조

```
test → build-and-deploy → notify
```

### 1. Test Job

- Python 3.13 환경 설정
- 의존성 설치
- pytest 실행 (coverage 포함)
- 코드 커버리지 리포트 업로드 (Codecov)

### 2. Build and Deploy Job

- GCP 인증 (Workload Identity Federation)
- Docker 이미지 빌드 (GitHub SHA 태그)
- GCR에 이미지 푸시
- Cloud Run에 배포 (staging 또는 production)
- Health check 실행
- Smoke tests 실행
- 배포 summary 생성

### 3. Notify Job

- 배포 성공/실패 알림 (향후 Slack/Discord 통합 가능)

## 🎯 환경별 설정 차이

| 설정 | Staging | Production |
|------|---------|------------|
| Service Name | `ion-api-staging` | `ion-api` |
| Min Instances | 0 | 1 |
| Max Instances | 10 | 50 |
| Memory | 512Mi | 1Gi |
| CPU | 1 | 2 |
| Canary % | 10% | 5% |

## 🐛 트러블슈팅

### 문제 1: Workload Identity 인증 실패

**증상**: `Error: google-github-actions/auth failed with: retry function failed after 3 attempts`

**해결**:
1. Workload Identity Pool/Provider가 올바르게 생성되었는지 확인
2. Service Account 바인딩이 정확한지 확인
3. GitHub Secret 값이 정확한지 확인

```bash
# 바인딩 확인
gcloud iam service-accounts get-iam-policy \
  github-actions-sa@naeda-genesis.iam.gserviceaccount.com
```

### 문제 2: Docker 이미지 푸시 실패

**증상**: `Error: failed to push image to gcr.io`

**해결**:
1. Service Account에 `roles/storage.admin` 권한이 있는지 확인
2. GCR API가 활성화되어 있는지 확인

```bash
gcloud services enable containerregistry.googleapis.com
```

### 문제 3: Cloud Run 배포 실패

**증상**: `Error: failed to deploy service`

**해결**:
1. Service Account에 `roles/run.admin` 권한이 있는지 확인
2. Secret Manager에 secrets가 올바르게 저장되어 있는지 확인

```bash
# Secrets 목록 확인
gcloud secrets list --project=naeda-genesis

# Secret 값 확인
gcloud secrets versions access latest --secret=VERTEX_AI_PROJECT_ID
```

## 🔒 보안 Best Practices

1. **Workload Identity 사용**: Service Account Key JSON 대신 Workload Identity Federation 사용
2. **Least Privilege**: 필요한 최소한의 권한만 부여
3. **Secret Manager**: 민감한 정보는 Secret Manager에 저장
4. **환경 분리**: Staging과 Production 환경 분리
5. **코드 리뷰**: main 브랜치로의 직접 push 금지, PR 필수

## 📚 참고 자료

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GCR Documentation](https://cloud.google.com/container-registry/docs)

## ✅ 설정 완료 체크리스트

- [ ] Workload Identity Pool 생성
- [ ] Workload Identity Provider 생성
- [ ] Service Account 생성 및 권한 부여
- [ ] GitHub Secrets 추가
- [ ] Secret Manager에 secrets 저장 (선택)
- [ ] 워크플로우 파일 추가 (`.github/workflows/deploy-ion-api.yml`)
- [ ] Staging 배포 테스트
- [ ] Production 배포 테스트
- [ ] Health check 확인
- [ ] 롤백 절차 테스트

---

**작성일**: 2025-10-22  
**버전**: 1.0.0  
**작성자**: 깃코 (GitHub Copilot)
