# ION Mentoring 테스트 가이드

ION Mentoring 프로젝트의 포괄적인 테스트 전략 및 실행 방법을 설명합니다.

## 목차

1. [테스트 구조](#테스트-구조)
2. [테스트 실행](#테스트-실행)
3. [테스트 작성](#테스트-작성)
4. [커버리지 메저](#커버리지-메저)
5. [CI/CD 통합](#cicd-통합)
6. [문제 해결](#문제-해결)
7. [VS Code 확장 + HTTP Poller E2E](#vs-code-확장--http-poller-e2e)

---

## 테스트 구조

### 계층화된 테스트 아키텍처

```text
tests/
├── conftest.py              # 공유 fixtures 및 설정
├── unit/                    # Unit 테스트
│   ├── __init__.py
│   ├── test_config.py       # 설정 모듈
│   ├── test_validators.py   # 검증자
│   └── test_schemas.py      # Pydantic 스키마
├── integration/             # Integration 테스트
│   ├── __init__.py
│   ├── test_api_flow.py     # API 통합 흐름
│   └── test_persona_routing.py  # 페르소나 라우팅
├── e2e/                     # End-to-End 테스트 (선택)
│   └── test_complete_flow.py
├── fixtures/                # 테스트 데이터
│   ├── personas.json
│   └── responses.json
└── test_api.py              # 기존 API 테스트
```

### 테스트 계층별 특징

| 계층 | 범위 | Mock 사용 | 속도 | 목적 |
|------|------|---------|------|------|
| **Unit** | 개별 함수 | ✅ 많음 | ⚡ 빠름 | 논리 검증 |
| **Integration** | 컴포넌트 상호작용 | ⚠️ 중간 | 🚶 중간 | 흐름 검증 |
| **E2E** | 전체 시스템 | ❌ 없음 | 🐢 느림 | 사용자 시나리오 |

---

## 테스트 실행

### 기본 실행

```bash
# 모든 테스트 실행
pytest

# 상세 출력
pytest -v

# 매우 상세한 출력
pytest -vv

# 출력 캡처 안 함 (print 문 출력)
pytest -s
```

### 선택적 실행

```bash
# Unit 테스트만
pytest -m unit

# Integration 테스트만
pytest -m integration

# E2E 테스트 제외
pytest -m "not e2e"

# 느린 테스트 제외
pytest -m "not slow"

# 특정 파일만 테스트
pytest tests/unit/test_config.py

# 특정 클래스 테스트
pytest tests/unit/test_config.py::TestSettingsConfig

# 특정 함수 테스트
pytest tests/unit/test_config.py::TestSettingsConfig::test_settings_defaults

# 이름 패턴으로 필터
pytest -k "chat" -v  # "chat" 이름 포함 테스트만
pytest -k "not slow" -v  # "slow" 제외
```

### 병렬 실행 (속도 향상)

```bash
# pytest-xdist 필요
pip install pytest-xdist

# 병렬 실행 (CPU 코어 수 자동 감지)
pytest -n auto

# 4개 프로세스로 실행
pytest -n 4

# 속도 + 상세 출력
pytest -n auto -v
```

### 타임아웃 설정

```bash
# pytest-timeout 필요
pip install pytest-timeout

# 각 테스트에 30초 타임아웃
pytest --timeout=30

# 느린 테스트는 더 긴 타임아웃
pytest --timeout=30 -m "not slow"
pytest --timeout=60 -m slow
```

---

## 커버리지 메저

### 기본 커버리지 레포트

```bash
# 커버리지 측정
pytest --cov=app --cov=orchestration

# HTML 리포트 생성
pytest --cov=app --cov=orchestration --cov-report=html

# 터미널에 출력
pytest --cov=app --cov=orchestration --cov-report=term-missing
```

### 상세 커버리지 분석

```bash
# 특정 모듈만 커버리지 측정
pytest --cov=app.main --cov-report=html

# 커버리지 임계값 설정 (70% 미만이면 실패)
pytest --cov=app --cov-fail-under=70

# 커버리지 보고 및 조각 난 라인 표시
pytest --cov=app --cov-report=term-missing --cov-report=html

# XML 리포트 (CI/CD 통합용)
pytest --cov=app --cov-report=xml
```

### HTML 리포트 보기

```bash
# 생성된 리포트 열기
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\index.html  # Windows
```

### 커버리지 목표

**현재 목표:**
- 전체: 70%+
- app/main.py: 80%+
- app/config.py: 90%+
- 핵심 비즈니스 로직: 85%+

**개선 계획:**
- Week 1: 70% (기본 테스트)
- Week 2: 75% (Unit 테스트 확대)
- Week 3: 80% (Integration 테스트)
- Week 4: 85%+ (전체 커버리지)

---

## 테스트 작성

### Fixtures 사용

```python
# conftest.py에서 제공하는 기본 fixtures

# FastAPI 테스트 클라이언트
def test_something(client):
    response = client.get("/health")
    assert response.status_code == 200

# Mock 응답
def test_chat(client, mock_pipeline_response):
    with patch('app.main.pipeline') as mock_pipeline:
        mock_pipeline.process.return_value = mock_pipeline_response
        response = client.post("/chat", json={"message": "테스트"})
        assert response.status_code == 200

# 테스트 메시지
def test_various_messages(client, test_messages):
    for message_type, message in test_messages.items():
        # 각 메시지 타입 테스트
        pass
```

### 테스트 마커

```python
# Unit 테스트
@pytest.mark.unit
def test_config_loading():
    pass

# Integration 테스트
@pytest.mark.integration
def test_api_flow():
    pass

# 느린 테스트 (선택적 실행)
@pytest.mark.slow
def test_load_behavior():
    pass

# Async 테스트
@pytest.mark.asyncio
async def test_async_function():
    pass
```

### Mock 사용 예제

```python
from unittest.mock import patch, MagicMock

# Mock 객체 생성
@patch('app.main.pipeline')
def test_with_mock(mock_pipeline, client):
    # Mock 설정
    mock_pipeline.process.return_value = expected_response

    # 테스트
    response = client.post("/chat", json={"message": "테스트"})

    # 검증
    mock_pipeline.process.assert_called_once()
    assert response.status_code == 200
```

### 예외 처리 테스트

```python
# 예외 발생 테스트
def test_exception_handling(client):
    with patch('app.main.pipeline') as mock_pipeline:
        mock_pipeline.process.side_effect = Exception("Error")

        response = client.post("/chat", json={"message": "테스트"})

        assert response.status_code == 500

# 특정 예외 테스트
def test_timeout_error(client):
    with patch('app.main.pipeline') as mock_pipeline:
        mock_pipeline.process.side_effect = TimeoutError()

        response = client.post("/chat", json={"message": "테스트"})

        assert response.status_code == 504
```

---

## CI/CD 통합

### GitHub Actions 설정

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev,test]"

      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Pre-commit Hook

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        stages: [commit]
```

---

## 문제 해결

### 테스트 실패 디버깅

```bash
# 자세한 실패 메시지
pytest -vv --tb=long

# 첫 번째 실패에서 멈춤
pytest -x

# 마지막 N개 실패 재실행
pytest --lf  # last failed
pytest --ff  # failed first

# PDB 디버거 진입
pytest --pdb

# 실패 시 PDB 진입
pytest --pdb -s
```

### 메모리 누수 감지

```bash
# pytest-memprof 필요
pip install pytest-memprof

# 메모리 사용 추적
pytest --memprof
```

### 성능 프로파일링

```bash
# pytest-profiling 필요
pip install pytest-profiling

# 성능 프로파일링
pytest --profile

# 출력 파일
pytest --profile-svg
```

### 일반적인 문제

**문제: `ModuleNotFoundError`**

```bash
# 해결: PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

**문제: `pytest.ini` 찾을 수 없음**

```bash
# 해결: pyproject.toml에 설정 있음
# 또는 pytest.ini 생성
cat > pytest.ini << EOF
[pytest]
testpaths = tests
python_files = test_*.py
EOF
```

**문제: Fixture 찾을 수 없음**

```bash
# 해결: conftest.py 위치 확인
# tests/conftest.py 또는 tests/*/conftest.py
```

---

## VS Code 확장 + HTTP Poller E2E

로컬 FastAPI 작업 큐와 VS Code 확장(HTTP Poller)을 연결해 End-to-End 동작을 검증하는 절차입니다. Windows + PowerShell 기준입니다.

### 빠른 요약

- 서버: http://127.0.0.1:8091/api (GET /health = 200)
- 확장: VS Code Extension Development Host에서 자동 활성(onStartupFinished) → "Gitko HTTP Poller" 출력 채널 확인
- 큐: GET /api/tasks/next는 작업이 없으면 204, 있으면 task_id 포함 JSON 반환
- 결과: POST /api/tasks/{task_id}/result 로 { success, data?, error? } 제출 → /api/results에서 확인

### 사전 준비

- FastAPI 작업 큐 서버 실행 상태 확인
- 엔드포인트 요약
  - GET /api/health → 200 OK
  - GET /api/tasks/next → 200(작업 있음) 또는 204(없음)
  - POST /api/tasks/create { type, data }
  - POST /api/tasks/{task_id}/result { success, data?, error? }
  - GET /api/results, GET /api/results/{task_id}

- 워크스페이스 설정(.vscode/settings.json 권장)
- gitko.enableHttpPoller: true
- gitko.httpApiBase: "http://127.0.0.1:8091/api"
- gitko.httpPollingInterval: 2000
- gitko.enableComputerUseOverHttp: true
- gitko.minUiActionIntervalMs: 250

- 한국어/영어 입력 호환성
- 자동 입력/타이핑이 필요한 작업은 IME 전환 상태에 따라 지연이 있을 수 있습니다. UI 타이핑 간격(minUiActionIntervalMs)을 200~300ms로 유지하고, 한/영 전환 키 충돌을 피하세요.

### 실행 절차

- VS Code 확장 구동
- 방법 A: Run and Debug에서 "Extension" 구성 선택 후 F5 → Extension Development Host가 뜨면 자동 활성
- 방법 B: 제공되는 전용 Task가 있을 경우 터미널 > Run Task에서 실행(예: "VS Code: Start Gitko Extension (Dev Host)")

- 출력 채널 확인
- View > Output에서 드롭다운으로 "Gitko HTTP Poller" 선택 → 폴링 시작/작업 처리 로그 확인

- 헬스/큐/결과 점검(선택)
- 헬스: GET /api/health → 200
- 큐 소모: 작업 생성 후 일정 시간 내 queue_size 감소(폴러 활성 시)
- 결과 누적: /api/results 또는 /api/results/{task_id}에서 success=true, data 확인

- 샘플 작업 유형
- ping → pong 반환 검증
- computer_use.scan → OCR/요소 스캔 결과 확인
- computer_use.find/click/type → 안전 쿨다운(minUiActionIntervalMs) 준수 확인

### 성공 기준(체크리스트)

- [ ] 확장 Development Host에서 "Gitko HTTP Poller" 로그가 주기적으로 폴링 로그를 출력한다.
- [ ] 작업 생성 시 GET /api/tasks/next 응답이 200으로 전환되고 task_id가 포함된다.
- [ ] 결과 제출 후 /api/results(또는 /api/results/{task_id})에서 success=true를 확인한다.
- [ ] computer_use.scan 결과가 정상(JSON)으로 수집된다.

### 통합 모니터링 연동(권장)

- 터미널 > Run Task에서 다음을 순서대로 활용하면 상태를 한눈에 점검 가능:
  - "Monitoring: Unified Dashboard (Adaptive)" 또는 "Monitoring: Unified Dashboard (Alert + Log)"
  - "Lumen: Quick Health Probe" (루멘 게이트웨이 응답 확인)
  - "VS Code: Watch Orchestrator Status" (오케스트레이터 상태 파일 모니터)

### 일반 이슈 및 해결

- VSIX 설치 후 활성화 문제가 있는 경우
- Development Host(F5 또는 전용 Task)로 우선 검증하세요. 동작이 정상이라면 빌드/패키징(VSIX) 절차를 재검토하고, 설치된 확장 캐시를 초기화 후 재설치합니다.

- 큐가 소모되지 않는 경우
- 확장 설정 gitko.httpApiBase 경로에 /api 접미사가 포함되어 있는지 확인
- 서버 측 /api/tasks/next가 204만 반환되는지 확인(작업 미생성 상태)
- 프록시/방화벽(로컬 127.0.0.1:8091) 간섭 여부 확인

- computer_use.* 작업이 느리거나 실패
- 안전 쿨다운(minUiActionIntervalMs) 값을 250~400ms로 상향 조정
- 포커스가 VS Code(또는 대상 앱) 창에 있는지 확인
- 한/영(IM E) 전환 또는 키보드 후킹 프로그램과 충돌 여부 확인

- 한글 입력시 깨짐/지연
- OS 입력기 설정에서 고급 텍스트 서비스/자동 교정 옵션을 줄이고, 필요한 경우 영문 입력 후 변환 방식으로 우회

### 추가 참고

- Python 통합 테스트는 "Python: Run All Tests (repo venv)" Task로 빠르게 재현 가능
- 대시보드 산출물: outputs/monitoring_report_latest.md, outputs/monitoring_metrics_latest.json, outputs/monitoring_dashboard_latest.html
- 작업 큐 API 계약은 상단 "사전 준비"의 엔드포인트 목록을 기준으로 검증합니다.

## 다음 단계

### 테스트 확대

1. **Unit 테스트 추가**
   - Validators 테스트
   - Schemas 테스트
   - 유틸리티 함수 테스트

2. **Integration 테스트 확대**
   - 메모리 저장소 테스트
   - RAG 기능 테스트
   - 백엔드 연동 테스트

3. **E2E 테스트 추가**
   - 전체 사용자 시나리오
   - 다양한 페르소나 테스트

### 테스트 최적화

1. **실행 속도 향상**
   - 병렬 실행 활용
   - 느린 테스트 병렬화 불가 표시

2. **커버리지 목표 달성**
   - 목표: 85%+ (3주 내)
   - 단계별 증가 계획

---

## 참고 문서

- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-cov 문서](https://pytest-cov.readthedocs.io/)
- [unittest.mock 문서](https://docs.python.org/3/library/unittest.mock.html)
- [FastAPI 테스팅](https://fastapi.tiangolo.com/tutorial/testing/)

---

**테스트 작성 시 팀 규칙:**
1. 모든 새로운 기능에 테스트 작성
2. 버그 수정 시 회귀 테스트 추가
3. 커버리지 70% 이상 유지
4. Unit 테스트 먼저, Integration 나중
5. Mock을 과용하지 않기
