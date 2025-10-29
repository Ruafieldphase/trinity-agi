# Google Secret Manager 통합 가이드 (4시간 작업)

## 📋 개요

**목표**: 환경 변수 기반 비밀번호 관리에서 Google Secret Manager로 마이그레이션
**현재 상태**: ⚠️ 위험 - API 키/JWT 비밀이 환경 변수로 관리
**목표 상태**: ✅ 안전 - 모든 민감 정보가 Google Secret Manager로 관리

---

## 🚨 현재 보안 문제

### 문제 1: 환경 변수에 저장된 민감 정보

**현재 설정** (`config/prod.yaml` & `.env`):
```bash
# 환경 변수에 저장 (위험 🚨)
JWT_SECRET=your-super-secret-key-here
PINECONE_API_KEY=your-pinecone-api-key
DATABASE_PASSWORD=postgres-password
OPENAI_API_KEY=sk-...
JAEGER_ENDPOINT=http://jaeger:6831
```

**문제점**:
- ✗ 환경 변수는 메모리에 평문 저장
- ✗ 프로세스 목록으로 노출 가능 (`ps aux`, `env`)
- ✗ 로그 파일에 실수로 기록될 수 있음
- ✗ Container 레이어에 평문 저장
- ✗ Git 리포지토리에 커밋될 위험

### 문제 2: 비밀 회전 불가능

**현재 상황**:
- ✗ 비밀 변경 시 서버 재배포 필요
- ✗ 다운타임 발생
- ✗ 감시되지 않은 비밀 업데이트
- ✗ 이전 비밀 추적 불가능

---

## ✅ Google Secret Manager 소개

### 이점

✅ **암호화**: 저장 시 자동 암호화 (AES-256)
✅ **접근 제어**: IAM 기반 세밀한 권한 관리
✅ **감시 로깅**: 모든 비밀 접근 기록
✅ **자동 회전**: 비밀 자동 회전 지원
✅ **버전 관리**: 비밀 변경 이력 관리
✅ **다운타임 없음**: 변경 시 서버 재배포 불필요

---

## 🛠️ 구현 가이드

### Phase 1: GCP 설정 (1시간)

#### Step 1-1: 프로젝트 선택

```bash
# GCP 프로젝트 ID 설정
export GCP_PROJECT_ID="your-project-id"

# 프로젝트 확인
gcloud config set project $GCP_PROJECT_ID
gcloud config get-value project
```

#### Step 1-2: Secret Manager API 활성화

```bash
# Secret Manager API 활성화
gcloud services enable secretmanager.googleapis.com

# 확인
gcloud services list --enabled | grep secretmanager
```

#### Step 1-3: 서비스 계정 생성 (또는 기존 사용)

```bash
# 서비스 계정 생성
gcloud iam service-accounts create ion-api \
  --display-name="ION Mentoring API Service Account"

# 프로젝트 ID 설정
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="ion-api@${PROJECT_ID}.iam.gserviceaccount.com"

# IAM 권한 부여
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

# 추가 권한 (옵션: 비밀 생성 권한)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.admin"
```

#### Step 1-4: 기본 비밀 생성

```bash
# 비밀 생성 (JWT_SECRET)
echo -n "$(openssl rand -base64 32)" | \
  gcloud secrets create jwt-secret --data-file=-

# 비밀 생성 (DB 암호)
echo -n "your-secure-postgres-password" | \
  gcloud secrets create db-password --data-file=-

# 비밀 생성 (Pinecone API 키)
echo -n "your-pinecone-api-key" | \
  gcloud secrets create pinecone-api-key --data-file=-

# 비밀 생성 (Vertex AI 기본값)
echo -n "gemini-1.5-flash-002" | \
  gcloud secrets create vertex-model --data-file=-

# 비밀 생성 (CORS Origins)
echo -n "https://app.ion-mentoring.com,https://admin.ion-mentoring.com" | \
  gcloud secrets create cors-origins --data-file=-
```

#### Step 1-5: 비밀 확인

```bash
# 생성된 비밀 목록
gcloud secrets list

# 비밀 상세 정보
gcloud secrets describe jwt-secret

# 비밀 버전 확인
gcloud secrets versions list jwt-secret
```

---

### Phase 2: 파이썬 라이브러리 설치 (10분)

#### Step 2-1: 의존성 설치

```bash
# Google Secret Manager 클라이언트 설치
pip install google-cloud-secret-manager

# 또는 pyproject.toml에 추가
# dependencies = [
#     ...,
#     "google-cloud-secret-manager>=2.16.0",
# ]
```

#### Step 2-2: 인증 설정 (로컬 개발용)

```bash
# Google Cloud 계정으로 인증 (개발용)
gcloud auth application-default login

# 서비스 계정 키 생성 (운영 환경용 - Cloud Run의 경우 불필요)
gcloud iam service-accounts keys create ion-api-key.json \
  --iam-account=$SERVICE_ACCOUNT
```

---

### Phase 3: 코드 구현 (2시간)

#### Step 3-1: Secret Manager 클라이언트 생성

**파일**: `app/secret_manager.py` (새로 생성)

```python
"""Google Secret Manager 통합"""

import os
import logging
from typing import Optional
from functools import lru_cache
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class SecretManagerClient:
    """Google Secret Manager 클라이언트"""

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Secret Manager client.

        Args:
            project_id: GCP Project ID (기본값: GOOGLE_CLOUD_PROJECT 환경변수)
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError("project_id not provided and GOOGLE_CLOUD_PROJECT not set")

        try:
            self.client = secretmanager.SecretManagerServiceClient()
            logger.info(f"Secret Manager initialized for project: {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Secret Manager: {str(e)}")
            raise

    def get_secret(self, secret_id: str, version: str = "latest") -> str:
        """
        비밀 값 가져오기

        Args:
            secret_id: 비밀 ID (예: "jwt-secret")
            version: 비밀 버전 (기본값: "latest")

        Returns:
            비밀 값 (문자열)

        Raises:
            Exception: 비밀을 찾을 수 없거나 접근 권한 없음
        """
        try:
            name = self.client.secret_version_path(
                self.project_id,
                secret_id,
                version
            )
            response = self.client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("UTF-8")
            logger.debug(f"Retrieved secret: {secret_id}")
            return payload
        except Exception as e:
            logger.error(f"Failed to get secret {secret_id}: {str(e)}")
            raise

    def create_secret(self, secret_id: str, value: str) -> str:
        """
        새 비밀 생성

        Args:
            secret_id: 비밀 ID
            value: 비밀 값

        Returns:
            생성된 비밀 경로
        """
        try:
            parent = self.client.project_path(self.project_id)
            secret = {
                "replication": {
                    "automatic": {}
                }
            }
            created_secret = self.client.create_secret(
                request={"parent": parent, "secret_id": secret_id, "secret": secret}
            )

            # 버전 추가
            version = self.client.add_secret_version(
                request={
                    "parent": created_secret.name,
                    "payload": {"data": value.encode("UTF-8")}
                }
            )

            logger.info(f"Created secret: {secret_id}")
            return created_secret.name
        except Exception as e:
            logger.error(f"Failed to create secret {secret_id}: {str(e)}")
            raise

    def update_secret(self, secret_id: str, value: str) -> str:
        """
        기존 비밀 값 업데이트 (새 버전 생성)

        Args:
            secret_id: 비밀 ID
            value: 새로운 비밀 값

        Returns:
            생성된 버전 경로
        """
        try:
            secret_path = self.client.secret_path(self.project_id, secret_id)
            version = self.client.add_secret_version(
                request={
                    "parent": secret_path,
                    "payload": {"data": value.encode("UTF-8")}
                }
            )
            logger.info(f"Updated secret: {secret_id}")
            return version.name
        except Exception as e:
            logger.error(f"Failed to update secret {secret_id}: {str(e)}")
            raise

    def list_secret_versions(self, secret_id: str):
        """
        비밀의 모든 버전 나열

        Args:
            secret_id: 비밀 ID

        Returns:
            버전 목록
        """
        try:
            secret_path = self.client.secret_path(self.project_id, secret_id)
            versions = self.client.list_secret_versions(
                request={"parent": secret_path}
            )
            logger.debug(f"Listed versions for secret: {secret_id}")
            return list(versions)
        except Exception as e:
            logger.error(f"Failed to list versions for {secret_id}: {str(e)}")
            raise

    @lru_cache(maxsize=128)
    def get_cached_secret(self, secret_id: str) -> str:
        """
        캐시된 비밀 값 가져오기 (메모리 캐시)

        주의: 캐시 TTL 없음. 프로덕션에서는 Redis 캐시 사용 권장

        Args:
            secret_id: 비밀 ID

        Returns:
            비밀 값
        """
        return self.get_secret(secret_id)


# 싱글톤 인스턴스
_secret_client: Optional[SecretManagerClient] = None


def get_secret_manager() -> SecretManagerClient:
    """Secret Manager 클라이언트 싱글톤 반환"""
    global _secret_client
    if _secret_client is None:
        _secret_client = SecretManagerClient()
    return _secret_client


def get_secret(secret_id: str, default: Optional[str] = None) -> str:
    """
    비밀 값 가져오기 (Helper 함수)

    Args:
        secret_id: 비밀 ID
        default: 기본값 (비밀이 없을 경우)

    Returns:
        비밀 값 또는 기본값
    """
    try:
        return get_secret_manager().get_secret(secret_id)
    except Exception as e:
        if default is not None:
            logger.warning(f"Using default value for {secret_id}: {str(e)}")
            return default
        raise
```

#### Step 3-2: 설정 통합

**파일**: `app/config.py` (수정)

```python
"""
FastAPI 애플리케이션 설정 관리

환경 변수 및 Google Secret Manager에서 설정을 로드합니다.
"""

import os
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 기본 설정
    app_name: str = Field(default="내다AI Ion API", description="애플리케이션 이름")
    app_version: str = Field(default="1.0.0", description="버전")
    environment: str = Field(default="development", description="환경 (development/production)")

    # 서버 설정
    host: str = Field(default="0.0.0.0", description="서버 호스트")
    port: int = Field(default=8080, description="서버 포트")
    reload: bool = Field(default=True, description="Hot reload (개발용)")

    # CORS 설정
    cors_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="허용할 Origin 목록"
    )

    # Vertex AI 설정
    vertex_project_id: Optional[str] = Field(
        default=None,
        description="GCP 프로젝트 ID",
        validation_alias="VERTEX_PROJECT_ID"
    )
    vertex_location: str = Field(
        default="us-central1",
        description="Vertex AI 리전",
        validation_alias="VERTEX_LOCATION"
    )
    vertex_model: Optional[str] = Field(
        default=None,
        description="사용할 Vertex AI 모델",
        validation_alias="VERTEX_MODEL"
    )

    # 비밀 관리 설정
    use_secret_manager: bool = Field(
        default=True,
        description="Google Secret Manager 사용",
        validation_alias="USE_SECRET_MANAGER"
    )
    gcp_project_id: Optional[str] = Field(
        default=None,
        description="GCP Project ID (Secret Manager용)",
        validation_alias="GCP_PROJECT_ID"
    )

    # 민감한 정보 (Secret Manager 또는 환경변수에서)
    jwt_secret: Optional[str] = Field(
        default=None,
        description="JWT 비밀 키",
        validation_alias="JWT_SECRET"
    )
    database_password: Optional[str] = Field(
        default=None,
        description="데이터베이스 암호",
        validation_alias="DATABASE_PASSWORD"
    )
    pinecone_api_key: Optional[str] = Field(
        default=None,
        description="Pinecone API 키",
        validation_alias="PINECONE_API_KEY"
    )

    # 로깅 설정
    log_level: str = Field(default="INFO", description="로그 레벨", validation_alias="LOG_LEVEL")
    use_cloud_logging: bool = Field(
        default=False,
        description="Google Cloud Logging 사용",
        validation_alias="USE_CLOUD_LOGGING"
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Rate Limiting 활성화")
    rate_limit_calls: int = Field(default=10, description="분당 요청 제한")
    rate_limit_period: int = Field(default=60, description="제한 기간 (초)")

    def __init__(self, **kwargs):
        """초기화 시 Secret Manager에서 비밀 로드"""
        super().__init__(**kwargs)

        # 프로덕션 환경 + Secret Manager 활성화 시 비밀 로드
        if self.is_production and self.use_secret_manager:
            self._load_from_secret_manager()

    def _load_from_secret_manager(self):
        """Secret Manager에서 비밀 로드"""
        try:
            from app.secret_manager import get_secret_manager

            sm = get_secret_manager()

            # JWT 비밀
            if not self.jwt_secret:
                try:
                    self.jwt_secret = sm.get_secret("jwt-secret")
                    logger.info("JWT secret loaded from Secret Manager")
                except Exception as e:
                    logger.error(f"Failed to load JWT secret: {str(e)}")

            # 데이터베이스 암호
            if not self.database_password:
                try:
                    self.database_password = sm.get_secret("db-password")
                    logger.info("Database password loaded from Secret Manager")
                except Exception as e:
                    logger.warning(f"Database password not in Secret Manager: {str(e)}")

            # Pinecone API 키
            if not self.pinecone_api_key:
                try:
                    self.pinecone_api_key = sm.get_secret("pinecone-api-key")
                    logger.info("Pinecone API key loaded from Secret Manager")
                except Exception as e:
                    logger.warning(f"Pinecone API key not in Secret Manager: {str(e)}")

            # Vertex AI 모델
            if not self.vertex_model:
                try:
                    self.vertex_model = sm.get_secret("vertex-model")
                    logger.info("Vertex model loaded from Secret Manager")
                except Exception as e:
                    logger.warning(f"Vertex model not in Secret Manager: {str(e)}")

            # CORS Origins
            if self.cors_origins == ["*"]:
                try:
                    cors_str = sm.get_secret("cors-origins")
                    self.cors_origins = [o.strip() for o in cors_str.split(",")]
                    logger.info(f"CORS origins loaded from Secret Manager: {len(self.cors_origins)} domain(s)")
                except Exception as e:
                    logger.warning(f"CORS origins not in Secret Manager: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to load from Secret Manager: {str(e)}")
            raise

    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.environment.lower() == "production"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        """CORS 원본 파싱"""
        if isinstance(value, str):
            items = [origin.strip() for origin in value.split(",") if origin.strip()]
            return items or ["*"]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# 싱글톤 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스 반환 (의존성 주입용)"""
    return settings


def is_production() -> bool:
    """프로덕션 환경 여부"""
    return settings.is_production
```

---

### Phase 4: 배포 설정 (30분)

#### Step 4-1: Cloud Run 환경 변수 설정

```yaml
# cloud-run-deploy.yaml 또는 gcloud 명령어

# 기본 환경 변수만 설정 (비밀은 Secret Manager 참조)
environment_variables:
  ENVIRONMENT: production
  GCP_PROJECT_ID: your-project-id
  USE_SECRET_MANAGER: "true"
  USE_CLOUD_LOGGING: "true"
  LOG_LEVEL: INFO
  VERTEX_PROJECT_ID: your-project-id
  VERTEX_LOCATION: us-central1
```

#### Step 4-2: 서비스 계정 바인딩

```bash
# Cloud Run 서비스 계정이 비밀 접근 권한 가지도록 설정
gcloud run services update ion-api \
  --service-account=ion-api@your-project-id.iam.gserviceaccount.com \
  --region=us-central1 \
  --platform=managed

# 권한 확인
gcloud projects get-iam-policy your-project-id \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount/ion-api*"
```

#### Step 4-3: 배포 스크립트

```bash
#!/bin/bash
# scripts/deploy-with-secrets.sh

set -e

PROJECT_ID="your-project-id"
SERVICE_NAME="ion-api"
REGION="us-central1"

echo "🚀 Deploying ION API with Secret Manager..."

# 1. Secret Manager 비밀 확인
echo "📋 Verifying secrets..."
for secret in jwt-secret db-password pinecone-api-key vertex-model cors-origins; do
  if gcloud secrets describe $secret --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "  ✅ $secret"
  else
    echo "  ❌ $secret NOT FOUND"
    exit 1
  fi
done

# 2. Docker 빌드 및 배포
echo "🏗️  Building and deploying..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region=$REGION \
  --platform=managed \
  --memory=2Gi \
  --cpu=2 \
  --timeout=120 \
  --max-instances=100 \
  --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=$PROJECT_ID,USE_SECRET_MANAGER=true" \
  --service-account="ion-api@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project=$PROJECT_ID

echo "✅ Deployment complete!"
```

---

### Phase 5: 모니터링 및 감시 (30분)

#### Step 5-1: 접근 로깅 설정

```bash
# Cloud Logging에서 Secret Manager 접근 로그 확인
gcloud logging read "resource.type=secretmanager.googleapis.com" \
  --limit=50 \
  --format=json \
  --project=$GCP_PROJECT_ID
```

#### Step 5-2: 감시 규칙 생성

```bash
# 비정상 접근 감시 (실패한 접근 시도)
gcloud logging sinks create secret-access-alert \
  logging.googleapis.com/projects/$GCP_PROJECT_ID/logs/secret-access \
  --log-filter='resource.type="secretmanager.googleapis.com" AND severity=ERROR'
```

---

## 📋 마이그레이션 체크리스트

### 준비 단계
- [ ] GCP Secret Manager API 활성화
- [ ] 서비스 계정 생성 및 권한 부여
- [ ] `google-cloud-secret-manager` 라이브러리 설치

### Secret 생성
- [ ] `jwt-secret` 생성
- [ ] `db-password` 생성
- [ ] `pinecone-api-key` 생성
- [ ] `vertex-model` 생성
- [ ] `cors-origins` 생성

### 코드 구현
- [ ] `app/secret_manager.py` 생성
- [ ] `app/config.py` 수정
- [ ] 테스트 코드 작성

### 배포
- [ ] 로컬 테스트 완료
- [ ] 스테이징 환경 배포
- [ ] 프로덕션 배포

### 모니터링
- [ ] 접근 로그 확인
- [ ] 감시 규칙 설정
- [ ] 정기적 감시

---

## 🧪 테스트 방법

### 1. 로컬 테스트 (개발용)

```python
# test_secret_manager.py

import pytest
from app.secret_manager import get_secret_manager, get_secret

def test_get_secret():
    """비밀 가져오기 테스트"""
    sm = get_secret_manager()

    # 기존 비밀 가져오기
    secret = sm.get_secret("jwt-secret")
    assert secret is not None
    assert len(secret) > 0

def test_get_secret_with_default():
    """기본값과 함께 비밀 가져오기"""
    secret = get_secret("nonexistent-secret", default="default-value")
    assert secret == "default-value"

def test_create_secret():
    """비밀 생성 테스트"""
    sm = get_secret_manager()
    secret_id = "test-secret-" + str(int(__import__('time').time()))
    value = "test-value"

    path = sm.create_secret(secret_id, value)
    assert path is not None

    # 생성된 비밀 확인
    retrieved = sm.get_secret(secret_id)
    assert retrieved == value
```

### 2. 프로덕션 검증

```bash
# 비밀 접근 확인
python -c "from app.config import settings; print(f'JWT Secret loaded: {bool(settings.jwt_secret)}')"

# Cloud Logging에서 접근 기록 확인
gcloud logging read "resource.type=secretmanager.googleapis.com" \
  --limit=10 \
  --project=$GCP_PROJECT_ID
```

---

## 🛡️ 보안 최적 사례

### DO ✅
- ✅ 모든 민감 정보 Secret Manager에 저장
- ✅ 정기적 비밀 회전 (90일마다)
- ✅ IAM 권한 최소화 (최소 권한 원칙)
- ✅ 접근 로그 정기 검토
- ✅ 백업 및 재해 복구 계획

### DON'T ❌
- ❌ 환경 변수에 비밀 저장
- ❌ 코드에 하드코딩된 비밀
- ❌ Git 리포지토리에 커밋
- ❌ 과도한 IAM 권한
- ❌ 접근 로그 무시

---

## 📊 마이그레이션 단계별 요약

| Phase | 작업 | 시간 | 상태 |
|-------|------|------|------|
| 1 | GCP 설정 | 1시간 | ⏳ |
| 2 | 라이브러리 설치 | 10분 | ⏳ |
| 3 | 코드 구현 | 2시간 | ⏳ |
| 4 | 배포 설정 | 30분 | ⏳ |
| 5 | 모니터링 | 30분 | ⏳ |
| **총계** | | **4시간** | ⏳ |

---

## 📞 문제 해결

### 문제: "Permission denied" 에러

**원인**: 서비스 계정이 비밀 접근 권한 없음

**해결**:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

### 문제: "Secret not found" 에러

**원인**: 비밀이 생성되지 않음

**해결**:
```bash
# 비밀 생성
echo -n "value" | gcloud secrets create secret-name --data-file=-

# 확인
gcloud secrets describe secret-name
```

### 문제: "Cloud Run timeout"

**원인**: Secret Manager 접근 시간 초과

**해결**:
- 캐시 사용 (로컬 메모리 또는 Redis)
- 타임아웃 시간 증가

---

## 📅 다음 단계

✅ **CORS 보안 강화 완료** (0.5시간)
✅ **Google Secret Manager 통합 가이드 완료** (4시간)
➡️ **Task 3: 자동 백업 및 복구 설정** (2시간)
➡️ **Task 4: 모니터링 및 알림 설정** (4시간)

총 소요 시간: Phase 1 **11시간** 중 **4.5시간** 완료 ✅
