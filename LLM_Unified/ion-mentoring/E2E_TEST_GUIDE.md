# E2E (End-to-End) 테스트 가이드

ION Mentoring 애플리케이션의 완전한 사용자 여정을 테스트하는 E2E 테스트 가이드입니다.

## 목차

1. [개요](#개요)
2. [테스트 설정](#테스트-설정)
3. [테스트 실행](#테스트-실행)
4. [테스트 시나리오](#테스트-시나리오)
5. [성능 검증](#성능-검증)
6. [CI/CD 통합](#cicd-통합)
7. [문제 해결](#문제-해결)

---

## 개요

### E2E 테스트란?

E2E(End-to-End) 테스트는 애플리케이션의 **완전한 사용자 여정**을 테스트합니다:

```
HTTP Request → Validation → Persona Routing → AI Response → HTTP Response
```

### 왜 E2E 테스트가 중요한가?

| 항목 | Unit 테스트 | Integration 테스트 | E2E 테스트 |
|------|-----------|-------------------|----------|
| **범위** | 단일 함수/클래스 | 모듈 간 상호작용 | 전체 시스템 |
| **리소스** | 빠름 (ms) | 중간 (초) | 느림 (초) |
| **커버리지** | 높음 (70-90%) | 중간 (50-70%) | 낮음 (10-30%) |
| **신뢰도** | 낮음 | 중간 | 높음 |
| **사용자 경험** | 반영 안 함 | 부분 반영 | 완전 반영 |

### 테스트 피라미드

```
        ┌─────────────┐
        │     E2E     │  ← 10% (18개 테스트)
        │  (9-15분)   │
        └─────────────┘
      ┌─────────────────┐
      │  Integration    │  ← 30% (20개 테스트)
      │    (2-3분)      │
      └─────────────────┘
    ┌───────────────────────┐
    │       Unit Tests      │  ← 60% (80개 테스트)
    │       (30-60초)       │
    └───────────────────────┘
```

---

## 테스트 설정

### 사전 요구사항

```bash
# Python 3.11+
python --version

# 의존성 설치
pip install -e ".[dev,test]"

# 필수 패키지 확인
pip show pytest pytest-asyncio httpx
```

### 테스트 환경 설정

```bash
# 테스트 환경 변수 설정
export ENVIRONMENT=test
export CONFIG_PATH=config/test.yaml
export BACKEND_TYPE=mock
export LOG_LEVEL=WARNING

# 또는 .env.test 파일 생성
cat > .env.test << EOF
ENVIRONMENT=test
CONFIG_PATH=config/test.yaml
BACKEND_TYPE=mock
LOG_LEVEL=WARNING
EOF
```

### 디렉토리 구조

```
tests/
├── __init__.py
├── conftest.py              # 공유 fixtures
├── unit/                    # 단위 테스트
│   ├── test_config.py
│   ├── test_logging.py
│   └── __init__.py
├── integration/             # 통합 테스트
│   ├── test_api_flow.py
│   └── __init__.py
└── e2e/                     # E2E 테스트 (새로 추가)
    ├── __init__.py
    └── test_complete_user_journeys.py
```

---

## 테스트 실행

### 1. 모든 E2E 테스트 실행

```bash
# 기본 실행
pytest tests/e2e/ -v

# 상세 출력과 함께
pytest tests/e2e/ -vv --tb=short

# 실시간 출력 모드
pytest tests/e2e/ -v -s
```

### 2. 특정 테스트 클래스 실행

```bash
# Happy Path 테스트만
pytest tests/e2e/test_complete_user_journeys.py::TestHappyPathJourneys -v

# 입력 검증 테스트만
pytest tests/e2e/test_complete_user_journeys.py::TestInputValidationJourneys -v

# 성능 테스트만
pytest tests/e2e/test_complete_user_journeys.py::TestPerformanceJourneys -v

# 속도 제한 테스트만
pytest tests/e2e/test_complete_user_journeys.py::TestRateLimitingJourneys -v
```

### 3. 특정 테스트 함수 실행

```bash
# 특정 테스트 하나만
pytest tests/e2e/test_complete_user_journeys.py::TestHappyPathJourneys::test_emotional_support_journey_lua -v

# 정규식으로 매칭
pytest tests/e2e/ -k "emotional" -v
pytest tests/e2e/ -k "persona" -v
```

### 4. 마커로 실행

```bash
# E2E 마커만 (자동으로 적용됨)
pytest -m e2e -v

# E2E + 비동기만
pytest -m "e2e and asyncio" -v

# E2E 제외
pytest -m "not e2e" -v
```

### 5. 성능 및 커버리지 측정

```bash
# 커버리지 함께 측정
pytest tests/e2e/ --cov=app --cov-report=html --cov-report=term-missing

# 성능 정보 출력
pytest tests/e2e/ -v --durations=10

# 느린 테스트 식별
pytest tests/e2e/ -v --durations=5 --tb=line
```

### 6. 병렬 실행 (빠른 테스트)

```bash
# 4개 프로세스로 병렬 실행
pytest tests/e2e/ -n 4 -v

# 자동으로 CPU 코어 수만큼
pytest tests/e2e/ -n auto -v
```

### 7. 선택적 실행

```bash
# 실패한 테스트만 재실행
pytest tests/e2e/ --lf -v

# 마지막 테스트 이후 실패한 것만
pytest tests/e2e/ --ff -v

# 처음 3개 실패 시 중단
pytest tests/e2e/ -x --maxfail=3 -v
```

---

## 테스트 시나리오

### E2E 테스트 매트릭스 (18개)

#### 1. Happy Path Journeys (4개)

| ID | 이름 | 입력 | 예상 페르소나 | 목표 |
|----|------|------|-------------|------|
| E2E-001 | 감정 지원 | "정말 답답해요!" | Lua | 감정적 지원 라우팅 |
| E2E-002 | 기술 질문 | "함수 복잡도는?" | Elro/Riri | 기술적 라우팅 |
| E2E-003 | 데이터 분석 | "데이터 분석해주세요" | Riri | 분석 라우팅 |
| E2E-004 | 프로젝트 조율 | "급히 조율해요!" | Nana | 조율 라우팅 |

```bash
# Happy Path 테스트 실행
pytest tests/e2e/test_complete_user_journeys.py::TestHappyPathJourneys -v
```

#### 2. Input Validation Journeys (5개)

| ID | 이름 | 입력 | 예상 상태 | 목표 |
|----|------|------|---------|------|
| E2E-005 | 빈 메시지 | "" | 400 | 검증 오류 |
| E2E-006 | 공백만 | "   " | 400 | 검증 오류 |
| E2E-007 | 너무 길음 | "A" * 1001 | 400 | 길이 검증 |
| E2E-008 | 특수 문자 | "@#$%^&*()" | 200 | 정상 처리 |
| E2E-009 | 이모지 | "😊 테스트" | 200 | 유니코드 처리 |

```bash
# 입력 검증 테스트 실행
pytest tests/e2e/test_complete_user_journeys.py::TestInputValidationJourneys -v
```

#### 3. Rate Limiting (1개)

| ID | 이름 | 시나리오 | 예상 결과 |
|----|------|--------|----------|
| E2E-010 | 속도 제한 | 분당 15개 요청 | 첫 10개: 200, 이후: 429 |

```bash
# 속도 제한 테스트 실행
pytest tests/e2e/test_complete_user_journeys.py::TestRateLimitingJourneys -v
```

#### 4. Error Handling (3개)

| ID | 이름 | 입력 | 예상 상태 |
|----|------|------|---------|
| E2E-011 | 필드 누락 | {"text": "..."} | 400 |
| E2E-012 | 잘못된 JSON | "{invalid}" | 422 |
| ... | 기타 에러 | ... | 4xx/5xx |

```bash
# 에러 처리 테스트 실행
pytest tests/e2e/test_complete_user_journeys.py::TestErrorHandlingJourneys -v
```

#### 5. Persona Routing (1개)

| ID | 이름 | 목표 |
|----|------|------|
| E2E-013 | 모든 페르소나 라우팅 | 4개 페르소나 모두 테스트 |

```bash
# 페르소나 라우팅 테스트
pytest tests/e2e/test_complete_user_journeys.py::TestPersonaRoutingJourneys -v
```

#### 6. Multi-Turn Conversation (1개)

| ID | 이름 | 목표 |
|----|------|------|
| E2E-014 | 다중 턴 대화 | 페르소나 전환 검증 |

```bash
# 다중 턴 테스트
pytest tests/e2e/test_complete_user_journeys.py::TestMultiTurnConversationJourneys -v
```

#### 7. Performance (2개)

| ID | 이름 | 목표 |
|----|------|------|
| E2E-016 | 응답 시간 SLO | P95 < 2초 |
| E2E-017 | 동시 요청 | 5개 동시 처리 |

```bash
# 성능 테스트 실행
pytest tests/e2e/test_complete_user_journeys.py::TestPerformanceJourneys -v
```

#### 8. API Documentation (2개)

| ID | 이름 | 목표 |
|----|------|------|
| E2E-018-a | Swagger 문서 | /docs 접근 가능 |
| E2E-018-b | ReDoc 문서 | /redoc 접근 가능 |

```bash
# 문서 테스트
pytest tests/e2e/test_complete_user_journeys.py::TestDocumentationJourneys -v
```

---

## 성능 검증

### 성능 메트릭

```yaml
Response Time:
  P50: < 1초      # 50% 요청
  P95: < 2초      # 95% 요청
  P99: < 5초      # 99% 요청

Throughput:
  Health Check: < 100ms
  Chat Endpoint: < 2초 (P95)

Concurrency:
  Simultaneous Users: 100+
  Rate Limit: 10 req/min

Error Rate:
  Threshold: < 1%
```

### 성능 테스트 실행

```bash
# 응답 시간 측정과 함께 실행
pytest tests/e2e/test_complete_user_journeys.py::TestPerformanceJourneys -v --durations=10

# CSV 출력으로 저장
pytest tests/e2e/ -v --csv=test_results.csv
```

### 성능 분석

```bash
# X-Process-Time 헤더 확인
curl -v http://localhost:8000/health

# 응답 예시
# < X-Process-Time: 0.025
```

---

## CI/CD 통합

### GitHub Actions 통합

```yaml
# .github/workflows/test.yml에 E2E 테스트 추가

- name: Run E2E Tests
  run: |
    pytest tests/e2e/ -v \
      --cov=app \
      --cov-report=xml \
      --tb=short

- name: Upload E2E Results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: e2e-test-results
    path: test_results.xml
```

### 배포 전 E2E 체크

```bash
# 배포 전 체크리스트
#!/bin/bash

echo "🧪 E2E 테스트 실행 중..."
pytest tests/e2e/ -v --tb=short

if [ $? -eq 0 ]; then
  echo "✅ E2E 테스트 통과!"
  echo "🚀 배포 준비 완료"
  exit 0
else
  echo "❌ E2E 테스트 실패!"
  echo "🛑 배포 중단"
  exit 1
fi
```

### 스테이징 배포 후 스모크 테스트

```bash
# 스테이징에서만 실행 (빠른 검증)
pytest tests/e2e/test_complete_user_journeys.py::TestHappyPathJourneys -v
pytest tests/e2e/test_complete_user_journeys.py::TestHealthCheckJourneys -v
```

---

## 문제 해결

### 테스트 실패 원인 및 해결

#### 1. "Connection refused" 오류

```
ERROR: Connection refused to http://test
```

**원인**: 애플리케이션이 실행 중이지 않음

**해결**:
```bash
# 애플리케이션 시작
python -m app.main

# 또는 테스트만 실행 (자동으로 app 시작)
pytest tests/e2e/ -v
```

#### 2. "Rate limit exceeded" 테스트 실패

```
AssertionError: Expected rate limit (429) after 10 requests
```

**원인**: 속도 제한이 비활성화되어 있음

**해결**:
```python
# config/test.yaml에서 확인
rate_limit_enabled: true
rate_limit_requests: 10
rate_limit_period: 60
```

#### 3. "Persona routing" 테스트 실패

```
AssertionError: personality_used was "Nana", expected "Lua"
```

**원인**: 라우팅 알고리즘이 다르게 작동

**해결**:
```bash
# Mock 백엔드 설정 확인
export BACKEND_TYPE=mock

# 테스트 로그 상세 출력
pytest tests/e2e/ -vv -s
```

#### 4. "Timeout" 에러

```
TimeoutError: Test timed out after 30 seconds
```

**원인**: 응답이 너무 오래 걸림

**해결**:
```bash
# pytest-timeout 설정 확인
pytest tests/e2e/ -v --timeout=60

# 또는 conftest.py에서:
@pytest.mark.timeout(60)
def test_something():
    pass
```

#### 5. Unicode 인코딩 오류

```
UnicodeEncodeError: 'utf-8' codec can't encode character
```

**원인**: 한글/이모지 처리 오류

**해결**:
```bash
# 환경 변수 설정
export PYTHONIOENCODING=utf-8

# 또는 pytest 실행
PYTHONIOENCODING=utf-8 pytest tests/e2e/ -v
```

### 디버깅 팁

#### 1. 상세 로그 출력

```bash
# -s 옵션으로 print 문 보기
pytest tests/e2e/ -v -s

# -vv로 최대 상세 출력
pytest tests/e2e/ -vv

# 로그 레벨 조정
RUST_LOG=debug pytest tests/e2e/ -v
```

#### 2. 실패한 테스트 디버깅

```bash
# 실패 시 debugger 진입
pytest tests/e2e/ --pdb

# 실패 후 debugger 진입
pytest tests/e2e/ --pdbcls=IPython.terminal.debugger:TerminalPdb
```

#### 3. 특정 응답 검증

```python
# 테스트 코드에서
response = await async_client.post("/chat", json={"message": "test"})
print(f"Status: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"Body: {response.json()}")
```

#### 4. 성능 프로파일링

```bash
# cProfile로 성능 분석
python -m cProfile -s cumtime -m pytest tests/e2e/ -v

# 메모리 프로파일링
python -m memory_profiler test_script.py
```

---

## 베스트 프랙티스

### 1. 테스트 작성 가이드

```python
# ✅ 좋은 예시
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_happy_path_with_clear_name(self, async_client):
    """
    E2E-001: 감정적 지원 요청 처리

    사용자가 감정적으로 도움을 요청하면
    Lua 페르소나가 응답해야 합니다.
    """
    # Arrange - 테스트 데이터 준비
    request_data = {"message": "정말 답답해요!"}

    # Act - 실제 동작
    response = await async_client.post("/chat", json=request_data)
    data = response.json()

    # Assert - 결과 검증
    assert response.status_code == 200
    assert data["persona_used"] == "Lua"
    assert data["confidence"] > 0.7

# ❌ 나쁜 예시
async def test_1(self, async_client):
    response = await async_client.post("/chat", json={"message": "test"})
    assert response.status_code == 200
```

### 2. 테스트 독립성

```python
# ✅ 독립적인 테스트
# 각 테스트는 다른 테스트에 의존하지 않음
async def test_scenario_1(self, async_client):
    response = await async_client.post("/chat", json={"message": "테스트1"})
    assert response.status_code == 200

async def test_scenario_2(self, async_client):
    response = await async_client.post("/chat", json={"message": "테스트2"})
    assert response.status_code == 200

# ❌ 의존성이 있는 테스트
async def test_setup(self, async_client):
    self.data = await async_client.post(...)

async def test_uses_setup_data(self):
    # test_setup이 먼저 실행되어야 함
    assert self.data is not None
```

### 3. 유지보수성

```python
# ✅ 재사용 가능한 Fixture
@pytest.fixture
def standard_request():
    return {"message": "테스트 메시지"}

async def test_1(self, async_client, standard_request):
    response = await async_client.post("/chat", json=standard_request)
    assert response.status_code == 200

async def test_2(self, async_client, standard_request):
    response = await async_client.post("/chat", json=standard_request)
    assert "persona_used" in response.json()
```

### 4. 성능 최적화

```bash
# 병렬 실행으로 시간 단축
pytest tests/e2e/ -n auto -v

# 느린 테스트만 건너뛰기
pytest tests/e2e/ -m "not slow" -v

# 타임아웃 설정
pytest tests/e2e/ --timeout=30 -v
```

---

## 실행 예시

### 전체 E2E 테스트 스위트 실행

```bash
$ pytest tests/e2e/ -v
========================= test session starts ==========================
platform win32 -- Python 3.11.0, pytest-8.4.2
plugins: asyncio-0.21.0, cov-4.1.0, timeout-2.2.0
collected 32 items

tests/e2e/test_complete_user_journeys.py::TestHappyPathJourneys::test_emotional_support_journey_lua PASSED [ 3%]
tests/e2e/test_complete_user_journeys.py::TestHappyPathJourneys::test_technical_query_journey_elro PASSED [ 6%]
tests/e2e/test_complete_user_journeys.py::TestInputValidationJourneys::test_empty_message_validation PASSED [10%]
tests/e2e/test_complete_user_journeys.py::TestRateLimitingJourneys::test_rate_limit_exceeded PASSED [13%]
tests/e2e/test_complete_user_journeys.py::TestPerformanceJourneys::test_response_time_slo_p95 PASSED [16%]
...
========================= 32 passed in 2m 45s ==========================

✅ 모든 E2E 테스트 통과!
```

### 성능 측정과 함께 실행

```bash
$ pytest tests/e2e/ -v --durations=5
...
======================== slowest 5 durations ==========================
2.34s call     tests/e2e/test_complete_user_journeys.py::TestPerformanceJourneys::test_concurrent_requests_handling
1.92s call     tests/e2e/test_complete_user_journeys.py::TestPerformanceJourneys::test_response_time_slo_p95
1.45s call     tests/e2e/test_complete_user_journeys.py::TestRateLimitingJourneys::test_rate_limit_exceeded
...
```

---

## 다음 단계

### 즉시 (이번 주)
- [ ] 모든 E2E 테스트 실행 및 검증
- [ ] CI/CD 파이프라인에 E2E 테스트 추가
- [ ] 스테이징 환경에서 E2E 스모크 테스트 실행

### 단기 (2-3주)
- [ ] 성능 프로파일링 및 최적화
- [ ] 부하 테스트 (Locust) 추가
- [ ] 카나리 배포 E2E 테스트

### 중기 (1개월)
- [ ] End-to-End 사용자 시나리오 확대 (50+)
- [ ] 자동 성능 회귀 테스트
- [ ] 프로덕션 모니터링과 E2E 테스트 통합

---

## 참고 문서

- [Pytest 공식 문서](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI 테스팅](https://fastapi.tiangolo.com/advanced/testing-events/)
- [httpx 비동기 클라이언트](https://www.python-httpx.org/)

---

**문제가 있나요?** [문제 해결 섹션](#문제-해결)을 참고하거나 팀에 문의하세요.

**마지막 업데이트**: 2025-10-18
**작성자**: Claude Code
**버전**: 0.1.0
