# 개발자 온보딩 가이드

## 👋 ION Mentoring 프로젝트에 오신 것을 환영합니다!

이 가이드는 새로운 팀 멤버가 ION Mentoring 프로젝트에 빠르게 참여할 수 있도록 돕습니다.

---

## 📋 필수 설정 (첫 날)

### 1단계: 환경 설정 (1시간)

```bash
# 1. 저장소 클론
git clone https://github.com/ion-mentoring/ion-api.git
cd ion-api

# 2. Python 3.11 설치 확인
python --version  # Python 3.11.x

# 3. 가상 환경 생성
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 또는: .venv\Scripts\activate  # Windows

# 4. 의존성 설치
pip install -e .[dev]

# 5. Pre-commit 훅 설정
pre-commit install

# 6. 데이터베이스 초기화 (개발용)
docker-compose up -d  # PostgreSQL, Redis 시작
python scripts/init_db.py
```

### 2단계: 프로젝트 구조 이해 (1시간)

```
ion-mentoring/
├── app/
│   ├── main.py                 # FastAPI 애플리케이션
│   ├── config.py               # 설정 관리
│   ├── secret_manager.py       # Secret Manager 통합
│   ├── metrics.py              # 메트릭 수집
│   └── logging_setup.py        # 로깅 설정
├── tests/
│   ├── unit/                   # 유닛 테스트 (80개)
│   ├── integration/            # 통합 테스트 (18개)
│   ├── e2e/                    # E2E 테스트 (23개)
│   └── security/               # 보안 테스트 (37개)
├── config/
│   ├── base.yaml               # 기본 설정
│   ├── dev.yaml                # 개발 환경
│   ├── test.yaml               # 테스트 환경
│   └── prod.yaml               # 프로덕션 환경
├── docs/                       # 문서 (23개 문서)
├── .github/workflows/          # CI/CD 파이프라인
└── pyproject.toml              # 프로젝트 설정
```

### 3단계: 첫 커밋 (30분)

```bash
# 1. 브랜치 생성
git checkout -b feat/my-feature

# 2. 코드 작성
# 예: app/main.py에 새 엔드포인트 추가

# 3. 테스트 작성
# tests/unit/test_my_feature.py

# 4. 테스트 실행
pytest tests/unit/test_my_feature.py -v

# 5. Pre-commit 훅 실행 (자동)
# Black, Ruff, MyPy가 자동으로 실행됨
git add .
git commit -m "feat: add new feature"

# 6. Push 및 PR
git push origin feat/my-feature
# GitHub에서 PR 생성
```

---

## 🚀 개발 워크플로우

### 일일 작업

```bash
# 아침: 최신 코드 받기
git pull origin develop
pip install -e .[dev]  # 신규 의존성 있을 수 있음

# 작업: 기능 개발
# 1. 이슈 선택: https://github.com/ion-mentoring/ion-api/issues
# 2. 브랜치 생성: git checkout -b feat/issue-123
# 3. 코드 작성
# 4. 테스트 작성
# 5. 테스트 실행: pytest -v
# 6. Pre-commit 훅 실행 (자동)
# 7. 커밋: git commit -m "feat: ..."

# 저녁: Push 및 PR
git push origin feat/issue-123
# GitHub에서 PR 생성 및 리뷰 받기
```

### 코드 리뷰

- PR은 최소 2명의 승인 필요
- CI/CD 파이프라인 통과 필수
- 모든 테스트 통과 필수
- 코드 커버리지 80% 이상 필수

---

## 🧪 테스트 작성 가이드

### 유닛 테스트

```python
# tests/unit/test_my_feature.py

import pytest
from app.my_feature import my_function

def test_my_function_success():
    """성공 케이스"""
    result = my_function(5)
    assert result == 10

def test_my_function_edge_case():
    """엣지 케이스"""
    result = my_function(0)
    assert result == 0

@pytest.mark.asyncio
async def test_async_function():
    """비동기 함수"""
    result = await my_async_function()
    assert result is not None
```

### 실행

```bash
# 모든 테스트 실행
pytest -v

# 특정 테스트만 실행
pytest tests/unit/test_my_feature.py -v

# 커버리지 포함
pytest --cov=app --cov-report=html

# 병렬 실행 (빠름)
pytest -n auto
```

---

## 📚 주요 문서

| 문서                                                 | 용도           | 읽기 시간 |
| ---------------------------------------------------- | -------------- | --------- |
| [README.md](../README.md)                            | 프로젝트 개요  | 10분      |
| [SETUP.md](../SETUP.md)                              | 개발 환경 설정 | 15분      |
| [TESTING.md](../TESTING.md)                          | 테스트 전략    | 20분      |
| API 스펙: [OpenAPI v2](../api/v2/openapi.yaml)       | API 사용법     | 30분      |
| [ARCHITECTURE.md](ARCHITECTURE.md)                   | 아키텍처       | 40분      |
| [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) | 문제 해결      | 필요시    |

---

## 🛠️ 자주 사용하는 명령어

```bash
# 개발 서버 실행
python -m uvicorn app.main:app --reload

# 테스트 실행
pytest -v --tb=short

# 포매팅 (Black)
black app/ tests/

# 린팅 (Ruff)
ruff check app/ tests/

# 타입 체크 (MyPy)
mypy app/

# 모든 검사 실행
pre-commit run --all-files

# 데이터베이스 마이그레이션
python scripts/migrate_db.py

# 로그 확인 (프로덕션)
gcloud logging read "resource.type=cloud_run_revision" --limit=100
```

---

## 🔑 주요 패턴

### 에러 처리

```python
# 좋은 예
from fastapi import HTTPException

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # 로직
        result = process_chat(request.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 로깅

```python
import logging

logger = logging.getLogger(__name__)

# 정보 로그
logger.info(f"Processing chat request: {user_id}")

# 경고 로그
logger.warning(f"Slow response: {response_time}ms")

# 에러 로그
logger.error(f"Failed to process: {str(e)}", exc_info=True)
```

### 비동기 처리

```python
import asyncio

async def async_operation():
    # 비동기 작업
    await database.query()
    await cache.set()

# 여러 비동기 작업 병렬 실행
results = await asyncio.gather(
    operation1(),
    operation2(),
    operation3()
)
```

---

## 📞 도움말

### 질문이 있을 때

1. 문서 검색: [docs/](../docs/)
2. 팀 Slack 채널: #development
3. Code owners에게 멘션: @dev-team
4. GitHub Issues: 이슈 제목으로 검색

### 일반적인 문제

| 문제                    | 해결                              |
| ----------------------- | --------------------------------- |
| "ModuleNotFoundError"   | `pip install -e .[dev]` 실행      |
| 테스트 실패             | `pytest -vv` 로 상세 로그 확인    |
| Pre-commit 실패         | `pre-commit run --all-files` 실행 |
| 데이터베이스 연결 안 됨 | `docker-compose up -d` 실행       |

---

## ✅ 온보딩 체크리스트

### 첫 주

- [ ] 환경 설정 완료
- [ ] 프로젝트 구조 이해
- [ ] 첫 커밋 완료
- [ ] 코드 리뷰 받음
- [ ] 팀원과 1:1 미팅
- [ ] Slack 채널 가입

### 첫 달

- [ ] 3개 이상 PR 통과
- [ ] 테스트 작성 경험
- [ ] API 문서 읽음
- [ ] 배포 프로세스 이해
- [ ] 팀 회의 참석

### 첫 분기

- [ ] 주요 기능 구현 완료
- [ ] 온콜 로테이션 포함
- [ ] 배포 경험 보유
- [ ] 팀에 기여 중

---

## 🎓 학습 자료

### 필수 지식

- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Docker](https://docs.docker.com/)

### 권장 학습

- [Google Cloud](https://cloud.google.com/docs)
- [Kubernetes](https://kubernetes.io/docs/)
- [Redis](https://redis.io/)
- [Git workflow](https://git-scm.com/docs)

---

## 🌟 성공 팁

1. **먼저 문서 읽기**: 질문하기 전에 문서 확인
2. **작은 커밋**: 큰 변경 대신 작은 커밋 여러 개
3. **테스트 먼저**: 코드 작성 전 테스트 설계
4. **도움 청하기**: 막히면 팀원에게 즉시 물어보기
5. **피드백 수용하기**: 코드 리뷰는 성장 기회

---

## 📅 다음 단계

이 가이드를 완료한 후:

1. **첫 이슈 선택**: [GitHub Issues](https://github.com/ion-mentoring/ion-api/issues)
2. **팀에 소개**: 팀 미팅에 참석
3. **코드 리뷰**: PR 제출 및 리뷰 받기
4. **배포 경험**: 첫 배포 참여

**환영합니다! 함께 멋진 프로젝트를 만들어봅시다! 🚀**
