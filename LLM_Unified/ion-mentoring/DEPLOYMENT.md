# ION Mentoring 배포 가이드

ION Mentoring 프로젝트를 개발/스테이징/프로덕션 환경에 배포하는 완전한 가이드입니다.

## 목차

1. [배포 아키텍처](#배포-아키텍처)
2. [사전 요구사항](#사전-요구사항)
3. [로컬 개발 환경](#로컬-개발-환경)
4. [Docker 빌드 및 실행](#docker-빌드-및-실행)
5. [Google Cloud Run 배포](#google-cloud-run-배포)
6. [Kubernetes 배포](#kubernetes-배포)
7. [CI/CD 파이프라인](#cicd-파이프라인)
8. [모니터링 & 로깅](#모니터링--로깅)
9. [문제 해결](#문제-해결)
10. [체크리스트](#배포-체크리스트)

---

## 배포 아키텍처

### 다층 배포 구조

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
└────────────┬────────────────────────────────────────────┘
             │
      ┌──────┴──────────┐
      │                 │
┌─────v─────┐     ┌─────v─────┐
│ Cloud Run │     │Kubernetes │
│ Instance 1│     │  Cluster  │
│(Auto-scale)│   │(Manual scale)│
└───────────┘     └───────────┘
      │                 │
      └──────┬──────────┘
             │
      ┌──────v──────────┐
      │  Cloud SQL DB   │
      │  Redis Cache    │
      │  Cloud Storage  │
      └─────────────────┘
```

### 환경별 배포 옵션

| 환경 | 플랫폼 | 스케일 | 모니터링 | 비용 |
|------|--------|--------|----------|------|
| **개발** | 로컬 / Docker | 1 | 기본 로깅 | $0 |
| **테스트** | Cloud Run | 1-2 | 로깅 + 메트릭 | $5-10 |
| **스테이징** | Cloud Run | 2-5 | 전체 모니터링 | $20-50 |
| **프로덕션** | K8s + Cloud Run | 5-20 | 전체 + Alert | $100+ |

---

## 사전 요구사항

### 1. 로컬 설정

```bash
# Python 3.11+
python --version

# pip / virtualenv
pip install --upgrade pip
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Google Cloud 설정

```bash
# GCP CLI 설치
curl https://sdk.cloud.google.com | bash

# 초기화
gcloud init
gcloud auth login

# 기본 프로젝트 설정
gcloud config set project YOUR_PROJECT_ID

# 필요한 서비스 활성화
gcloud services enable \
  run.googleapis.com \
  cloudkms.googleapis.com \
  container.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

### 3. Docker 설치

```bash
# macOS
brew install docker

# Linux
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Windows
# Docker Desktop 설치: https://www.docker.com/products/docker-desktop
```

### 4. 의존성 설치

```bash
pip install -r requirements-lock.txt
pip install -e ".[dev,test]"
```

---

## 로컬 개발 환경

### 1. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 편집
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true
RELOAD=true
BACKEND_TYPE=mock
```

### 2. 개발 서버 실행

```bash
# 방법 1: FastAPI 직접 실행
python -m app.main

# 방법 2: uvicorn 사용
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 방법 3: Docker Compose (권장)
docker-compose up -f docker-compose.dev.yml
```

### 3. 로컬 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# API 문서
open http://localhost:8000/docs

# 채팅 테스트
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요!"}'
```

---

## Docker 빌드 및 실행

### 1. 이미지 빌드

```bash
# 기본 빌드
docker build -t ion-mentoring:latest .

# 특정 버전 태그
docker build -t ion-mentoring:v0.1.0 .

# 빌드 시 인자 전달
docker build \
  --build-arg PYTHON_VERSION=3.13 \
  -t ion-mentoring:latest .
```

### 2. 이미지 실행

```bash
# 기본 실행
docker run -d \
  -p 8080:8080 \
  -e ENVIRONMENT=production \
  -e GCP_PROJECT_ID=your-project \
  --name ion-api \
  ion-mentoring:latest

# 환경 파일 사용
docker run -d \
  -p 8080:8080 \
  --env-file .env.production \
  --name ion-api \
  ion-mentoring:latest

# 로그 확인
docker logs -f ion-api

# 컨테이너 중지
docker stop ion-api
docker rm ion-api
```

### 3. Docker Compose

```bash
# docker-compose.yml 생성
version: '3.9'
services:
  ion-api:
    build: .
    ports:
      - "8080:8080"
    environment:
      ENVIRONMENT: production
      GCP_PROJECT_ID: ${GCP_PROJECT_ID}
      REDIS_HOST: redis
      POSTGRES_HOST: postgres
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ion_mentoring
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"

# 실행
docker-compose up -d

# 종료
docker-compose down
```

---

## Google Cloud Run 배포

### 1. 이미지 레지스트리에 푸시

```bash
# Artifact Registry에 푸시
docker tag ion-mentoring:latest \
  gcr.io/${PROJECT_ID}/ion-mentoring:latest

docker push gcr.io/${PROJECT_ID}/ion-mentoring:latest
```

### 2. Cloud Run 배포

```bash
# 기본 배포
gcloud run deploy ion-api \
  --image gcr.io/${PROJECT_ID}/ion-mentoring:latest \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --allow-unauthenticated

# 상세 설정
gcloud run deploy ion-api \
  --image gcr.io/${PROJECT_ID}/ion-mentoring:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 100 \
  --timeout 600 \
  --max-instances 100 \
  --min-instances 1 \
  --set-env-vars "ENVIRONMENT=production,LOG_LEVEL=INFO" \
  --set-secrets "GCP_PROJECT_ID=gcp-project-id:latest" \
  --allow-unauthenticated

# 배포 확인
gcloud run services list
gcloud run services describe ion-api --region us-central1
```

### 3. 트래픽 관리

```bash
# 새 버전 배포 (기존 트래픽 유지)
gcloud run deploy ion-api \
  --image gcr.io/${PROJECT_ID}/ion-mentoring:v0.2.0 \
  --platform managed \
  --region us-central1 \
  --no-traffic

# 트래픽 분할 (카나리 배포)
gcloud run services update-traffic ion-api \
  --to-revisions LATEST=10,prev-version=90 \
  --region us-central1

# 전체 트래픽 전환
gcloud run services update-traffic ion-api \
  --to-revisions LATEST=100 \
  --region us-central1
```

---

## Kubernetes 배포

### 1. Deployment 생성

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ion-api
  namespace: default
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: ion-api
  template:
    metadata:
      labels:
        app: ion-api
    spec:
      containers:
      - name: ion-api
        image: gcr.io/PROJECT_ID/ion-mentoring:latest
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: GCP_PROJECT_ID
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: gcp_project_id
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: db_password
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 2. Service 생성

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ion-api-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: ion-api
```

### 3. 배포 실행

```bash
# ConfigMap 생성
kubectl create configmap app-config \
  --from-literal=gcp_project_id=your-project-id

# Secret 생성
kubectl create secret generic app-secrets \
  --from-literal=db_password='secure-password'

# 배포
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 상태 확인
kubectl get deployments
kubectl get pods
kubectl get services

# 로그 확인
kubectl logs -f deployment/ion-api

# 스케일링
kubectl scale deployment ion-api --replicas=5

# 롤백
kubectl rollout undo deployment/ion-api
```

---

## CI/CD 파이프라인

### GitHub Actions 설정

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements-lock.txt
        pip install -e ".[dev,test]"

    - name: Run tests
      run: pytest tests/ --cov=app

    - name: Setup Cloud SDK
      uses: google-github-actions/setup-gcloud@v0
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}

    - name: Build Docker image
      run: |
        docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/ion-mentoring:latest .

    - name: Push to Artifact Registry
      run: |
        docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/ion-mentoring:latest

    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy ion-api \
          --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/ion-mentoring:latest \
          --platform managed \
          --region us-central1 \
          --allow-unauthenticated
```

---

## 모니터링 & 로깅

### Cloud Monitoring 설정

```bash
# 메트릭 확인
gcloud monitoring metrics-descriptors list

# 대시보드 생성
gcloud monitoring dashboards create --config-from-file=dashboard.json
```

### 알림 설정

```bash
# 에러율 알림
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 1%"
```

---

## 문제 해결

### 배포 실패

```bash
# 로그 확인
gcloud run services describe ion-api --region us-central1

# 배포 재시도
gcloud run deploy ion-api --no-traffic  # 먼저 트래픽 없이 배포
gcloud run services update-traffic ion-api --to-revisions LATEST=100

# 이전 버전으로 롤백
gcloud run services update-traffic ion-api --to-revisions PREVIOUS=100
```

### 성능 문제

```bash
# 메모리 사용량 확인
gcloud run services describe ion-api --format="value(spec.template.spec.containers[0].resources.limits.memory)"

# 메모리 증가
gcloud run deploy ion-api --memory 2Gi
```

### 네트워크 문제

```bash
# VPC Connector 설정
gcloud run deploy ion-api \
  --vpc-connector=projects/PROJECT_ID/locations/REGION/connectors/CONNECTOR_NAME
```

---

## 배포 체크리스트

### 사전 배포

- [ ] 모든 테스트 통과 (커버리지 > 85%)
- [ ] 코드 리뷰 완료
- [ ] 의존성 업데이트 확인
- [ ] 환경 변수 설정 완료
- [ ] Secret 관리 설정 완료
- [ ] 백업 및 복구 계획 수립

### 배포 중

- [ ] 스테이징 환경 배포 성공
- [ ] 헬스 체크 통과
- [ ] API 엔드포인트 접근 가능
- [ ] 모니터링 시작
- [ ] 초기 부하 테스트

### 배포 후

- [ ] 프로덕션 헬스 체크 확인
- [ ] 로그 모니터링 시작
- [ ] 메트릭 수집 확인
- [ ] 에러율 정상 (< 0.5%)
- [ ] 응답 시간 정상 (P99 < 5s)
- [ ] 사용자 피드백 수집

### 롤백 계획

- [ ] 롤백 조건 명확화
- [ ] 롤백 테스트 완료
- [ ] 롤백 스크립트 준비
- [ ] 팀 알림 방법 정의

---

## 참고 문서

- [Google Cloud Run 공식 문서](https://cloud.google.com/run/docs)
- [Docker 공식 문서](https://docs.docker.com/)
- [Kubernetes 공식 문서](https://kubernetes.io/docs/)
- [GitHub Actions 공식 문서](https://docs.github.com/en/actions)

---

**배포에 문제가 있나요?** [문제 해결 섹션](#문제-해결)을 참고하거나 팀에 문의하세요.
