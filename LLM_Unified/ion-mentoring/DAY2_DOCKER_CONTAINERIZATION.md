# Week 3 Day 2: Docker Containerization

**날짜**: 2025-10-17
**작업 시간**: 09:00-12:00
**목표**: REST API를 Docker 컨테이너로 패키징하여 Cloud Run 배포 준비

---

## 📋 목차

- 완료된 작업
- Docker 구성
- 빌드 및 테스트
- 보안 고려사항
- 문제 해결
- 다음 단계

---

## ✅ 완료된 작업

### 1. `.dockerignore` 생성 (116줄)

컨테이너 빌드 시 불필요한 파일 제외:

```dockerignore
# Python cache
__pycache__/
*.py[cod]
.Python

# Virtual environments
.venv/
venv/

# Testing
tests/
.pytest_cache/
.coverage

# Documentation
*.md
docs/

# Git
.git/
.gitignore

# Credentials
.env
*.key
*.pem
credentials/

# Temporary files
*.tmp
*.bak
```

**결과**: 빌드 컨텍스트 크기 최소화 → 빌드 속도 향상

---

### 2. `Dockerfile` 생성 (68줄) - Multi-stage Build

#### Stage 1: Builder

```dockerfile
FROM python:3.13.7-slim as builder
WORKDIR /build

# 빌드 도구 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY requirements-api.txt .
RUN pip install --user --no-cache-dir -r requirements-api.txt
```

**역할**:

- gcc/g++ 설치 (컴파일 필요한 패키지용)
- Python 패키지 빌드 및 설치
- `/root/.local`에 패키지 저장

#### Stage 2: Runtime

```dockerfile
FROM python:3.13.7-slim

LABEL maintainer="Ion Mentoring <ion@naeda.ai>"
LABEL version="1.0.0"

# 비root 사용자 생성
RUN useradd -m -u 1000 ion && \
    mkdir -p /app && \
    chown -R ion:ion /app

WORKDIR /app

# 빌더 스테이지에서 패키지 복사
COPY --from=builder /root/.local /home/ion/.local

# 애플리케이션 코드 복사
COPY --chown=ion:ion ./app ./app
COPY --chown=ion:ion ./persona_pipeline.py .
COPY --chown=ion:ion ./persona_router.py .
COPY --chown=ion:ion ./resonance_converter.py .
COPY --chown=ion:ion ./ion_first_vertex_ai.py .
COPY --chown=ion:ion ./prompt_client.py .

# 환경 변수
ENV PATH=/home/ion/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    ENVIRONMENT=production

USER ion

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**특징**:

- 최소 이미지 크기
- 비root 사용자 실행
- Health check 내장
- Production 환경 설정

---

### 3. Pydantic 버전 업데이트

**문제**: pydantic 2.5.0이 Python 3.13.7과 호환되지 않음

```text
ERROR: Failed building wheel for pydantic-core
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument
```

**해결**:

```diff
- pydantic==2.5.0
- pydantic-settings==2.0.3
+ pydantic==2.10.5  # Python 3.13 compatibility
+ pydantic-settings==2.7.1  # Compatible with pydantic 2.10.5
```

**검증**: 빌드 성공, 런타임 정상 작동 ✅

---

## 🐳 Docker 구성

### 이미지 크기

```bash
docker images ion-api:latest
# REPOSITORY   TAG       IMAGE ID       SIZE
# ion-api      latest    bbad93e7f9f9   487MB
```

**목표 대비**: 487MB < 1GB ✅

### Multi-stage Build의 이점

| 항목                     | 단일 스테이지 | Multi-stage |
| ------------------------ | ------------- | ----------- |
| 이미지 크기              | ~1.2GB        | 487MB       |
| 빌드 도구 포함           | ✅            | ❌          |
| 보안                     | 낮음          | 높음        |
| 빌드 속도 (캐시 사용 시) | 느림          | 빠름        |

---

## ✅ 빌드 및 테스트

### 빌드

```bash
cd D:\nas_backup\LLM_Unified\ion-mentoring
docker build -t ion-api:latest .
```

**빌드 시간**: 29.9초 (초기 빌드)

### 로컬 테스트

#### 1. 컨테이너 실행 (Development 모드)

```bash
docker run -d -p 8081:8080 \
  -e ENVIRONMENT=development \
  --name ion-api-dev \
  ion-api:latest
```

**참고**:

- `-p 8081:8080`: 호스트 8081 → 컨테이너 8080
- `-e ENVIRONMENT=development`: Mock Vertex AI 사용
- `-d`: Detached mode

#### 2. Health Check

```bash
curl http://localhost:8081/health
```

**응답**:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "pipeline_ready": true
}
```

**결과**: ✅ 200 OK

#### 3. Chat Endpoint

```powershell
Invoke-RestMethod -Uri http://localhost:8081/chat `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"message":"안녕하세요"}'
```

**응답**:

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

**결과**: ✅ 200 OK

#### 4. 로그 확인

```bash
docker logs ion-api-dev --tail 20
```

**로그**:

```text
2025-10-17 12:06:31 - INFO - Using mocked Vertex AI client
2025-10-17 12:06:31 - INFO - PersonaPipeline initialized successfully
INFO:     Started server process [1]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     172.17.0.1:54242 - "GET /health HTTP/1.1" 200 OK
INFO:     172.17.0.1:55256 - "POST /chat HTTP/1.1" 200 OK
```

**결과**: Mock Vertex AI 클라이언트 정상 작동 ✅

#### 5. 정리

```bash
docker stop ion-api-dev
docker rm ion-api-dev
```

---

## 🔒 보안 고려사항

### 1. 비root 사용자 실행

```dockerfile
RUN useradd -m -u 1000 ion
USER ion
```

**이유**:

- 컨테이너 탈출 시 호스트 손상 최소화
- 최소 권한 원칙
- Cloud Run 보안 모범 사례

### 2. 파일 소유권 설정

```dockerfile
COPY --chown=ion:ion ./app ./app
```

**이유**:

- root 소유 파일 방지
- 애플리케이션 프로세스 파일 접근 보장

### 3. 최소 베이스 이미지

```dockerfile
FROM python:3.13.7-slim
```

**이유**:

- 공격 표면 최소화
- 이미지 크기 축소 (slim: ~120MB vs full: ~1GB)
- 보안 패치 최소화

### 4. `.dockerignore` 활용

```dockerignore
credentials/
.env
*.key
*.pem
```

**이유**:

- 민감 정보 유출 방지
- 이미지 레이어에 credentials 포함 차단

### 5. Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"
```

**이유**:

- Cloud Run 자동 재시작 지원
- 비정상 컨테이너 조기 감지
- 가용성 향상

---

## 🛠️ 문제 해결

### 문제 1: Pydantic Build 실패

**증상**:

```text
ERROR: Failed building wheel for pydantic-core
TypeError: ForwardRef._evaluate() missing required keyword-only argument
```

**원인**: pydantic 2.5.0의 pydantic-core 2.14.1이 Python 3.13.7과 호환되지 않음

**해결**:

```diff
- pydantic==2.5.0
+ pydantic==2.10.5  # Python 3.13 compatible
```

**교훈**: Python 메이저 버전 업그레이드 시 의존성 버전 호환성 확인 필수

---

### 문제 2: 포트 충돌

**증상**:

```text
Error: Bind for 0.0.0.0:8080 failed: port is already allocated
```

**해결**:

```bash
# 다른 포트 사용
docker run -p 8081:8080 ...
```

**예방**:

```bash
# 사용 중인 포트 확인
netstat -an | findstr :8080
```

---

### 문제 3: 컨테이너 이름 충돌

**증상**:

```text
Error: The container name "/ion-api-dev" is already in use
```

**해결**:

```bash
# 기존 컨테이너 제거 후 재실행
docker rm -f ion-api-dev
docker run --name ion-api-dev ...
```

---

## 📊 최종 결과

### 달성 목표 (WEEK3_KICKOFF.md 기준)

| 항목            | 목표      | 실제      | 상태 |
| --------------- | --------- | --------- | ---- |
| 이미지 크기     | < 1GB     | 487MB     | ✅   |
| 빌드 시간       | < 3분     | 29.9초    | ✅   |
| Health check    | 정상 작동 | 200 OK    | ✅   |
| Chat endpoint   | 정상 작동 | 200 OK    | ✅   |
| Mock 클라이언트 | 정상 작동 | 로그 확인 | ✅   |
| 비root 사용자   | 적용      | ion:1000  | ✅   |

### 파일 변경 사항

```text
9 files changed, 369 insertions(+), 85 deletions(-)

새로 생성:
- .dockerignore (116줄)
- Dockerfile (68줄)

수정:
- requirements-api.txt (pydantic 버전 업데이트)
- app/config.py (사용자 수정)
- app/main.py (사용자 수정)
- ion_first_vertex_ai.py (사용자 수정)
- tests/test_ion_first_vertex_ai.py (사용자 수정)
- tools/quick_check_config.py (사용자 수정)
```

---

## 🚀 다음 단계

### Week 3 Day 3: Cloud Run 배포

1. **GCP 프로젝트 설정**

   ```bash
   gcloud config set project [PROJECT_ID]
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

2. **Artifact Registry 생성**

   ```bash
   gcloud artifacts repositories create ion-api \
     --repository-format=docker \
     --location=us-central1 \
     --description="Ion API Docker images"
   ```

3. **이미지 푸시**

   ```bash
   docker tag ion-api:latest \
     us-central1-docker.pkg.dev/[PROJECT_ID]/ion-api/ion-api:latest

   docker push us-central1-docker.pkg.dev/[PROJECT_ID]/ion-api/ion-api:latest
   ```

4. **Cloud Run 배포**

   ```bash
   gcloud run deploy ion-api \
     --image us-central1-docker.pkg.dev/[PROJECT_ID]/ion-api/ion-api:latest \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --set-env-vars ENVIRONMENT=production
   ```

5. **Secret Manager 연동**

   ```bash
   gcloud run services update ion-api \
     --update-secrets=GOOGLE_APPLICATION_CREDENTIALS=vertex-ai-key:latest
   ```

---

## 📚 참고 자료

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Cloud Run Container Contract](https://cloud.google.com/run/docs/container-contract)
- [Python Official Docker Images](https://hub.docker.com/_/python)

---

**다음 문서**: [DAY3_CLOUD_RUN_DEPLOYMENT.md](./DAY3_CLOUD_RUN_DEPLOYMENT.md)
**이전 문서**: DAY1_REST_API.md (예정)
**Week 3 개요**: [WEEK3_KICKOFF.md](./WEEK3_KICKOFF.md)
