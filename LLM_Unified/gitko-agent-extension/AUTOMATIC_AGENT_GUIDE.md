# Gitko Agent Extension - 자동 에이전트 호출

## 🎯 핵심 개선사항

### Before (명령형)

```
사용자: "@gitko 이 코드를 리팩토링해줘"
        ↑ 명령어를 알아야 함
```

### After (자동 판단)

```
사용자: "이 코드를 더 깔끔하게 만들고 싶어"
Copilot: (내부 분석) "리팩토링이 필요하구나"
         → sian_refactor 도구 자동 호출
         → 결과를 자연어로 설명
```

## 🛠️ 등록된 Language Model Tools

Extension은 3개의 도구를 Copilot에게 제공합니다:

### 1. `sian_refactor` (Sian 에이전트)
**자동 호출 조건:**
- "코드를 개선해줘"
- "리팩토링이 필요해"
- "더 깔끔하게 만들어줘"
- "성능을 최적화해줘"
- "모던한 코드로 바꿔줘"

**역할:** 코드 품질 개선, 리팩토링, 최적화

### 2. `lubit_review` (Lubit 에이전트)
**자동 호출 조건:**
- "보안 취약점을 찾아줘"
- "코드 리뷰해줘"
- "버그가 있는지 확인해줘"
- "베스트 프랙티스를 따르는지 봐줘"
- "안전한지 검토해줘"

**역할:** 코드 리뷰, 보안 검토, 버그 탐지

### 3. `gitko_orchestrate` (Gitko 오케스트레이터)
**자동 호출 조건:**
- "프로젝트 전체를 개선해줘"
- "여러 파일을 한꺼번에 수정해줘"
- "복잡한 리팩토링이 필요해"
- "전체적인 코드 품질을 올려줘"

**역할:** 멀티 에이전트 조율, 복잡한 작업

## 🎬 사용 예시

### 예시 1: 자연어로 리팩토링 요청

```
사용자: 이 함수가 너무 길어서 읽기 힘들어. 어떻게 하면 좋을까?

Copilot: (자동 판단) → sian_refactor 호출
         → "함수를 3개로 분리하고, 각각 단일 책임 원칙을 따르도록 개선했습니다..."
```

### 예시 2: 보안 검토 요청

```
사용자: 이 인증 코드가 안전한지 확인해줘

Copilot: (자동 판단) → lubit_review 호출
         → "SQL Injection 취약점 발견, Prepared Statement 사용 권장..."
```

### 예시 3: 프로젝트 전체 개선

```
사용자: 이 프로젝트 코드가 오래됐어. 전체적으로 현대화하고 싶어

Copilot: (자동 판단) → gitko_orchestrate 호출
         → Sian: 코드 리팩토링
         → Lubit: 보안 검토
         → "총 15개 파일 개선, 3개 보안 이슈 해결..."
```

## 🔧 동작 원리

```
1. 사용자가 Copilot Chat에 자연어로 요청
   ↓
2. Copilot이 요청 분석 (내장 LLM)
   ↓
3. Copilot이 등록된 Tools 중 적합한 것 선택
   - sian_refactor: "리팩토링", "개선", "최적화" 키워드
   - lubit_review: "보안", "리뷰", "버그" 키워드
   - gitko_orchestrate: "전체", "프로젝트", "복잡한" 키워드
   ↓
4. Extension의 Tool 실행
   - Python CLI 호출 (gitko_cli.py)
   - 해당 에이전트 실행
   ↓
5. 결과를 Copilot이 자연어로 가공
   ↓
6. 사용자에게 친절한 설명과 함께 제공
```

## ⚙️ 설정 방법

### 1. Extension 로컬 테스트

```powershell
# VS Code에서
1. (workspace)/LLM_Unified/gitko-agent-extension 폴더 열기
2. F5 키 누르기 (Extension Development Host 실행)
3. 새 창에서 아무 코드 파일 열기
4. Copilot Chat 열기 (Ctrl+Shift+I)
5. 자연어로 요청해보기
```

> 💡 `gitkoAgent.*` 설정을 비워둬도 확장이 현재 워크스페이스 내 `.venv`와 `LLM_Unified/ion-mentoring/gitko_cli.py`를 자동으로 탐지합니다. 여러 프로젝트에서 재사용하려면 `${workspaceFolder}` 템플릿을 활용하세요.

### 2. Tool 활성화 확인

```
Copilot Chat에서:
"어떤 도구들을 사용할 수 있어?"

예상 응답:
- Sian Code Refactoring: 코드 개선 및 리팩토링
- Lubit Code Review: 코드 리뷰 및 보안 검토
- Gitko Orchestrator: 복잡한 작업 조율
```

### 3. 실제 테스트

```python
# test.py 파일 열기
def calculate(a, b, c, d):
    return a + b + c + d

# Copilot Chat에 입력:
"이 함수를 개선해줘"

# Copilot이 자동으로 sian_refactor 호출
# 결과: "가변 인자(*args)로 개선 가능합니다..."
```

### Copilot 안전장치 (v0.2+)

- Language Model Tool/Chat Participant 출력은 3,200자 이내로 자동 절단되어 GitHub Copilot의 400 `invalid_request_body` 오류를 예방합니다.
- 실행 타임아웃(기본 5분)과 취소 신호가 강제되며, 전체 stdout/stderr는 `Gitko Agent Runtime` Output Channel에서 확인할 수 있습니다.
- 필수 파일을 찾지 못하면 도구 등록 전 단계에서 경고 후 비활성화되므로 잘못된 경로가 Copilot 세션을 깨뜨리지 않습니다.

## 📊 기존 vs 개선

| 항목 | Before (Chat Participant) | After (Language Model Tools) |
|------|--------------------------|------------------------------|
| 호출 방식 | `@gitko 명령어` | 자연어 대화 |
| 사용자 학습 | 명령어 외워야 함 | 자연스럽게 대화 |
| 에이전트 선택 | 사용자가 명시 | Copilot이 자동 판단 |
| 프로그래밍 지식 | 필요 (명령어 구조) | 불필요 (자연어만) |
| UX | 명령형 인터페이스 | 대화형 어시스턴트 |

## 🎯 핵심 차이점

### Chat Participant (기존)

```
@gitko /review 이 파일을 검토해줘
  ↑      ↑
명령어  서브커맨드
```

- 사용자가 명령 구조 알아야 함
- 에이전트 수동 선택

### Language Model Tools (개선)

```
이 파일에 보안 문제가 있는지 확인해줘
```

- 자연어만으로 의도 전달
- Copilot이 자동으로 lubit_review 선택
- 명령어 몰라도 됨

## 🚀 다음 단계

1. **즉시 테스트**: F5 → Copilot Chat에서 자연어로 요청
2. **사용성 검증**: 다양한 요청 패턴 테스트
3. **Tool Description 개선**: Copilot의 선택 정확도 향상
4. **VSIX 패키징**: 프로덕션 배포 준비

---

**핵심**: 이제 사용자는 프로그래밍 명령어를 몰라도, 자연스럽게 "이 코드 개선해줘"라고 말하면 Copilot이 알아서 적절한 에이전트를 호출합니다!
