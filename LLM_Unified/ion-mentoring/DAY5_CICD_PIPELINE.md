# Week 3 Day 5: CI/CD Pipeline

## 개요

GitHub Actions를 사용한 자동 배포 파이프라인을 구현했습니다. `master` 브랜치에 코드를 푸시하면 자동으로 테스트, 빌드, 배포가 진행됩니다.

## 1. GitHub Actions Workflow

### Workflow 파일

`.github/workflows/deploy.yml` 파일을 생성했습니다.

### Workflow 단계

1. **Checkout code**: 저장소 코드 가져오기
2. **Set up Python 3.13**: Python 환경 설정 (pip 캐시 활성화)
3. **Install dependencies**: requirements-api.txt + pytest 설치
4. **Run tests**: 67개 테스트 실행 (실패 시 배포 중단)
5. **Authenticate to Google Cloud**: GCP 서비스 계정 인증
6. **Set up Cloud SDK**: gcloud CLI 설정
7. **Configure Docker**: Artifact Registry 인증
8. **Build Docker image**: 이미지 빌드 및 태그 (commit SHA + latest)
9. **Push Docker image**: Artifact Registry에 푸시
10. **Deploy to Cloud Run**: Cloud Run에 배포
11. **Test deployment**: 배포된 서비스 헬스 체크

### Trigger 조건

```yaml
on:
  push:
    branches:
      - master
    paths:
      - "ion-mentoring/**"
      - ".github/workflows/deploy.yml"
```

- `master` 브랜치에 푸시할 때만 실행
- `ion-mentoring/` 디렉토리 또는 워크플로우 파일 변경 시에만 실행

## 2. GitHub Secrets 설정

워크플로우가 작동하려면 다음 GitHub Secrets를 설정해야 합니다:

### Required Secrets

1. **GCP_PROJECT_ID**: Google Cloud 프로젝트 ID

   ```
   naeda-genesis
   ```

2. **GCP_SA_KEY**: Google Cloud 서비스 계정 키 (JSON)

### 서비스 계정 생성 방법

#### Step 1: 서비스 계정 생성

```bash
# 서비스 계정 생성
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deployment" \
  --project=naeda-genesis

# 서비스 계정 이메일 확인
SA_EMAIL=$(gcloud iam service-accounts list \
  --filter="displayName:GitHub Actions Deployment" \
  --format='value(email)')

echo $SA_EMAIL
# 출력: github-actions@naeda-genesis.iam.gserviceaccount.com
```

#### Step 2: 필요한 권한 부여

```bash
# Artifact Registry 쓰기 권한
gcloud projects add-iam-policy-binding naeda-genesis \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/artifactregistry.writer"

# Cloud Run 관리자 권한
gcloud projects add-iam-policy-binding naeda-genesis \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/run.admin"

# Service Account 사용자 권한 (Cloud Run이 다른 SA로 실행되도록)
gcloud projects add-iam-policy-binding naeda-genesis \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/iam.serviceAccountUser"
```

#### Step 3: 키 파일 생성

```bash
# 키 파일 생성 (JSON)
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=$SA_EMAIL

# 키 파일 내용 확인 (GitHub Secret에 복사할 내용)
cat github-actions-key.json
```

#### Step 4: GitHub Secrets 등록

1. GitHub 저장소 페이지로 이동
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** 클릭
4. Secret 추가:
   - **Name**: `GCP_PROJECT_ID`
   - **Value**: `naeda-genesis`
5. **Add secret** 클릭
6. 다시 **New repository secret** 클릭
7. Secret 추가:
   - **Name**: `GCP_SA_KEY`
   - **Value**: `github-actions-key.json` 파일의 전체 내용 (JSON)
8. **Add secret** 클릭

#### Step 5: 키 파일 보안 삭제

```bash
# 로컬 키 파일 삭제 (GitHub에 업로드 완료 후)
rm github-actions-key.json
```

## 3. Workflow 테스트

### 테스트 방법 1: 더미 커밋으로 트리거

```bash
# ion-mentoring 디렉토리로 이동
cd D:\nas_backup\LLM_Unified\ion-mentoring

# 더미 파일 생성 (워크플로우 트리거용)
echo "# GitHub Actions Test" > TEST_WORKFLOW.md

# Git 커밋
git add TEST_WORKFLOW.md
git commit -m "test: Trigger GitHub Actions workflow"
git push origin master
```

### 테스트 방법 2: 실제 코드 변경

```bash
# app/main.py의 version을 변경
# version="1.0.0" → version="1.0.1"

git add app/main.py
git commit -m "chore: Bump version to 1.0.1"
git push origin master
```

### Workflow 실행 확인

1. GitHub 저장소 페이지로 이동
2. **Actions** 탭 클릭
3. 최신 워크플로우 실행 확인
4. 각 단계별 로그 확인:
   - ✅ Run tests (67 passed)
   - ✅ Build Docker image
   - ✅ Push Docker image
   - ✅ Deploy to Cloud Run
   - ✅ Test deployment

### 예상 실행 시간

- **Run tests**: ~10-20초
- **Build Docker image**:
  - 첫 빌드: ~2-3분 (모든 레이어 빌드)
  - 이후 빌드: ~30-60초 (캐시 활용)
- **Push Docker image**: ~30-60초 (레이어 재사용)
- **Deploy to Cloud Run**: ~30-60초
- **Test deployment**: ~5-10초
- **총 소요 시간**: 첫 실행 ~5분, 이후 ~2-3분

## 4. Cloud Run 자동 배포 확인

### 배포된 서비스 확인

```bash
# 서비스 리스트
gcloud run services list --region us-central1

# 최신 revision 확인
gcloud run revisions list --service ion-api --region us-central1 --limit 5

# 서비스 URL 확인
gcloud run services describe ion-api --region us-central1 --format 'value(status.url)'
```

### 예상 출력

```
SERVICE   REGION        URL                                              LAST DEPLOYED BY            LAST DEPLOYED AT
ion-api   us-central1   https://ion-api-64076350717.us-central1.run.app  github-actions@...          2025-10-17
```

### 배포 검증

```powershell
# 서비스 URL 설정
$SERVICE_URL = "https://ion-api-64076350717.us-central1.run.app"

# Health check
Invoke-RestMethod -Uri "$SERVICE_URL/health" | Format-Table

# Chat 테스트
$body = @{
    message = "GitHub Actions 자동 배포 테스트"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$SERVICE_URL/chat" -Method POST -Body $body -ContentType "application/json"
```

## 5. Troubleshooting

### 테스트 실패 시

```bash
# 로컬에서 먼저 테스트 실행
cd D:\nas_backup\LLM_Unified\ion-mentoring
python -m pytest -v

# 67/67 테스트 통과 확인 후 푸시
```

### Docker 빌드 실패 시

```bash
# 로컬에서 Docker 빌드 테스트
docker build -t ion-api:test .

# 빌드 성공 확인 후 푸시
```

### Cloud Run 배포 실패 시

```bash
# 서비스 계정 권한 확인
gcloud projects get-iam-policy naeda-genesis \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:github-actions@*"

# 필요한 역할 확인:
# - roles/artifactregistry.writer
# - roles/run.admin
# - roles/iam.serviceAccountUser
```

### GitHub Actions 로그 확인

1. GitHub Actions 탭에서 실패한 워크플로우 클릭
2. 실패한 단계 클릭하여 상세 로그 확인
3. 오류 메시지 복사하여 디버깅

## 6. 다음 단계

- [ ] Cloud Monitoring 대시보드 생성
- [ ] 부하 테스트 (locust 또는 hey)
- [ ] Week 3 Summary 문서 작성

## 참고 자료

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Google Cloud GitHub Actions](https://github.com/google-github-actions)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
