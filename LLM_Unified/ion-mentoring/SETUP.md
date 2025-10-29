# ION Mentoring 설정 및 실행 가이드

이 문서는 ION Mentoring 프로젝트를 개발/테스트/프로덕션 환경에서 설정하고 실행하는 방법을 설명합니다.

## 목차

1. [필수 요구사항](#필수-요구사항)
2. [초기 설정](#초기-설정)
3. [환경별 설정](#환경별-설정)
4. [설치 및 실행](#설치-및-실행)
5. [설정 파일 설명](#설정-파일-설명)
6. [문제 해결](#문제-해결)

---

## 필수 요구사항

### 시스템 요구사항

- **Python**: 3.11 이상 3.13 미만
- **OS**: Linux, macOS, Windows
- **메모리**: 최소 4GB (개발), 8GB (프로덕션)
- **디스크**: 최소 2GB

### 개발 도구

- Git
- pip (Python 패키지 관리자)
- Docker (선택, 프로덕션 배포용)

### 외부 서비스 계정

- **Google Cloud Platform (필수)**
  - Vertex AI 액세스 권한
  - Cloud Project ID
- **Redis (선택, 프로덕션)**
- **PostgreSQL (선택, 프로덕션)**

---

## 초기 설정

### 1단계: 저장소 클론

```bash
git clone https://github.com/nada-ai/ion-mentoring.git
cd ion-mentoring
```

### 2단계: Python 가상 환경 생성

```bash
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3단계: 환경 변수 설정

```bash
# .env.example을 .env로 복사
cp .env.example .env

# 에디터로 .env 파일을 열어 필요한 값 입력
# 최소한 다음 변수는 반드시 설정해야 함:
# - ENVIRONMENT (development/staging/production)
# - GCP_PROJECT_ID (Google Cloud 프로젝트 ID)
```

---

## 환경별 설정

### 개발 환경 (Development)

**사용하는 설정 파일:**

- `config/base.yaml` + `config/dev.yaml`
- `.env`의 `ENVIRONMENT=development`

**특징:**

- Mock 백엔드 사용 (실제 LLM 호출 없음)
- 디버그 모드 활성화
- Hot reload 활성화
- 로깅: 텍스트 형식 (가독성)
- Rate Limiting 비활성화

**설정 방법:**

```bash
# .env 파일 설정
ENVIRONMENT=development
CONFIG_PATH=config/dev.yaml
DEBUG=true
LOG_LEVEL=DEBUG
BACKEND_TYPE=mock
```

### 테스트 환경 (Test)

**사용하는 설정 파일:**

- `config/base.yaml` + `config/test.yaml`
- `.env`의 `ENVIRONMENT=test`

**특징:**

- Mock 백엔드
- 로깅 최소화
- 캐시 비활성화
- 각 테스트마다 데이터 초기화

**설정 방법:**

```bash
# pytest 실행 시 자동으로 test.yaml 로드
pytest --config test.yaml

# 또는 환경 변수 설정
ENVIRONMENT=test pytest
```

### 스테이징 환경 (Staging)

**사용하는 설정 파일:**

- `config/base.yaml` + `config/prod.yaml` (일부 수정)

**특징:**

- 프로덕션과 유사한 설정
- 실제 Vertex AI 사용
- 로깅: JSON 형식
- Rate Limiting 활성화
- 모니터링 활성화

### 프로덕션 환경 (Production)

**사용하는 설정 파일:**

- `config/base.yaml` + `config/prod.yaml`
- 환경 변수 (민감한 정보는 환경 변수에서만)

**특징:**

- 보안 강화
- 모니터링 및 추적 활성화
- 고가용성 설정 (Redis, PostgreSQL)
- 자동 롤백 설정

---

## 설치 및 실행

### 의존성 설치

**개발 환경:**

```bash
# pyproject.toml에서 모든 의존성 설치
pip install -e ".[dev,test]"

# 또는 requirements-lock.txt 사용 (정확한 버전)
pip install -r requirements-lock.txt
```

**프로덕션:**

```bash
# 필수 의존성만 설치
pip install -e .

# RAG 기능 포함
pip install -e ".[rag]"
```

### 애플리케이션 실행

**개발 환경:**

```bash
# 기본 실행
python -m app.main

# 또는 uvicorn 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 환경 설정 지정
ENVIRONMENT=development python -m app.main
```

**테스트 실행:**

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 실행
pytest tests/unit/test_persona_orchestrator.py

# 커버리지 리포트 생성
pytest --cov=. --cov-report=html

# 병렬 실행 (속도 향상)
pytest -n auto
```

**프로덕션:**

```bash
# Docker 사용
docker build -t ion-mentoring:latest .
docker run -e ENVIRONMENT=production \
           -e GCP_PROJECT_ID=your-project \
           -p 8080:8080 \
           ion-mentoring:latest

# 또는 Kubernetes
kubectl apply -f k8s/deployment.yaml
```

---

## 설정 파일 설명

### 파일 구조

```
config/
├── base.yaml      # 모든 환경의 기본 설정
├── dev.yaml       # 개발 환경 오버라이드
├── test.yaml      # 테스트 환경 오버라이드
└── prod.yaml      # 프로덕션 환경 오버라이드

.env.example       # 환경 변수 템플릿
.env               # 실제 환경 변수 (커밋 제외)

pyproject.toml     # Python 프로젝트 메타데이터 및 의존성
requirements-lock.txt  # 잠금된 의존성 버전
```

### YAML 설정 파일 계층화

설정은 다음 순서로 병합됩니다:

1. `config/base.yaml` (기본값)
2. `config/{ENVIRONMENT}.yaml` (환경별 오버라이드)
3. 환경 변수 (최고 우선순위)

**예제:**

```yaml
# config/base.yaml
logging:
  level: "INFO"
  format: "json"

# config/dev.yaml (오버라이드)
logging:
  level: "DEBUG"
  format: "text"

# 결과: dev 환경에서는 DEBUG 레벨, 텍스트 형식
```

---

## 주요 설정 항목

### 1. 백엔드 LLM 선택

```yaml
backend:
  type: "mock" # mock, vertex-ai, openai, anthropic
```

**옵션별 설정:**

- **mock**: 테스트/개발 (실제 LLM 호출 없음)
- **vertex-ai**: Google Vertex AI (권장)
- **openai**: OpenAI API
- **anthropic**: Anthropic Claude API

### 2. 데이터베이스 설정

```yaml
database:
  type: "json" # json, sqlite, postgresql
```

**프로덕션 시 PostgreSQL 권장:**

```bash
# PostgreSQL 설정 환경 변수
POSTGRES_HOST=your-db.rds.amazonaws.com
POSTGRES_PORT=5432
POSTGRES_DB=ion_mentoring
POSTGRES_USER=ion_user
POSTGRES_PASSWORD=secure-password
```

### 3. 캐싱 설정

```yaml
cache:
  type: "memory" # memory, redis
  ttl_seconds: 300
```

**Redis 설정 (프로덕션):**

```bash
REDIS_HOST=your-redis.cache.amazonaws.com
REDIS_PORT=6379
REDIS_PASSWORD=secure-password
```

### 4. Rate Limiting

```yaml
api:
  rate_limit:
    enabled: true
    calls_per_minute: 60
    storage: "memory" # memory, redis
```

---

## 문제 해결

### 1. `ModuleNotFoundError: No module named 'app'`

**원인:** Python 경로 설정 오류

**해결책:**

```bash
# 프로젝트 루트에서 실행
cd /path/to/ion-mentoring

# 또는 PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:/path/to/ion-mentoring"
```

### 2. `GCP_PROJECT_ID not set`

**원인:** Google Cloud 프로젝트 ID 미설정

**해결책:**

```bash
# .env 파일에 설정
echo "GCP_PROJECT_ID=your-project-id" >> .env

# 또는 환경 변수로 설정
export GCP_PROJECT_ID=your-project-id
```

### 3. `Redis connection refused`

**원인:** Redis 서버가 실행 중이지 않음

**해결책:**

```bash
# Redis 설치 (macOS)
brew install redis
brew services start redis

# Redis 설치 (Linux)
sudo apt-get install redis-server
sudo systemctl start redis-server

# 또는 Docker 사용
docker run -d -p 6379:6379 redis:7
```

### 4. 테스트 실패 (`pytest` 오류)

**원인:** 테스트 의존성 미설치

**해결책:**

```bash
# 개발 의존성 설치
pip install -e ".[dev,test]"

# 또는
pip install pytest pytest-asyncio pytest-mock
```

### 5. 설정 파일을 찾을 수 없음

**원인:** CONFIG_PATH 경로 오류

**해결책:**

```bash
# .env 파일에서 경로 확인
cat .env | grep CONFIG_PATH

# 절대 경로 사용
CONFIG_PATH=/absolute/path/to/config/dev.yaml
```

---

## 다음 단계

1. **API 테스트**

   ```bash
   # Swagger UI 접속
   http://localhost:8000/docs
   ```

2. **로드 테스트**

   ```bash
   # locust 로드 테스트 실행
   locust -f load_test.py --host http://localhost:8000
   ```

3. **모니터링 대시보드**
   ```bash
   # Prometheus 메트릭 조회
   http://localhost:9090
   ```

---

## 참고 문서

- [API 문서](api/v2/openapi.yaml)
- [개발자 온보딩](docs/DEVELOPER_ONBOARDING.md)
- [배포 가이드](DEPLOYMENT.md)
- [문제 해결 가이드](docs/TROUBLESHOOTING_GUIDE.md)

---

**문제가 발생했나요?** GitHub Issues에서 보고해주세요: https://github.com/nada-ai/ion-mentoring/issues
