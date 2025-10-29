# CI/CD 파이프라인 설정 가이드

ION Mentoring 프로젝트의 GitHub Actions CI/CD 파이프라인 설정 및 운영 가이드입니다.

## 목차

1. [파이프라인 개요](#파이프라인-개요)
2. [사전 준비](#사전-준비)
3. [Secrets 설정](#secrets-설정)
4. [워크플로우 설명](#워크플로우-설명)
5. [배포 프로세스](#배포-프로세스)
6. [모니터링 & 롤백](#모니터링--롤백)
7. [문제 해결](#문제-해결)

---

## 파이프라인 개요

### 전체 흐름

```
Pull Request 또는 Push
    ↓
┌───────────────────────────────────────┐
│  Tests & Code Quality                 │
│  • Lint (Ruff)                        │
│  • Format Check (Black)               │
│  • Type Check (MyPy)                  │
│  • Unit/Integration Tests             │
│  • Coverage Report                    │
└───────────────────────────────────────┘
    ↓ (main 브랜치만 계속)
┌───────────────────────────────────────┐
│  Build Docker Image                   │
│  • Docker 빌드 & 최적화              │
│  • GCR에 푸시                        │
│  • 이미지 태그 생성                   │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│  Deploy to Staging                    │
│  • Cloud Run 배포                    │
│  • Smoke Tests 실행                  │
│  • PR 댓글 작성                      │
└───────────────────────────────────────┘
    ↓ (수동 트리거)
┌───────────────────────────────────────┐
│  Deploy to Production                 │
│  • 신규 리비전 배포 (no traffic)    │
│  • Smoke Tests 실행                  │
│  • 수동 승인 필요                    │
└───────────────────────────────────────┘
    ↓
├─> GitHub Release 생성
└─> Slack 알림 전송
```

### 워크플로우 목록

| 파일 | 트리거 | 목적 |
|------|--------|------|
| **test.yml** | PR, Push (모든 브랜치) | 테스트 & 품질 검사 |
| **build-deploy.yml** | Push (main), 수동 트리거 | 빌드 & 배포 |

---

## 사전 준비

### 1. GitHub Repository 설정

```bash
# 저장소 클론
git clone https://github.com/YOUR_ORG/ion-mentoring.git
cd ion-mentoring

# 브랜치 보호 설정 (Settings → Branches)
# - main 브랜치 보호
# - PR 필요
# - 상태 체크 필요 (test.yml)
```

### 2. Google Cloud 설정

#### Workload Identity 연동

```bash
# GCP 프로젝트 설정
export PROJECT_ID="your-gcp-project"
export GITHUB_REPO="YOUR_ORG/ion-mentoring"

# 1. 서비스 계정 생성
gcloud iam service-accounts create github-ci \
  --project=$PROJECT_ID \
  --display-name="GitHub CI/CD"

# 2. 필요한 권한 부여
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-ci@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# 3. Workload Identity Provider 생성
gcloud iam workload-identity-pools create "github" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc "github" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github" \
  --display-name="GitHub" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.aud=assertion.aud" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 4. 저장소-서비스계정 연결
WORKLOAD_IDENTITY_PROVIDER=$(gcloud iam workload-identity-pools providers \
  --workload-identity-pool=github \
  --project=$PROJECT_ID \
  describe github \
  --format="value(name)")

gcloud iam service-accounts add-iam-policy-binding \
  github-ci@${PROJECT_ID}.iam.gserviceaccount.com \
  --project=$PROJECT_ID \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github/attribute.repository/${GITHUB_REPO}"
```

---

## Secrets 설정

### GitHub Secrets 추가

Settings → Secrets and variables → Actions 에서 다음을 추가하세요:

```bash
# GCP 설정
GCP_PROJECT_ID              # 예: ion-mentoring-prod
WIF_PROVIDER               # Workload Identity Provider 경로
WIF_SERVICE_ACCOUNT        # github-ci@{PROJECT_ID}.iam.gserviceaccount.com

# Slack 알림 (선택)
SLACK_WEBHOOK              # Slack Webhook URL
```

### 환경별 Secrets (선택)

```bash
# Production environment secrets
Settings → Environments → production

PRODUCTION_GCP_PROJECT_ID
PRODUCTION_SLACK_WEBHOOK
```

---

## 워크플로우 설명

### 1. Test Workflow (test.yml)

**트리거**:
- PR 생성/업데이트 (모든 브랜치)
- main/develop에 Push

**실행 내용**:
1. Python 3.11, 3.12, 3.13 다중 버전 테스트
2. Ruff 린팅
3. Black 포맷 검사
4. MyPy 타입 체크
5. pytest 실행 (커버리지 포함)
6. Codecov 업로드

**예상 시간**: 5-10분

```yaml
# 수동 실행 (필요시)
# Settings → Actions → Tests & Code Quality → Run workflow
```

### 2. Build & Deploy Workflow (build-deploy.yml)

**트리거**:
- main에 Push (자동)
- 수동 트리거 (수동)

**스테이징 배포**:
1. Docker 이미지 빌드 (최적화됨)
2. GCR에 푸시
3. Cloud Run에 배포 (no-traffic)
4. Smoke 테스트 실행
5. PR에 댓글 작성

**프로덕션 배포**:
- 수동 트리거로만 가능
- Staging과 동일 but no-traffic
- 수동 승인 후 트래픽 전환

**예상 시간**: 10-15분

---

## 배포 프로세스

### 1. 자동 스테이징 배포

```bash
# main에 커밋 & 푸시
git add .
git commit -m "feat: add new feature"
git push origin main

# GitHub Actions에서 자동으로:
# 1. 테스트 실행
# 2. 이미지 빌드
# 3. 스테이징에 배포
# 4. Smoke 테스트 실행
```

### 2. 수동 프로덕션 배포

```bash
# GitHub UI에서:
# 1. Actions → Build & Deploy to Cloud Run
# 2. Run workflow 클릭
# 3. environment 선택: production
# 4. Run workflow 클릭

# 또는 CLI에서:
gh workflow run build-deploy.yml -f environment=production
```

### 3. 프로덕션 트래픽 전환

```bash
# Smoke 테스트 통과 후, 수동으로 트래픽 전환:

gcloud run services update-traffic ion-api-prod \
  --to-revisions LATEST=100 \
  --region us-central1

# 또는 카나리 배포 (10% 트래픽):
gcloud run services update-traffic ion-api-prod \
  --to-revisions LATEST=10 \
  --region us-central1
```

---

## 모니터링 & 롤백

### 배포 상태 모니터링

```bash
# 최근 배포 확인
gcloud run revisions list \
  --service=ion-api-prod \
  --region=us-central1 \
  --limit=5

# 트래픽 분포 확인
gcloud run services describe ion-api-prod \
  --region=us-central1 \
  --format='value(status.traffic)'

# 로그 확인
gcloud run services logs read ion-api-prod \
  --region=us-central1 \
  --limit=50
```

### 롤백 프로세스

```bash
# 1. 이전 리비전 확인
gcloud run revisions list \
  --service=ion-api-prod \
  --region=us-central1

# 2. 이전 버전으로 롤백
gcloud run services update-traffic ion-api-prod \
  --to-revisions PREVIOUS=100 \
  --region=us-central1

# 3. 로그 확인
gcloud run services logs read ion-api-prod \
  --region=us-central1
  --limit=100
```

### 자동 롤백 조건

배포 후 다음 조건 시 자동 롤백 고려:

- ❌ 에러율 > 5% (5분 이상)
- ❌ 응답 시간 > 10s (P99)
- ❌ 메모리 사용량 > 90%
- ❌ 헬스 체크 실패

---

## 문제 해결

### 1. 테스트 실패

```bash
# 로컬에서 재현
pytest tests/ -v

# 린팅 확인
ruff check .

# 포맷 검사
black --check .

# 타입 체크
mypy app --ignore-missing-imports
```

### 2. 빌드 실패

```bash
# 로컬 빌드 테스트
docker build -t ion-mentoring:test .

# 이미지 실행
docker run -p 8080:8080 ion-mentoring:test

# 헬스 체크
curl http://localhost:8080/health
```

### 3. 배포 실패

```bash
# GCP 인증 확인
gcloud auth list

# 서비스 계정 권한 확인
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:github-ci*"

# Cloud Run 배포 로그
gcloud run deploy --help
```

### 4. Secrets 문제

```bash
# Secrets 확인 (GitHub UI)
# Settings → Secrets and variables → Actions

# 워크플로우에서 Secrets 사용 확인
grep -r "\${{ secrets." .github/workflows/
```

---

## 최적화 팁

### 1. 빌드 시간 단축

```yaml
# Docker 멀티스테이지 빌드 활용 (이미 Dockerfile에 구현됨)
# 캐시 활용 (actions/setup-python에 cache: 'pip')
# 병렬 테스트 실행
pytest tests/ -n auto
```

### 2. 비용 절감

```bash
# Cloud Run 비용 최적화
# - 최소 인스턴스 조정
# - 메모리 크기 최적화
# - 타임아웃 설정

# 저장소 정리
# - 오래된 이미지 삭제
# - 태그 정책 수립
```

### 3. 보안 강화

```bash
# Secrets 로테이션
# - 주기적 갱신
# - 접근 권한 최소화

# 이미지 스캔
# - 취약점 스캔 활성화
# - 부정신뢰할 수 없는 이미지 차단
```

---

## 배포 체크리스트

### 매 배포 전

- [ ] 모든 테스트 통과
- [ ] 코드 리뷰 완료
- [ ] 의존성 업데이트 확인
- [ ] 환경 변수 검증
- [ ] CHANGELOG 업데이트

### 배포 중

- [ ] GitHub Actions 성공
- [ ] Smoke 테스트 통과
- [ ] 로그 모니터링 시작
- [ ] 슬랙 알림 확인

### 배포 후

- [ ] 프로덕션 헬스 체크
- [ ] 에러율 정상 (< 0.5%)
- [ ] 응답 시간 정상 (< 2s)
- [ ] 사용자 피드백 수집

---

## 참고 문서

- [GitHub Actions 공식 문서](https://docs.github.com/en/actions)
- [Google Cloud Run CI/CD](https://cloud.google.com/run/docs/continuous-deployment-with-cloud-build)
- [Docker 최적화](https://docs.docker.com/develop/dev-best-practices/)
- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)

---

**문제가 있나요?** [문제 해결 섹션](#문제-해결)을 참고하거나 팀에 문의하세요.
