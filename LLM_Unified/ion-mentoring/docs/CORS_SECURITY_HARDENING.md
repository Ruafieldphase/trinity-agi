# CORS 보안 강화 가이드 (30분 작업)

## 📋 개요

**목표**: 프로덕션 배포 전 CORS(Cross-Origin Resource Sharing) 설정을 보안 강화
**현재 상태**: ⚠️ 위험 - `allow_origins: ["*"]` (모든 도메인 허용)
**목표 상태**: ✅ 안전 - 화이트리스트 기반 도메인만 허용

---

## 🚨 현재 보안 문제

### 문제 1: 과도하게 허용된 CORS 정책

**현재 설정** (`config/prod.yaml:61`):
```yaml
api:
  cors_origins:
    - "${API_CORS_ORIGINS:*}"  # ⚠️ 위험: 모든 도메인 허용
```

**문제점**:
- ✗ 모든 도메인에서 요청 가능
- ✗ CSRF(Cross-Site Request Forgery) 공격 위험
- ✗ 세션 탈취 가능성
- ✗ API 남용 및 의도하지 않은 접근 증가

### 문제 2: 환경 변수 의존

**현재 코드** (`app/main.py:203`):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 환경 변수에 의존
    allow_credentials=True,
    allow_methods=["*"],  # ⚠️ 모든 HTTP 메서드 허용
    allow_headers=["*"],  # ⚠️ 모든 헤더 허용
)
```

**문제점**:
- ✗ 환경 변수 설정 실수 시 보안 누수
- ✗ 프로덕션 배포 체크리스트 누락 가능성
- ✗ 모니터링 및 감시 어려움

---

## ✅ 해결 방안

### Step 1: 프로덕션 설정 파일 수정

**파일**: `config/prod.yaml`

```yaml
# 현재 (위험)
api:
  cors_origins:
    - "${API_CORS_ORIGINS:*}"

# 변경할 설정 (안전)
api:
  cors_origins:
    - "https://app.ion-mentoring.com"      # 메인 웹앱
    - "https://admin.ion-mentoring.com"    # 관리자 대시보드
    - "https://api.ion-mentoring.com"      # API 도메인
    - "https://www.ion-mentoring.com"      # WWW 도메인
    - "https://ion-mentoring.vercel.app"   # 스테이징 (필요시)
  allow_credentials: true
  allow_methods:
    - GET
    - POST
    - OPTIONS
  allow_headers:
    - Content-Type
    - Authorization
    - X-Requested-With
    - Accept
```

**설명**:
- 🔒 명시적 도메인 화이트리스트 (와일드카드 제거)
- 🔒 필수 HTTP 메서드만 허용
- 🔒 필수 헤더만 허용
- 🔒 HTTPS만 허용 (보안 채널)

### Step 2: 환경 변수 기본값 변경

**파일**: `.env.production`

```bash
# 기존 설정 제거 (또는 주석 처리)
# API_CORS_ORIGINS="*"  # ❌ 제거

# 대신 GCP Secret Manager 사용으로 전환 (Task 2에서 진행)
# 또는 다음과 같이 명시적으로 설정:
API_CORS_ORIGINS="https://app.ion-mentoring.com,https://admin.ion-mentoring.com"
```

### Step 3: 코드 수정 - 환경 변수 파싱 강화

**파일**: `app/config.py`

```python
from typing import List
import os

class Settings:
    # ... 기존 설정 ...

    @property
    def cors_origins(self) -> List[str]:
        """
        CORS 원본 파싱 (환경 변수에서)

        환경 변수 형식:
        - 단일 도메인: "https://app.example.com"
        - 여러 도메인: "https://app.example.com,https://admin.example.com"

        기본값: 프로덕션에서는 빈 리스트 (거부 우선)
        """
        cors_env = os.getenv("API_CORS_ORIGINS", "")

        if not cors_env:
            if self.is_production:
                logger.warning("CORS_ORIGINS not configured in production - using restrictive defaults")
                return ["https://app.ion-mentoring.com"]  # 기본값: 메인 앱만
            else:
                return ["*"]  # 개발 환경: 모두 허용

        # 쉼표로 분리된 도메인 파싱
        origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

        # 유효성 검사
        for origin in origins:
            if not origin.startswith("https://"):
                logger.error(f"Invalid CORS origin (must be HTTPS): {origin}")
                raise ValueError(f"CORS origins must use HTTPS protocol: {origin}")
            if "*" in origin:
                logger.error(f"Invalid CORS origin (wildcard not allowed): {origin}")
                raise ValueError(f"Wildcard CORS origins are not allowed: {origin}")

        logger.info(f"CORS origins configured: {len(origins)} domain(s)")
        return origins
```

### Step 4: 보안 헤더 추가

**파일**: `app/main.py`

```python
# 기존 CORS 미들웨어 (수정됨)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 화이트리스트
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # 명시적 메서드
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],  # 명시적 헤더
    expose_headers=["X-Process-Time", "X-Request-ID"],  # 노출할 헤더
    max_age=86400,  # Preflight 캐시: 24시간
)

# 추가 보안 헤더 미들웨어
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """보안 헤더 추가"""
    response = await call_next(request)

    # 기본 보안 헤더
    response.headers["X-Content-Type-Options"] = "nosniff"  # MIME 타입 스니핑 방지
    response.headers["X-Frame-Options"] = "DENY"  # 클릭재킹 방지
    response.headers["X-XSS-Protection"] = "1; mode=block"  # XSS 보호
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"  # 리퍼러 정책
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"  # HSTS
    response.headers["Content-Security-Policy"] = "default-src 'self'"  # CSP

    return response
```

---

## 📊 환경별 설정 가이드

### 개발 환경 (`config/dev.yaml`)
```yaml
api:
  cors_origins:
    - "http://localhost:3000"
    - "http://localhost:8000"
    - "http://127.0.0.1:3000"
```

### 테스트 환경 (`config/test.yaml`)
```yaml
api:
  cors_origins:
    - "http://testclient"  # 테스트 클라이언트만
    - "http://localhost"
```

### 프로덕션 환경 (`config/prod.yaml`)
```yaml
api:
  cors_origins:
    - "https://app.ion-mentoring.com"
    - "https://admin.ion-mentoring.com"
    - "https://www.ion-mentoring.com"
```

### 스테이징 환경 (`config/staging.yaml`)
```yaml
api:
  cors_origins:
    - "https://staging-app.ion-mentoring.com"
    - "https://staging-admin.ion-mentoring.com"
    - "https://localhost:3000"  # 로컬 테스트용
```

---

## 🔄 배포 체크리스트

프로덕션 배포 전 다음을 확인하세요:

### 배포 전 체크리스트
- [ ] `config/prod.yaml`에서 와일드카드(`*`) 제거 완료
- [ ] CORS 도메인 화이트리스트 설정 완료
- [ ] 환경 변수 `API_CORS_ORIGINS` 올바르게 설정됨
- [ ] 모든 허용 도메인 HTTPS 사용 확인
- [ ] 보안 헤더 미들웨어 추가 완료
- [ ] 로컬 테스트에서 정상 작동 확인

### 배포 후 검증
- [ ] `/docs` (Swagger UI) 접근 가능
- [ ] API 엔드포인트 정상 응답
- [ ] 허용된 도메인에서 CORS 요청 성공
- [ ] 차단된 도메인에서 CORS 요청 실패
- [ ] 보안 헤더 응답 확인
  ```bash
  curl -i https://api.ion-mentoring.com/health
  # X-Content-Type-Options: nosniff
  # X-Frame-Options: DENY
  # Strict-Transport-Security: max-age=31536000
  ```

---

## 🧪 테스트 방법

### 1. 로컬 테스트

```bash
# 개발 서버 실행
python -m uvicorn app.main:app --reload --env-file .env.development

# 다른 터미널에서 테스트
curl -X OPTIONS http://localhost:8000/chat \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -v
```

### 2. 프로덕션 검증

```bash
# 허용된 도메인 확인
curl -X OPTIONS https://api.ion-mentoring.com/chat \
  -H "Origin: https://app.ion-mentoring.com" \
  -H "Access-Control-Request-Method: POST" \
  -v

# 차단된 도메인 확인
curl -X OPTIONS https://api.ion-mentoring.com/chat \
  -H "Origin: https://evil.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

### 3. 브라우저 개발자 도구 테스트

```javascript
// 콘솔에서 실행 (허용된 도메인)
fetch('https://api.ion-mentoring.com/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',  // 쿠키 포함
  body: JSON.stringify({ message: 'test' })
})

// 응답 확인
// ✅ 성공: 응답 수신
// ❌ 실패: CORS 오류 (예상대로)
```

---

## 🛡️ 보안 최적 사례

### DO ✅
- ✅ HTTPS만 허용
- ✅ 명시적 도메인 화이트리스트 사용
- ✅ 필요한 메서드/헤더만 허용
- ✅ 정기적 도메인 감시
- ✅ 보안 헤더 설정
- ✅ 로그 기록 및 모니터링

### DON'T ❌
- ❌ `allow_origins: ["*"]` 사용
- ❌ `allow_methods: ["*"]` 사용
- ❌ `allow_headers: ["*"]` 사용
- ❌ HTTP 도메인 허용
- ❌ 와일드카드 도메인 사용 (예: `*.example.com`)
- ❌ 민감한 정보를 CORS 응답에 포함

---

## 📋 마이그레이션 단계

### Phase 1: 설정 준비 (즉시)
1. `config/prod.yaml` 수정
2. 환경 변수 설정
3. 로컬 테스트

### Phase 2: 코드 강화 (1시간)
1. `app/config.py` 유효성 검사 추가
2. 보안 헤더 미들웨어 추가
3. 통합 테스트 실행

### Phase 3: 배포 (0시간)
1. 스테이징 환경 배포
2. 검증 완료
3. 프로덕션 배포

### Phase 4: 모니터링 (지속)
1. CORS 에러 로깅
2. 비정상 요청 감시
3. 주기적 감시

---

## 🔗 참고 자료

- [MDN CORS 문서](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI CORS 문서](https://fastapi.tiangolo.com/tutorial/cors/)
- [OWASP CORS 보안](https://owasp.org/www-community/attacks/CSRF)
- [HTTP 보안 헤더](https://owasp.org/www-project-secure-headers/)

---

## 📞 지원 및 문제 해결

### 문제: "CORS policy: No 'Access-Control-Allow-Origin' header"

**원인**: 요청 도메인이 화이트리스트에 없음

**해결**:
1. 요청 도메인 확인
2. `config/prod.yaml`에 도메인 추가
3. 서버 재시작

### 문제: "Preflight request failed"

**원인**: OPTIONS 메서드 차단됨

**해결**:
1. `allow_methods`에 "OPTIONS" 포함 확인
2. 필요한 헤더 `allow_headers`에 포함 확인
3. 서버 로그 확인

### 문제: "Credentials mode is 'include' but 'Access-Control-Allow-Credentials' header is missing"

**원인**: 쿠키가 필요하지만 `allow_credentials` 미설정

**해결**:
1. `allow_credentials: true` 설정
2. 화이트리스트 도메인만 쿠키 허용

---

## 📅 다음 단계

✅ **CORS 보안 강화 완료** (0.5시간)
➡️ **Task 2: Google Secret Manager 통합** (4시간)
➡️ **Task 3: 자동 백업 설정** (2시간)
➡️ **Task 4: 모니터링 및 알림** (4시간)

총 소요 시간: Phase 1 **11시간** 중 0.5시간 완료 ✅
