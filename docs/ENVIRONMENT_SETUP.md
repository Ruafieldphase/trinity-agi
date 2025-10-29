# 환경 설정 가이드

이 문서는 프로젝트 환경변수 설정 방법을 안내합니다.

## 빠른 시작

### 1. 환경변수 파일 생성

```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# 또는 대화형 설정 도구 사용
python scripts/setup_env.py
```

### 2. 필수 환경변수 설정

`.env` 파일을 열어 다음 값들을 설정하세요:

```bash
# Vertex AI (필수)
GCP_PROJECT=your-project-id
GOOGLE_API_KEY=your-api-key

# Vertex AI (선택사항)
GCP_LOCATION=us-central1
VERTEX_MODEL_GEMINI=gemini-1.5-flash-002
EMBEDDINGS_MODEL=text-embedding-004
```

### 3. 설정 검증

```bash
# 환경변수 설정 상태 확인
python scripts/check_env_config.py

# 상세 정보 포함
python scripts/check_env_config.py --verbose
```

## 환경변수 목록

### Vertex AI 설정

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `GCP_PROJECT` | ✅ | - | Google Cloud 프로젝트 ID |
| `GOOGLE_CLOUD_PROJECT` | ⚪ | - | GCP_PROJECT 별칭 |
| `VERTEX_PROJECT_ID` | ⚪ | - | GCP_PROJECT 별칭 |
| `GCP_LOCATION` | ⚪ | us-central1 | Vertex AI 리전 |
| `GOOGLE_CLOUD_REGION` | ⚪ | - | GCP_LOCATION 별칭 |
| `VERTEX_LOCATION` | ⚪ | - | GCP_LOCATION 별칭 |
| `GOOGLE_API_KEY` | ⚪ | - | Google AI Studio API 키 (없으면 ADC 사용) |
| `VERTEX_MODEL_GEMINI` | ⚪ | gemini-1.5-flash-002 | 사용할 Gemini 모델 |
| `GEMINI_MODEL` | ⚪ | - | VERTEX_MODEL_GEMINI 별칭 |
| `EMBEDDINGS_MODEL` | ⚪ | text-embedding-004 | 임베딩 모델 |

### Redis 캐시 설정

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `REDIS_ENABLED` | ⚪ | false | Redis 캐싱 활성화 |
| `REDIS_HOST` | ⚪ | localhost | Redis 호스트 |
| `REDIS_PORT` | ⚪ | 6379 | Redis 포트 |
| `REDIS_DB` | ⚪ | 0 | Redis DB 번호 |
| `REDIS_PASSWORD` | ⚪ | - | Redis 비밀번호 |

### 모니터링 설정

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `EVIDENCE_GATE_FORCE` | ⚪ | false | Evidence Gate 강제 모드 |
| `AGI_LEDGER_PATH` | ⚪ | - | AGI 레저 파일 경로 |
| `EVIDENCE_LEDGER_PATH` | ⚪ | - | Evidence 레저 파일 경로 |

## 환경별 설정 예시

### 로컬 개발 환경

```bash
# .env
GCP_PROJECT=my-dev-project
GOOGLE_API_KEY=AIza...
GCP_LOCATION=us-central1
REDIS_ENABLED=false
EVIDENCE_GATE_FORCE=true
```

### 스테이징 환경

```bash
# .env
GCP_PROJECT=my-staging-project
GCP_LOCATION=asia-northeast3
REDIS_ENABLED=true
REDIS_HOST=staging-redis.example.com
REDIS_PASSWORD=staging-password
```

### 프로덕션 환경

```bash
# .env (또는 시스템 환경변수)
GCP_PROJECT=my-prod-project
GCP_LOCATION=us-central1
REDIS_ENABLED=true
REDIS_HOST=prod-redis.example.com
REDIS_PASSWORD=${REDIS_PROD_PASSWORD}  # Secret Manager에서 주입
VERTEX_MODEL_GEMINI=gemini-1.5-pro  # 더 강력한 모델 사용
```

## 인증 설정

### Google Cloud 인증

두 가지 방법 중 하나를 선택하세요:

**방법 1: API 키 사용 (로컬 개발 권장)**

```bash
# .env에 추가
GOOGLE_API_KEY=AIza...
```

**방법 2: Application Default Credentials (프로덕션 권장)**

```bash
# 서비스 계정 키 파일 지정
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# 또는 gcloud CLI로 인증
gcloud auth application-default login
```

### Redis 인증

인증이 필요한 경우:

```bash
REDIS_PASSWORD=your-redis-password
```

인증이 필요 없는 경우 (로컬 개발):

```bash
REDIS_PASSWORD=
```

## 문제 해결

### "Project ID not set" 오류

```bash
# 해결 방법: GCP_PROJECT 환경변수 설정
export GCP_PROJECT=your-project-id

# 또는 .env 파일에 추가
echo "GCP_PROJECT=your-project-id" >> .env
```

### Vertex AI 인증 실패

```bash
# ADC 재설정
gcloud auth application-default login

# 또는 GOOGLE_API_KEY 설정
export GOOGLE_API_KEY=your-api-key
```

### Redis 연결 실패

```bash
# Redis 서버 상태 확인
redis-cli ping

# 연결 테스트
python -c "import redis; r=redis.Redis(host='localhost'); print(r.ping())"

# 문제가 있다면 Redis 비활성화
export REDIS_ENABLED=false
```

## 보안 모범 사례

### ✅ 해야 할 것

- `.env` 파일을 `.gitignore`에 추가 (이미 설정됨)
- 프로덕션 환경에서는 Secret Manager 사용
- API 키를 정기적으로 로테이션
- 최소 권한 원칙으로 서비스 계정 생성

### ❌ 하지 말아야 할 것

- `.env` 파일을 Git에 커밋
- API 키를 코드에 하드코딩
- 프로덕션 키를 로컬 개발에 사용
- 공개 저장소에 환경변수 노출

## 도구 사용법

### 환경 설정 도우미

대화형으로 `.env` 파일 생성:

```bash
python scripts/setup_env.py
```

빠른 모드 (기본값 사용):

```bash
python scripts/setup_env.py
# 프롬프트에서 2 선택
```

기존 `.env` 덮어쓰기:

```bash
python scripts/setup_env.py --force
```

### 환경 검증 스크립트

설정 상태 확인:

```bash
python scripts/check_env_config.py
```

상세 정보 포함:

```bash
python scripts/check_env_config.py --verbose
```

배포 전 자동 검증:

```bash
python scripts/check_env_config.py && echo "Ready to deploy"
```

## CI/CD 통합

### GitHub Actions 예시

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Validate Environment
        env:
          GCP_PROJECT: ${{ secrets.GCP_PROJECT }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
          GCP_LOCATION: us-central1
        run: |
          python scripts/check_env_config.py
      
      - name: Deploy
        run: |
          # 배포 스크립트 실행
```

## 추가 리소스

- [Google Cloud 인증 문서](https://cloud.google.com/docs/authentication)
- [Vertex AI 리전 목록](https://cloud.google.com/vertex-ai/docs/general/locations)
- [Redis 설정 가이드](https://redis.io/docs/manual/config/)
- [.env 파일 모범 사례](https://12factor.net/config)

## 문의

환경 설정 관련 문제가 있다면:

1. 먼저 `python scripts/check_env_config.py --verbose` 실행
2. 에러 메시지 확인 및 문제 해결 섹션 참조
3. 이슈 트래커에 문의
