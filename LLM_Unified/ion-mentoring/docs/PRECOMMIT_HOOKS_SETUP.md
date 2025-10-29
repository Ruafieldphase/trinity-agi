# Pre-commit Hooks 설정 가이드 (3시간 작업)

## 📋 개요

**목표**: Git 커밋 전 자동으로 코드 품질 검사
**도구**: `pre-commit` 프레임워크 + Black, Ruff, MyPy, 기타 훅
**이점**: 일관된 코드 스타일, 버그 조기 발견, CI/CD 파이프라인 시간 단축

---

## 🎯 Pre-commit 훅 목록

| 훅 | 역할 | 속도 |
|-------|------|------|
| **trailing-whitespace** | 줄 끝 공백 제거 | ⚡ 빠름 |
| **end-of-file-fixer** | 파일 끝 개행 정리 | ⚡ 빠름 |
| **check-yaml** | YAML 문법 검사 | ⚡ 빠름 |
| **check-json** | JSON 문법 검사 | ⚡ 빠름 |
| **check-toml** | TOML 문법 검사 | ⚡ 빠름 |
| **check-added-large-files** | 큰 파일 커밋 방지 | ⚡ 빠름 |
| **Black** | 코드 포맷팅 | 🔸 중간 |
| **Ruff** | 린팅 (PEP8 등) | 🔸 중간 |
| **MyPy** | 타입 검사 | 🔴 느림 |
| **Pytest** | 테스트 실행 | 🔴 느림 |

---

## 🛠️ 설치 및 설정

### Step 1: pre-commit 설치

```bash
# pip로 설치
pip install pre-commit

# 또는 pyproject.toml에 추가
# [project.optional-dependencies]
# dev = ["pre-commit>=3.0.0", ...]

# 버전 확인
pre-commit --version
```

### Step 2: 구성 파일 생성

**파일**: `.pre-commit-config.yaml` (프로젝트 루트)

```yaml
# Pre-commit 훅 설정
# 커밋 전 자동으로 실행되는 검사 목록

repos:
  # ============================================================================
  # 기본 검사 (빠름) - 모든 커밋에 필수
  # ============================================================================
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      # 줄 끝 공백 제거
      - id: trailing-whitespace
        name: "Trim trailing whitespace"
        args: [--markdown-template='{original}']  # Markdown 공백 보존

      # 파일 끝 개행 확인
      - id: end-of-file-fixer
        name: "Fix end of file"

      # YAML 문법 검사
      - id: check-yaml
        name: "Check YAML syntax"
        args: ['--unsafe']  # 커스텀 태그 허용

      # JSON 문법 검사
      - id: check-json
        name: "Check JSON syntax"
        exclude: "^\\.vscode/"  # VSCode 설정 제외

      # TOML 문법 검사
      - id: check-toml
        name: "Check TOML syntax"

      # 큰 파일 커밋 방지 (기본값: 500KB)
      - id: check-added-large-files
        name: "Check for large files"
        args: ['--maxkb=1000']  # 1MB 이상 파일 검사

      # 파일 실행 권한 검사
      - id: check-executable-scripts
        name: "Check executable scripts"

      # Debugger import 확인
      - id: debug-statements
        name: "Check for debugger imports"

  # ============================================================================
  # Black - 코드 포매팅 (필수)
  # ============================================================================
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        name: "Black code formatter"
        language_version: python3.11
        args: ['--line-length=100']  # 한 줄 최대 100자

  # ============================================================================
  # Ruff - 린팅 (필수)
  # ============================================================================
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      # Lint 검사
      - id: ruff
        name: "Ruff lint"
        args: [
          '--select=E,W,F,I,N,UP,B,A,C4,SIM,PIE',  # 선택할 규칙
          '--ignore=E501,W503',  # 무시할 규칙 (라인 길이는 Black이 처리)
          '--line-length=100'
        ]
        stages: [commit]

      # Auto-fix 적용
      - id: ruff-format
        name: "Ruff format"
        args: ['--line-length=100']
        stages: [commit]

  # ============================================================================
  # MyPy - 타입 검사 (권장, 느림)
  # ============================================================================
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        name: "MyPy type checking"
        additional_dependencies: [
          'pydantic>=2.0',
          'fastapi',
          'types-pyyaml',
          'types-python-dateutil'
        ]
        args: [
          '--ignore-missing-imports',
          '--strict',  # 엄격한 타입 검사
          '--warn-unused-ignores',
          '--no-implicit-optional'
        ]
        stages: [commit]
        exclude: '^tests/'  # 테스트 파일 제외

  # ============================================================================
  # Pytest - 유닛 테스트 (권장, 가장 느림)
  # ============================================================================
  - repo: local
    hooks:
      - id: pytest
        name: "Pytest unit tests"
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
        stages: [commit]
        args: [
          'tests/unit',  # 유닛 테스트만 (E2E는 CI/CD에서)
          '-v',
          '--tb=short',
          '--timeout=10'
        ]

  # ============================================================================
  # 보안 검사
  # ============================================================================
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        name: "Bandit security check"
        args: ['-c', '.bandit']
        exclude: '^tests/'
        stages: [commit]

  # ============================================================================
  # 문서 검사
  # ============================================================================
  - repo: https://github.com/pre-commit/mirrors-docformatter
    rev: v1.7.5
    hooks:
      - id: docformatter
        name: "Docstring formatter"
        args: ['--in-place', '--make-summary-multi-line']
        stages: [commit]

# ============================================================================
# 전역 설정
# ============================================================================
default_language_version:
  python: python3.11

# 기본 실행 단계
default_stages: [commit]

# 타임아웃 (초)
fail_fast: false

# 동시 실행 (병렬 처리)
# ci:
#   autofix_commit_msg: '🔧 auto fix by pre-commit hooks'
#   autoupdate_commit_msg: '⬆️ upgrade pre-commit hooks'
#   skip: [mypy, pytest]  # CI에서는 mypy와 pytest 생략 (느림)
```

### Step 3: Git 훅 설치

```bash
# pre-commit 프레임워크 설치
pre-commit install

# 모든 파일에 대해 훅 실행 (확인용)
pre-commit run --all-files

# 특정 훅만 실행
pre-commit run black --all-files
pre-commit run ruff --all-files
```

---

## ⚙️ 상세 설정

### Black 설정

**파일**: `pyproject.toml`

```toml
[tool.black]
line-length = 100
target-version = ['py311', 'py312']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
preview = true  # 새로운 기능 미리보기
```

### Ruff 설정

**파일**: `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort (import sorting)
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "A",      # flake8-builtins
    "C4",     # flake8-comprehensions
    "SIM",    # flake8-simplify
    "PIE",    # flake8-pie
]

ignore = [
    "E501",   # line too long (Black이 처리)
    "W503",   # line break before binary operator
    "N818",   # Exception name should be named with Error suffix
]

exclude = [
    ".git",
    "__pycache__",
    ".venv",
    "build",
    "dist",
]

[tool.ruff.isort]
known-first-party = ["app", "persona_pipeline"]
known-third-party = ["fastapi", "pydantic"]
```

### MyPy 설정

**파일**: `pyproject.toml`

```toml
[tool.mypy]
python_version = "3.11"
check_untyped_defs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
disallow_untyped_calls = true
warn_return_any = true
warn_unused_ignores = true
warn_unused_configs = true
no_implicit_optional = true
strict_equality = true

[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = true

[[tool.mypy.overrides]]
module = [
    "google.cloud.*",
    "slowapi.*",
]
ignore_missing_imports = true
```

### Bandit 설정

**파일**: `.bandit`

```yaml
# Bandit 보안 검사 설정
assert_used:
  skips:
    - 'tests/*'

exclude_dirs:
  - '/tests/'
  - '/.venv/'
  - '/venv/'

tests:
  - B201  # flask_debug_true
  - B301  # pickle
  - B302  # marshal
  - B303  # md5
  - B304  # cipher
  - B305  # cipher
  - B306  # temp_file
  - B307  # eval
  - B308  # mark_safe
  - B309  # httpsconnection
  - B310  # urllib_urlopen
  - B311  # random
  - B312  # telnetlib
  - B313  # xml_bad_etree
  - B314  # xml_bad_expat
  - B315  # xml_bad_sax
  - B316  # xml_bad_pulldom
  - B317  # xml_bad_etree
  - B318  # xml_bad_expat
  - B319  # xml_bad_sax
  - B320  # xml_bad_pulldom
  - B321  # ftplib
  - B322  # input
  - B323  # unverified_context
  - B324  # hashlib
```

---

## 🚀 워크플로우

### 일반적인 개발 워크플로우

```bash
# 1. 코드 수정
nano app/main.py

# 2. 변경사항 스테이징
git add app/main.py

# 3. 커밋 시도
git commit -m "feat: add new endpoint"

# 자동으로 실행:
# ✅ trailing-whitespace 검사
# ✅ end-of-file-fixer 실행
# ✅ Black 포매팅
# ✅ Ruff 린팅
# ✅ MyPy 타입 검사
# ✅ Pytest 테스트 실행
# ✅ Bandit 보안 검사

# 4a. 모두 통과하면 커밋 완료 ✅
# 4b. 실패하면 수정 후 다시 시도
```

### 훅 스킵 (긴급 상황)

```bash
# 모든 훅 스킵 (권장하지 않음)
git commit --no-verify -m "urgent fix"

# 또는 특정 단계만 스킵
SKIP=mypy,pytest git commit -m "quick fix"
```

### 훅 업데이트

```bash
# pre-commit 프레임워크 업데이트
pre-commit autoupdate

# 특정 훅만 업데이트
pre-commit autoupdate --repo https://github.com/psf/black
```

---

## 📊 성능 최적화

### 느린 훅 최적화

```yaml
# .pre-commit-config.yaml

# MyPy는 느리므로 push 단계에서만 실행
- repo: https://github.com/pre-commit/mirrors-mypy
  stages: [push]  # commit 대신 push에서만 실행

# Pytest는 커밋 시 스킵하고 CI/CD에서만 실행
- repo: local
  stages: [manual]  # git commit 시 실행 안 함
  # 대신: pre-commit run pytest --hook-stage manual
```

### CI/CD에서 훅 실행

**파일**: `.github/workflows/lint.yml`

```yaml
name: Lint and Format

on:
  pull_request:
    branches: [main, develop]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - uses: pre-commit/action@v3
        with:
          extra_args: '--all-files'
```

---

## 🧪 테스트 및 검증

### 로컬 테스트

```bash
# 1. 모든 파일에 대해 훅 실행
pre-commit run --all-files

# 2. 특정 훅만 테스트
pre-commit run black --all-files
pre-commit run ruff --all-files
pre-commit run mypy --all-files

# 3. 상세 로그 출력
pre-commit run --all-files --verbose

# 4. 훅 설치 확인
cat .git/hooks/pre-commit
```

### 테스트 케이스

```bash
# 테스트 1: 포맷팅 에러가 자동 수정되는지 확인
echo 'x=1  ' > test_file.py  # 줄 끝 공백 추가
git add test_file.py
git commit -m "test"
# 예상: Black이 자동으로 포맷팅하고 커밋 성공

# 테스트 2: 타입 에러가 감지되는지 확인
echo 'def add(a: int, b: str) -> int:\n    return a + b' > test_file.py
git add test_file.py
git commit -m "test"
# 예상: MyPy가 타입 에러 감지하고 커밋 실패

# 테스트 3: 테스트 실패가 감지되는지 확인
# (테스트 파일 수정해서 실패 유도)
git add tests/
git commit -m "test"
# 예상: Pytest 실패로 커밋 실패
```

---

## 📋 설정 체크리스트

### 설치 단계
- [ ] `pre-commit` 패키지 설치
- [ ] `.pre-commit-config.yaml` 생성
- [ ] `pre-commit install` 실행
- [ ] 모든 개발자가 설치 완료

### 설정 단계
- [ ] Black 설정 (`pyproject.toml`)
- [ ] Ruff 설정 (`pyproject.toml`)
- [ ] MyPy 설정 (`pyproject.toml`)
- [ ] Bandit 설정 (`.bandit`)

### 검증 단계
- [ ] 로컬에서 `pre-commit run --all-files` 실행
- [ ] 모든 훅 성공 확인
- [ ] CI/CD 워크플로우 추가
- [ ] README 문서 업데이트

### 팀 온보딩
- [ ] 모든 개발자에게 설치 가이드 제공
- [ ] 개발 환경 문서 업데이트
- [ ] Slack/Wiki에 공지

---

## 📚 일반적인 문제 해결

### 문제: "Command 'black' not found"

**원인**: Black이 PATH에 없음

**해결**:
```bash
# 가상 환경 활성화
source .venv/bin/activate

# 또는 pre-commit 재설치
pre-commit clean
pre-commit install
```

### 문제: "MyPy: error: Cannot find implementation or library stub"

**원인**: 타입 스텁 누락

**해결**:
```bash
# 필요한 타입 패키지 설치
pip install types-pyyaml types-python-dateutil

# 또는 .pre-commit-config.yaml에 추가
additional_dependencies: ['pydantic>=2.0', 'types-pyyaml']
```

### 문제: 훅이 너무 느림

**해결**:
- MyPy와 Pytest를 push 단계로 이동
- 병렬 처리 활성화
- 특정 파일 제외

```yaml
- repo: ...
  stages: [push]  # commit 대신 push에서만
```

### 문제: "pre-commit run 하면 이전 코드로 돌아감"

**설명**: pre-commit은 스테이징된 파일만 검사하고 자동 수정함

**해결**:
```bash
# 수정 후 다시 스테이징
git add .
git commit -m "message"
```

---

## 🔧 고급 설정

### 커스텀 훅 추가

```yaml
- repo: local
  hooks:
    - id: custom-check
      name: "Custom code check"
      entry: bash -c 'echo "Running custom check"'
      language: system
      types: [python]
      stages: [commit]
```

### 특정 파일 제외

```yaml
- repo: https://github.com/psf/black
  hooks:
    - id: black
      exclude: '^(migrations/|scripts/)'
```

### 스테이지별 실행

```bash
# 특정 스테이지만 실행
pre-commit run --hook-stage commit   # commit 단계만
pre-commit run --hook-stage push     # push 단계만
pre-commit run --hook-stage manual   # 수동 실행
```

---

## 📅 마이그레이션 가이드 (팀 전체)

### 1단계: 리더 지정 (30분)
- DevOps 또는 시니어 개발자가 주도
- 모든 개발자에게 공지

### 2단계: 개발 환경 업데이트 (1시간)
- 모든 개발자가 `.pre-commit-config.yaml` 풀 받기
- `pre-commit install` 실행
- 로컬에서 `pre-commit run --all-files` 실행

### 3단계: CI/CD 설정 (30분)
- GitHub Actions 워크플로우 추가
- 풀 요청 시 자동 검사

### 4단계: 기존 코드 정리 (1-2시간)
```bash
# 모든 파일에 대해 훅 실행 (자동 수정)
pre-commit run --all-files

# 수정된 파일 커밋
git add .
git commit -m "🔧 auto fix by pre-commit hooks"
git push
```

### 5단계: 규칙 설정 (확인)
- 모든 풀 요청은 pre-commit 통과 필수
- 긴급 상황 시에만 `--no-verify` 사용

---

## 📊 도움말 및 참고

### 유용한 명령어

```bash
# 설치 확인
pre-commit installed

# 현재 설정 확인
cat .pre-commit-config.yaml

# 훅 목록 보기
pre-commit-show

# 특정 파일만 검사
pre-commit run --files app/main.py

# 자세한 로그
pre-commit run --verbose --all-files

# 훅 제거
pre-commit uninstall

# 캐시 초기화
pre-commit clean
```

### 추가 자료

- [pre-commit 공식 문서](https://pre-commit.com/)
- [Black 문서](https://black.readthedocs.io/)
- [Ruff 문서](https://docs.astral.sh/ruff/)
- [MyPy 문서](https://mypy.readthedocs.io/)

---

## 📅 다음 단계

✅ **Pre-commit hooks 설정 가이드 완료** (3시간)

➡️ **Task 2: WAF/Cloud Armor 설정** (6시간)

총 소요 시간: Phase 2 **90시간** 중 **3시간** 완료 ✅
