# 📐 Phase 1-3 아키텍처 가이드

**최종 작성일**: 2025-10-19
**상태**: Phase 4 배포 전 검증 완료
**테스트 결과**: 414 passed, 7 failed, 36 errors (의존성 및 호환성 이슈)

---

## 📋 목차

1. [Phase 개요](#phase-개요)
2. [핵심 시스템 아키텍처](#핵심-시스템-아키텍처)
3. [Phase별 역할과 구성](#phase별-역할과-구성)
4. [데이터 흐름](#데이터-흐름)
5. [배포 구성](#배포-구성)
6. [테스트 현황](#테스트-현황)
7. [알려진 이슈 및 개선 사항](#알려진-이슈-및-개선-사항)

---

## Phase 개요

ION Mentoring은 **다중 페르소나 AI 채팅 시스템**으로, 3개의 Phase로 구성되어 있습니다:

| Phase | 기간 | 주요 기능 | 상태 |
|-------|------|---------|------|
| **Phase 1** | Week 1 | 개발 환경 구성, Vertex AI 통합 | ✅ 완료 |
| **Phase 2** | Week 2 | 아키텍처 설계, 페르소나 라우팅 | ✅ 완료 |
| **Phase 3** | Week 3-5 | Cloud Run 배포, 멀티 페르소나 통합 | ✅ 완료 |
| **Phase 4** | Week 6-7 | 추천 엔진, 멀티턴 대화, 세션 관리 | 🚀 배포 준비 |

---

## 핵심 시스템 아키텍처

### 1. 고수준 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    클라이언트 요청                              │
└────────────────────────────┬────────────────────────────────┘
                             │
                    FastAPI 애플리케이션
                    (app/main.py - 613줄)
                             │
        ┌────────┬─────────┬─────────────┐
        │        │         │             │
    요청처리   미들웨어   라우팅         예외처리
   (422ms avg)  메트릭   엔진           (429/500)
        │        │         │             │
        └────────┴─────────┴─────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
  설정관리      페르소나      Vertex AI
 (config.py)  라우터        연결
  (113줄)   (persona_router.py)  (LLM)
      │              │              │
      └──────────────┼──────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
    로깅시스템   캐싱       모니터링
   Google Cloud  (Redis)    Prometheus
    Logging              OpenTelemetry
```

### 2. 핵심 컴포넌트

#### **A. FastAPI 애플리케이션 (`app/main.py`)**
- 라인 수: 613줄
- 책임: 웹 서비스의 중앙 진입점
- 주요 기능:
  - Request/Response 처리
  - Rate Limiting (10 calls/60s)
  - CORS 미들웨어
  - 구조화된 로깅
  - 성능 모니터링 (>2.0s 경고)
  - Google Cloud Logging 통합

**주요 미들웨어:**
```python
- log_request_performance: 요청 처리 시간 측정
- CORS 미들웨어: 크로스 도메인 요청 처리
- Rate Limit: 요청 속도 제어
```

#### **B. 설정 관리 (`app/config.py`)**
- 라인 수: 113줄
- 책임: 환경별 설정 중앙화
- Pydantic 기반 타입 안전 설정

**설정 항목:**
```python
# 기본
- app_name: "내다AI Ion API"
- environment: development|production
- port: 8080

# Vertex AI (LLM)
- vertex_project_id: GCP 프로젝트 ID
- vertex_model: "gemini-1.5-flash-002"
- vertex_location: "us-central1"

# 레이트 제한
- rate_limit_calls: 10
- rate_limit_period: 60초

# Lumen 게이트웨이 (가드레일)
- lumen_gate_enabled: false (기본값)
- lumen_gateway_url: null

# 로깅
- use_cloud_logging: false (개발)
- log_level: "INFO"
```

#### **C. 페르소나 라우터 (`persona_router.py`)**
- 라인 수: 200+ 줄
- 책임: 파동키(resonance_key) 분석 → 최적 페르소나 선택

**4개 페르소나:**

| 페르소나 | 특성 | 강점 | 선호 톤 |
|---------|------|------|--------|
| **Lua** | 감성, 창의, 유연 | 감정 이해, 창의적 문제해결 | frustrated, playful, anxious |
| **Elro** | 논리, 체계, 명확 | 기술 아키텍처, 코드 설계 | curious, analytical, calm |
| **Riri** | 분석, 균형, 객관 | 메트릭 분석, 품질 검증 | analytical, calm, curious |
| **Nana** | 조율, 통합, 협업 | 팀 협업, 프로세스 관리 | urgent, confused, collaborative |

**라우팅 알고리즘:**
```python
1. 파동키 파싱: "frustrated-burst-seeking_advice"
   → tone: frustrated
   → pace: burst
   → intent: seeking_advice

2. 각 페르소나 매칭 점수 계산
   (유사도 기반: 0.0 ~ 1.0)

3. 1순위, 2순위 페르소나 선택

4. 신뢰도(confidence) 함께 반환
```

#### **D. 로깅 시스템 (`app/logging_setup.py`)**
- 라인 수: 150줄
- 책임: 구조화된 로깅
- 지원 채널:
  - 콘솔 로깅 (개발)
  - 파일 로깅 (프로덕션)
  - Google Cloud Logging (프로덕션)

---

## Phase별 역할과 구성

### **Phase 1: 환경 구성 (Week 1)**

**목표**: 개발 환경 구성 및 Vertex AI 통합

**주요 산출물:**
- `.venv` 가상환경
- `requirements.txt` 의존성
- `.env.example` 템플릿
- GCP 프로젝트 설정
- Vertex AI 모델 선택 (gemini-1.5-flash-002)

**배포 위치**: 로컬 개발 환경

---

### **Phase 2: 아키텍처 & 페르소나 라우팅 (Week 2)**

**목표**: 시스템 아키텍처 설계 및 페르소나 라우팅 구현

**주요 산출물:**
1. **FastAPI 기본 앱** (`app/main.py`)
   - 라우트: GET /, POST /chat
   - 미들웨어: CORS, Rate Limit, Logging

2. **페르소나 라우터** (`persona_router.py`)
   - 4개 페르소나 정의
   - 파동키 기반 라우팅
   - 신뢰도 점수 계산

3. **설정 관리** (`app/config.py`)
   - Pydantic BaseSettings
   - 환경별 설정 분리

4. **로깅 시스템** (`app/logging_setup.py`)
   - JSON 구조화 로깅
   - Google Cloud Logging 지원

**배포 위치**: 로컬 + Docker 테스트

---

### **Phase 3: Cloud Run 배포 & 멀티 페르소나 (Week 3-5)**

**목표**: GCP Cloud Run에 배포 및 멀티 페르소나 통합

**주요 산출물:**
1. **Docker 컨테이너화**
   - `Dockerfile`: 3단계 빌드 최적화
   - `docker-compose.yml`: 개발용 Compose

2. **Cloud Run 배포 설정**
   - GitHub Actions CI/CD
   - 자동 빌드 및 배포
   - 상태 체크 헬스 엔드포인트

3. **멀티 페르소나 통합**
   - Persona Pipeline 구현
   - 컨텍스트 메모리
   - 세션 관리

4. **모니터링 & 로깅**
   - Prometheus 메트릭
   - Google Cloud Logging
   - OpenTelemetry 계측

**배포 위치**: GCP Cloud Run

---

## 데이터 흐름

### 사용자 요청 → 페르소나 선택 → LLM 응답

```
1. 클라이언트 요청
   ├─ POST /api/v1/chat
   ├─ Body: {
   │   "message": "I'm frustrated with my code",
   │   "resonance_key": "frustrated-burst-seeking_advice"
   │ }
   └─ Headers: Content-Type, Authorization (필요시)

2. FastAPI 요청 처리
   ├─ Rate Limit 검증 (10 calls/60s)
   ├─ CORS 검증
   ├─ 요청 파싱 및 검증
   └─ 구조화된 로그 기록

3. 페르소나 라우팅
   ├─ 파동키 파싱
   │  └─ tone, pace, intent 추출
   ├─ 각 페르소나 매칭 점수 계산
   ├─ 1순위 페르소나 선택 (신뢰도 0.0~1.0)
   └─ 2순위 페르소나 기록 (폴백용)

4. Vertex AI LLM 호출
   ├─ 선택된 페르소나 프롬프트 스타일 적용
   ├─ 컨텍스트 메모리 (세션별) 추가
   ├─ Vertex AI API 호출
   │  └─ gemini-1.5-flash-002 모델
   └─ 응답 수신

5. 응답 처리 및 반환
   ├─ 응답 메타데이터 추가
   ├─ 세션 메모리 업데이트
   ├─ 메트릭 기록
   │  └─ 응답 시간, 토큰 사용량
   ├─ 구조화된 로그 기록
   └─ 클라이언트에 JSON 반환

6. 모니터링
   ├─ Prometheus 메트릭 수집
   ├─ Google Cloud Logging 전송
   └─ 성능 분석 (>2.0s 경고)
```

---

## 배포 구성

### 개발 (Local)
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Hot reload 활성화
- 모든 오류 상세 로깅

### 프로덕션 (Cloud Run)
```bash
# 환경 변수
ENVIRONMENT=production
USE_CLOUD_LOGGING=true
GCP_PROJECT_ID=<your-project-id>
VERTEX_PROJECT_ID=<your-project-id>

# 컨테이너 실행
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e USE_CLOUD_LOGGING=true \
  ion-api:latest
```

**특징:**
- 자동 헬스 체크
- 자동 스케일링
- 로드 밸런싱
- SSL/TLS 자동 적용

---

## 테스트 현황

### 전체 테스트 결과

```
총 테스트: 461개
✅ 414개 통과 (89.8%)
❌ 7개 실패 (1.5%)
⚠️ 36개 에러 (7.8%) - 의존성 이슈
⏭️ 4개 스킵 (0.9%)
```

### 카테고리별 분석

#### ✅ 통과한 테스트 (414개)

```
- 단위 테스트: 280개
- 통합 테스트: 100개
- E2E 테스트: 34개
```

**주요 성공 항목:**
- Persona Router 라우팅 정확도
- FastAPI 엔드포인트
- 설정 관리 및 환경 변수 파싱
- 로깅 및 모니터링
- 레이트 제한
- 에러 핸들링
- 입력 검증

#### ❌ 실패한 테스트 (7개)

| 테스트 | 원인 | 심각도 |
|-------|------|--------|
| `test_two_tier_cache_promotion` | Redis 모듈 미설치 | 🟡 중간 |
| `test_optimized_pipeline_cache_stats` | `tone` 파라미터 오류 | 🟡 중간 |
| `test_cache_hit_rate` | `tone` 파라미터 오류 | 🟡 중간 |
| `test_process_with_metadata` | 메타데이터 키 누락 | 🔴 높음 |
| `test_valid_resonance_key` | 유효성 검사 로직 오류 | 🔴 높음 |
| `test_parse_valid_resonance_key` | 톤 파싱 로직 오류 | 🔴 높음 |
| `test_valid_resonance_key_parsing` | 톤 파싱 로직 오류 | 🔴 높음 |

#### ⚠️ 에러 발생 (36개)

| 에러 유형 | 개수 | 원인 |
|----------|------|------|
| `AsyncClient` 호환성 | 31개 | httpx 버전 문제 |
| Sentry 임포트 | 5개 | sqlalchemy 의존성 |

---

## 알려진 이슈 및 개선 사항

### 🔴 높은 우선순위 (배포 전 필수)

#### 1. **파동키 파싱 로직 오류**
- **증상**: Resonance key validation 실패
- **원인**: 톤 파싱에서 기본값(CALM)으로 폴백
- **영향**: 페르소나 라우팅 정확도 감소
- **해결**: `/persona_router.py:180-200` 파싱 로직 재검토

**현재 로직:**
```python
def _parse_resonance_key(self, resonance_key: str):
    parts = resonance_key.split('-')
    # 기본값으로 폴백되고 있음
    tone = Tone(parts[0]) if len(parts) > 0 else Tone.CALM
    ...
```

**예상 수정:**
```python
# Enum 동적 생성 또는 매핑 테이블 추가
tone_map = {
    'frustrated': Tone.FRUSTRATED,
    'calm': Tone.CALM,
    'curious': Tone.CURIOUS,
    ...
}
```

#### 2. **메타데이터 전달 오류**
- **증상**: `test_process_with_metadata` 실패
- **원인**: Pipeline에서 메타데이터 키 누락
- **영향**: 컨텍스트 정보 손실
- **해결**: `/persona_system/pipeline.py` 메타데이터 전달 체크

#### 3. **AsyncClient 호환성**
- **증상**: 31개 보안 테스트 에러
- **원인**: httpx 버전 변경 (AsyncClient 인터페이스 변경)
- **영향**: 테스트 실행 불가
- **해결**:
  ```python
  # 기존 (v0.23 이하)
  async with AsyncClient(app=app) as client:

  # 신규 (v0.24+)
  async with AsyncClient(app=app, base_url="http://test") as client:
  ```

---

### 🟡 중간 우선순위 (배포 후 개선)

#### 1. **Redis 캐싱 모듈**
- **증상**: `test_two_tier_cache_promotion` 실패
- **원인**: `redis` 패키지 미설치
- **권장**: `pip install redis` 추가
- **이점**: 멀티턴 대화 응답 시간 개선 (예상 30% 단축)

#### 2. **Tone 파라미터 호환성**
- **증상**: Pipeline 최적화 모듈에서 `tone` 인자 오류
- **원인**: `ElroPersona.build_user_prompt()` 시그니처 미일치
- **해결**: 프롬프트 빌더 인터페이스 통일

---

## 배포 체크리스트 (Phase 4 전)

### 필수 항목

- [ ] 파동키 파싱 로직 수정 및 재테스트
- [ ] 메타데이터 전달 로직 수정 및 재테스트
- [ ] httpx AsyncClient 호환성 업데이트
- [ ] `redis` 패키지 의존성 추가 (선택)
- [ ] Sentry 모니터링 sqlalchemy 통합 (선택)

### 검증 항목

- [ ] 전체 테스트 실행: `pytest tests/ -v`
- [ ] 커버리지 확인: `pytest tests/ --cov=app`
- [ ] 성능 테스트: 평균 응답 시간 < 500ms
- [ ] 로드 테스트: 100 RPS 처리
- [ ] 보안 스캔: OWASP Top 10 검증

---

## 운영 가이드

### 로그 모니터링

```bash
# 로컬 개발
tail -f logs/app.log

# 프로덕션 (Google Cloud Logging)
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 --format json
```

### 메트릭 확인

```bash
# Prometheus 메트릭
curl http://localhost:8000/metrics

# 주요 메트릭
- http_request_duration_seconds
- http_request_total
- personality_router_latency_seconds
```

### 헬스 체크

```bash
# 기본 헬스 확인
GET /health

# 상세 헬스 확인
GET /health/detailed

# 응답 예시
{
  "status": "healthy",
  "timestamp": "2025-10-19T12:00:00Z",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "vertex_ai": "healthy",
    "logging": "healthy"
  }
}
```

---

## 다음 단계 (Phase 4)

Phase 4에서 다음 시스템들이 추가됩니다:

1. **추천 엔진** (Hybrid Ensemble)
   - 협업 필터링 (40%)
   - 콘텐츠 기반 (40%)
   - 페르소나 친화력 (20%)

2. **멀티턴 대화 엔진**
   - 컨텍스트 메모리 (TTL 기반)
   - 대화 히스토리 관리
   - P95 응답 시간 < 200ms

3. **세션 관리**
   - 분산 세션 스토어
   - 24시간 TTL
   - O(1) 조회 성능

4. **Canary 배포**
   - 5% 트래픽로 시작
   - 자동 헬스 체크
   - 자동 롤백 (1% 에러율 기준)

---

## 참고 자료

- [Phase 1-5 완료 보고서](./DELIVERY_PACKAGE.md)
- [CI/CD 가이드](./CI_CD_GUIDE.md)
- [배포 검증 체크리스트](./DEPLOYMENT_VERIFICATION_CHECKLIST.md)
- [E2E 테스트 가이드](./E2E_TEST_GUIDE.md)

---

**작성자**: Sena (AI 분석)
**승인자**: Lubit (프로젝트 아키텍트)
**최종 검토일**: 2025-10-19
