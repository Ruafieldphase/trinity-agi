# Day 2 — 아키텍처와 설계 가이드 (ION Mentoring)

본 문서는 Day 1에서 구축한 “실행 가능한 환경 + 첫 Vertex AI 호출”을 토대로, Day 2에 수행할 아키텍처 정리와 테스트 도입 계획을 제시합니다. 실습자는 최소 단위의 설계 산출물, 테스트 스켈레톤, 다음 단계 확장 로드맵을 확보하게 됩니다.

## 목표

- 실행 환경을 넘어 “안전하고 테스트 가능한 구조”를 갖춘다.
- 구성 파싱과 프롬프트 전송 로직의 경계를 명확히 하고, 단위 테스트를 도입한다.
- 이후 확장을 고려한 간단한 계층 구조와 인터페이스를 정의한다.

## 범위

- 코드: 기존 `ion_first_vertex_ai.py`의 구성 파싱(환경변수)과 커넥터 경계 재확인
- 테스트: 구성 파싱 유닛 테스트, SDK 미설치 가드 동작 테스트(네트워크 호출 없음)
- 문서/로드맵: 간단한 계층 구조, 확장 플랜 정의

## 현재 구조 요약

- 파일: `ion-mentoring/ion_first_vertex_ai.py`
  - `get_runtime_config()`: 환경 변수에서 Project/Location/Model을 해석
  - `VertexAIConnector`: `initialize()`, `load_model()`, `send_prompt()` 제공
  - 메인 실행: 구성 출력 → 초기화 → 모델 로드 → 샘플 프롬프트 전송

## 제안하는 계층 구조 (경량)

- config 레이어: 환경변수/파일/CLI 옵션 → 런타임 구성 오브젝트로 표준화
- provider 레이어: Vertex/Gemini 등 각 벤더별 커넥터
- use-case 레이어: 프롬프트 전송, 결과 후처리, 로깅, 안전장치 등

- Day 2에서는 “config + provider” 경계를 먼저 다지고, use-case 레이어는 *핵심 스켈레톤*까지 마련합니다.

### PromptClient 추상화 추가 (경량)

- 파일: `ion-mentoring/prompt_client.py`
- 역할: 공통 `PromptClient` 인터페이스와 `VertexPromptClient` 래퍼 제공
- 이점: 추후 다른 벤더(또는 로컬 모델)로 교체 시 상위 레이어 변경 최소화

간단 사용 예시:

```python
from ion_mentoring import prompt_client  # 폴더 이름에 하이픈이 있어 동적 로더 사용

client = prompt_client.create_default_vertex_prompt_client()
client.initialize().load()
print(client.info())
print(client.send("Ping"))
```

### Baseline Use-case Layer

- 제안 파일: `ion_mentoring/usecases/baseline_story.py`
  - `run_story(prompt: str) -> dict`: PromptClient를 호출해 응답/메타 정보를 묶어 반환.
  - `summarise(result: dict) -> str`: Day 3 리듬 로직에 넘길 핵심 요약을 생성.
  - CLI 진입점 예시: `python -m ion_mentoring.usecases.baseline_story "안녕, 오늘 수업 개요를 정리해줘."`
- 테스트: `tests/test_baseline_story.py`
  - 환경 미구성 시 친절한 안내를 출력하고 종료.
  - mock 응답으로 JSON 포맷·에러 처리·로깅 플래그를 검증.

> Day 2에서는 config/provider와 위의 최소 use-case 스켈레톤까지 준비하고,
> Day 3부터 Resonance/리듬 로직을 해당 use-case 모듈 안에서 확장합니다.

## 테스트 도입 (Pytest)

도입 이유

- Day 1 코드가 “돌아가는지”에서 “의도대로 동작하는지”를 검증
- 회귀 방지: 환경키 우선순위, 예외 가드 등 핵심 규칙 고정

도입 항목

- `test_get_runtime_config_defaults`: 환경변수 미설정 시 기본값 해석 검증
- `test_get_runtime_config_env_override`: 환경변수 우선순위 규칙 검증
- `test_initialize_import_guard`: SDK 미설치(혹은 가드) 시 친절 에러 확인
- `test_load_model_import_guard`: GenerativeModel 가드 검증

실행 방법 (선택)

- VS Code Tasks: “Python: Run Tests” 또는 아래 명령으로 특정 파일만 실행
- 빠른 실행 예시는 본 문서 하단 “Try it” 참고

## 확장 로드맵

- 안전장치: 요청/응답 길이 제한, 재시도/타임아웃, 예외 분류
- 로깅/관측: 구조화 로그, 최소 메트릭 카운터, 응답 샘플링 보관
- 구성 확장: 파일(.env, yaml) + CLI 옵션 병합, 프로필(DEV/PROD) 구분
- 래퍼 추상화: `PromptClient` 인터페이스 도입, Vertex/Gemini/타벤더 플러그형 커넥터
- 통합 테스트: 모의 서버/레코더(VCR) 기반의 네트워크 독립 검증

## Try it

- 환경 체크: `ion-mentoring/tools/quick_check_config.py`
- 첫 연결: `ion-mentoring/ion_first_vertex_ai.py`
- 테스트: 아래처럼 단일 테스트 파일만 선택 실행 가능

```powershell
# (옵션) 가상환경 활성화 후 pytest 설치
. .\.venv\Scripts\Activate.ps1; pip install -q pytest

# 본 리포지토리 루트(또는 임의 경로)에서 지정 파일만 실행
python -m pytest -q LLM_Unified/ion-mentoring/tests/test_ion_first_vertex_ai.py
```

PromptClient 테스트 실행:

```powershell
python -m pytest -q LLM_Unified/ion-mentoring/tests/test_prompt_client.py
```

### PowerShell 환경 로더 고급 사용법

- 세션 적용(기본): 현재 PowerShell 세션에만 즉시 적용

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring\tools
./load_env.ps1 -Path ..\..\.env
```

- 영구 적용: 사용자 환경 변수에 저장되어 새 세션부터 유효

```powershell
cd D:\nas_backup\LLM_Unified\ion-mentoring\tools
./load_env.ps1 -Path ..\..\.env -Persist
```

참고: `.env.example`를 복사해 `.env`로 만들고 실제 값을 채운 뒤 사용하세요. `.env.example`는 Git에 포함되고, `.env`는 `.gitignore`로 보호됩니다.

---

## 👉 다음 단계: Day 3로 이동하기

Day 2에서 아키텍처 기초와 테스트 환경을 구축했습니다. 이제 Day 3에서는 내다AI의 핵심 기능인 **파동키 변환 시스템**을 실제로 구현합니다:

- **`ResonanceConverter`** 클래스 설계 및 구현
- Vertex AI를 활용한 감정 톤 분석
- 리듬 패턴 추출 알고리즘
- 페어 프로그래밍 실습

📘 [DAY3_RESONANCE_IMPLEMENTATION.md로 이동](./DAY3_RESONANCE_IMPLEMENTATION.md)

---

작성/검토: ION × GitHub Copilot — 2025-10-17
