# Gitko AI Agent Orchestrator

🤖 GitHub Copilot과 통합된 멀티 에이전트 오케스트레이션 시스템

**Current Version**: v0.3.1

## 📖 문서

### 빠른 시작
- 🚀 [Quick Start Guide](QUICKSTART.md) - 5분 안에 시작하기
- ⚡ [치트시트](docs/CHEATSHEET.md) - 1분 빠른 참조
- 📚 [실전 사용 예제](docs/USAGE_EXAMPLES.md) - 상세한 활용 가이드
- ⚙️ [Setup Guide](docs/SETUP_GUIDE.md) - 상세 설정 가이드

### 릴리스 & 완료 보고
- 📝 [Release Notes](RELEASE_NOTES.md) - 최신 릴리스 (v0.3.1)
- 📊 [Completion Report](COMPLETION_REPORT.md) - 프로젝트 완성 보고서
- 📁 [이전 릴리스](docs/releases/) - 과거 버전 릴리스 노트

### 개발 & 배포
- ✅ [배포 체크리스트](docs/DEPLOYMENT_CHECKLIST.md) - 프로덕션 배포 가이드
- 🔍 [자동 테스트](tests/test-extension.ps1) - F5 전 빠른 검증
- 🛠️ [문제 해결](scripts/troubleshoot.ps1) - 자동 진단 & 수정
- 📊 [프로젝트 통계](scripts/project-stats.ps1) - 코드 통계 확인

## ✨ 주요 기능

### 🔧 Language Model Tools (자동 호출)
GitHub Copilot이 자동으로 상황에 맞는 에이전트를 선택하여 실행합니다.

- **Sian Agent** - 코드 리팩토링 및 품질 개선
- **Lubit Agent** - 코드 리뷰 및 보안 검사
- **Gitko Orchestrator** - 복잡한 멀티 에이전트 작업 조율

### 💬 Chat Participant (명시적 호출)
`@gitko` 명령어로 직접 에이전트를 호출할 수 있습니다.

### 📊 실시간 피드백
- 작업 진행 상태 실시간 표시
- Progress 알림으로 장시간 작업 진행률 확인
- Output Channel을 통한 상세 로깅

## 🚀 설치 방법

### 필수 요구사항

- VS Code 1.90.0 이상
- GitHub Copilot 확장 설치
- Python 3.8 이상 (gitko_cli.py 스크립트 실행용)

## 🚀 빠른 시작

### 🔍 테스트 실행 (F5 전 권장)

```powershell
# 자동 검증 스크립트 실행
.\test-extension.ps1

# 출력: ✅ 모든 테스트 통과!
```

### 1. 로컬 개발 모드 (디버깅)

```powershell
# Extension 디렉토리로 이동
cd d:\nas_backup\LLM_Unified\gitko-agent-extension

# 의존성 설치
npm install

# VS Code에서 열기
code .

# F5 키를 눌러 Extension Development Host 실행
```

### 2. VSIX 패키징 및 설치

```powershell
# VSCE 설치 (최초 1회)
npm install -g @vscode/vsce

# VSIX 파일 생성
vsce package

# 생성된 파일 설치
code --install-extension gitko-agent-extension-0.1.0.vsix
```

## ⚙️ 설정

`Ctrl+,` (설정)에서 "Gitko Agent"를 검색하거나, `.vscode/settings.json`에 추가:

```json
{
  "gitkoAgent.pythonPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "gitkoAgent.scriptPath": "${workspaceFolder}/LLM_Unified/ion-mentoring/gitko_cli.py",
  "gitkoAgent.workingDirectory": "${workspaceFolder}/LLM_Unified/ion-mentoring",
  "gitkoAgent.enableLogging": true,
  "gitkoAgent.timeout": 300000,
  "gitkoAgent.computerUsePythonPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "gitkoAgent.computerUseScriptPath": "${workspaceFolder}/LLM_Unified/ion-mentoring/computer_use.py"
}
```

### 설정 항목

| 설정 | 설명 | 기본값 |
|------|------|--------|
| `pythonPath` | Python 실행 파일 경로 | 자동 탐지 |
| `scriptPath` | gitko_cli.py 스크립트 경로 | 자동 탐지 |
| `workingDirectory` | 작업 디렉토리 | 자동 탐지 |
| `enableLogging` | Output Channel 로깅 활성화 | true |
| `timeout` | 에이전트 실행 타임아웃 (ms) | 300000 (5분) |
| `computerUsePythonPath` | Computer Use용 Python 경로 | `pythonPath` → 자동 |
| `computerUseScriptPath` | Computer Use 백엔드(`computer_use.py`) 경로 | 기본값 자동 |
| `ocrBackend` | OCR 백엔드 선택: `auto`(기본), `tesseract`, `rapidocr` | `auto` |

### 자동 경로 감지 & Copilot 안전 장치

- **자동 탐지**: 설정을 비워두면 확장이 워크스페이스(`workspaceFolder`), `.venv`, `LLM_Unified/ion-mentoring` 등을 순회하며 Python 실행 파일과 `gitko_cli.py`를 자동으로 찾습니다. `${workspaceFolder}` 템플릿과 `~` 확장을 지원하므로 여러 프로젝트에서 동일 설정을 재사용할 수 있습니다.
- **경고 후 비활성화**: 필수 파일을 찾지 못하면 Copilot Tool을 등록하지 않고 경고만 표시하므로, 잘못된 절대 경로 때문에 Copilot 요청이 실패하지 않습니다.
- **타임아웃 & 출력 절단**: Language Model Tool/Chat Participant 실행은 기본 5분 타임아웃과 취소 신호를 강제하며, Copilot으로 전달되는 응답을 3,200자 이내로 자동 절단해 400 `invalid_request_body` 오류를 예방합니다. 전체 stdout/stderr는 `Gitko Agent Runtime` Output Channel에서 확인할 수 있습니다.

## 📖 사용법

### 방법 1: 자동 도구 호출 (권장)

GitHub Copilot Chat에서 자연어로 요청하면 자동으로 적절한 에이전트가 선택됩니다:

```text
사용자: "이 코드를 더 깔끔하게 만들어줘"
→ Copilot이 Sian Agent를 자동 호출

사용자: "보안 취약점이 있는지 검토해줘"
→ Copilot이 Lubit Agent를 자동 호출

사용자: "프로젝트 전체를 개선해줘"
→ Copilot이 Gitko Orchestrator를 자동 호출
```

### 방법 2: Chat Participant 직접 호출

```text
@gitko 이 함수를 리팩토링해줘
@gitko /review 코드 리뷰 부탁해
@gitko /improve 성능 최적화 필요해
@gitko /parallel 리뷰와 개선을 동시에 해줘
```

### 사용 가능한 명령어

| 명령어 | 설명 | 에이전트 |
|--------|------|----------|
| `/review` | 코드 리뷰 및 보안 검사 | Lubit |
| `/improve` | 코드 개선 및 리팩토링 | Sian |
| `/parallel` | 병렬 작업 실행 | Gitko |

### 🖱️ Computer Use (OCR/RPA)

명령 팔레트에서 다음 명령을 사용할 수 있습니다:

- "Gitko: Computer Use - Scan Screen" → 화면의 텍스트 요소를 OCR로 스캔해 결과를 출력 채널에 표시
- "Gitko: Computer Use - Click by Text" → 입력한 텍스트와 일치하는 요소를 찾아 클릭

Computer Use는 기본적으로 Tesseract OCR을 우선 사용하며, 미설치/실패 시 RapidOCR(onnxruntime)로 자동 폴백합니다.

- 백엔드 강제 지정이 필요한 경우 VS Code 설정에서 `gitkoAgent.ocrBackend`를 `tesseract` 또는 `rapidocr`로 설정하세요. 이 값은 확장이 Python 백엔드 실행 시 환경변수 `COMPUTER_USE_OCR_BACKEND`로 전달되어 즉시 반영됩니다.

### 🤖 AI/AGI 제어: HTTP Task Poller 연동

에이전트가 데스크탑을 조작할 수 있도록 HTTP Task Queue와 연계했습니다. 확장은 설정 `gitko.httpApiBase`(기본: `http://localhost:8091/api`)의 작업 큐에서 주기적으로 태스크를 가져와 실행하고 결과를 돌려줍니다. 폴링 주기는 `gitko.httpPollingInterval`(기본: 2000ms)로 조정합니다.

- 폴링 엔드포인트: `POST {apiBase}/tasks/next` (body: `{ worker_id: "gitko-extension" }`)
- 결과 제출: `POST {apiBase}/tasks/{task_id}/result` (body: `{ task_id, worker, status, data, error_message? }`)

지원 태스크 타입과 데이터 스키마:

- `computer_use.scan`
  - 요청: `{ type: "computer_use.scan", data: {} }`
  - 응답: `{ elements: Array<{ text, x, y, width, height, confidence }> }`

- `computer_use.find`
  - 요청: `{ type: "computer_use.find", data: { text: string } }`
  - 응답: `{ element: { text, x, y, width, height, confidence } | null }`

- `computer_use.click`
  - 요청1(좌표): `{ type: "computer_use.click", data: { x: number, y: number } }`
  - 요청2(텍스트): `{ type: "computer_use.click", data: { text: string } }`
  - 응답: `{ success: boolean }`

- `computer_use.type`
  - 요청: `{ type: "computer_use.type", data: { text: string } }`
  - 응답: `{ success: boolean }`

안전장치:
- 원격 데스크톱 조작 킬 스위치: `gitko.enableComputerUseOverHttp`를 `false`로 두면 HTTP 태스크를 통한 모든 Computer Use 조작(scan/find/click/type)이 즉시 차단됩니다.
- UI 액션 속도 제한: `gitko.minUiActionIntervalMs`(기본 150ms)로 클릭/타이핑 등 UI 동작 간 최소 간격을 강제합니다.
- pyautogui FAILSAFE가 활성화되어 있어 마우스를 화면 좌상단으로 이동하면 즉시 중단됩니다.

시작/중지:
- 자동 시작: `gitko.enableHttpPoller`가 `true`일 때 활성화 시 자동으로 HTTP 폴러를 시작합니다. (기본값: `true`)
  - 자동 시작을 끄려면 설정에서 `gitko.enableHttpPoller: false`로 변경하세요.
  - 수동 제어는 명령 팔레트에서 다음을 사용하세요.
  - Gitko: Enable HTTP Poller
  - Gitko: Disable HTTP Poller
  - Gitko: Show HTTP Poller Output

## 🎯 에이전트 설명

### 🔧 Sian (코드 개선 전문가)
- 코드 리팩토링
- 성능 최적화
- 클린 코드 제안
- 디자인 패턴 적용

**자동 호출 키워드**: 리팩토링, 개선, 최적화, 깔끔하게, 모던하게

### 🛡️ Lubit (코드 리뷰 전문가)
- 버그 탐지
- 보안 취약점 검사
- 베스트 프랙티스 검증
- 코드 품질 분석

**자동 호출 키워드**: 리뷰, 검토, 보안, 버그, 취약점

### 🎭 Gitko (오케스트레이터)
- 복잡한 멀티 스텝 작업
- 여러 에이전트 조율
- 종합적인 프로젝트 개선

**자동 호출 키워드**: 전체, 종합, 프로젝트, 복합

## 🔍 디버깅

### Output Channel 확인
`View` > `Output` > `Gitko Agent` 선택하여 상세 로그 확인

### 일반적인 문제 해결

#### Python 환경을 찾을 수 없습니다

```powershell
# Python 경로 확인
where python

# 설정에서 수동 지정
"gitkoAgent.pythonPath": "경로/python.exe"
```

#### 에이전트가 응답하지 않습니다
- Output Channel에서 오류 메시지 확인
- Python 스크립트가 정상 실행되는지 확인:

  ```powershell
  python gitko_cli.py "테스트 메시지"
  ```

#### OCR/Computer Use가 동작하지 않습니다

1. Tesseract 설치 확인 및 설정

   - 관리자 권한 PowerShell에서 자동 설치 (권장):
     - `install_tesseract_admin.ps1` 실행 → Chocolatey로 설치, 버전 확인까지 자동 수행
   - 일반 권한 대안:
     - `install_tesseract_winget.ps1` 실행 → 여러 공급자 ID 시도. 환경에 따라 실패할 수 있으며, 이 경우 관리자 스크립트를 권장합니다.
   - 설치 검증만 수행:
     - `configure_tesseract.ps1` 실행 → Tesseract 경로/버전 출력 (일부 터미널에서 한글 출력이 깨질 수 있으나 기능에는 영향 없습니다)
   - 터미널에서 한글이 계속 깨진다면:
     - `configure_tesseract.ps1 -English` 처럼 `-English` 스위치를 붙여 ASCII로 출력하세요.
     - 또는 PowerShell 7 사용, Windows Terminal 사용, `chcp 65001` 적용 등 UTF-8 환경으로 실행하세요.

2. 설정 확인

   ```json
   {
     "gitkoAgent.computerUsePythonPath": "D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe",
     "gitkoAgent.computerUseScriptPath": "D:/nas_backup/LLM_Unified/ion-mentoring/computer_use.py"
   }
   ```

3. 백엔드 수동 테스트

   ```powershell
   # 스캔 (JSON 배열 출력, ExitCode=0 기대)
   D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe D:/nas_backup/LLM_Unified/ion-mentoring/computer_use.py scan

   # 단일 텍스트 찾기 (단어 단위가 더 잘 잡힙니다)
   D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe D:/nas_backup/LLM_Unified/ion-mentoring/computer_use.py find --text "Extension"
   ```

## 📝 사용 예제

### 자동 도구 호출 방식

```text
# Copilot Chat에서
"이 함수의 성능을 개선해줘" → Sian Agent 자동 실행
"SQL 인젝션 취약점이 있는지 확인해줘" → Lubit Agent 자동 실행
"프로젝트 전체를 분석하고 개선점 제안해줘" → Gitko Orchestrator 자동 실행
```

### Chat Participant 직접 호출

```text
@gitko 이 코드를 리팩토링해줘
@gitko /review 보안 취약점 검사
@gitko /improve 성능 최적화 필요
@gitko /parallel 종합적인 코드 개선
```

## 🏗️ 개발

### 프로젝트 구조

```text
gitko-agent-extension/
├── src/
│   └── extension.ts          # 메인 Extension 로직
├── resources/
│   └── gitko-icon.svg         # Extension 아이콘
├── out/                       # 컴파일된 JavaScript
├── package.json               # Extension 매니페스트
├── tsconfig.json              # TypeScript 설정
└── README.md                  # 이 문서
```

### 빌드 및 테스트

```powershell
# 의존성 설치
npm install

# 컴파일
npm run compile

# Watch 모드 (자동 컴파일)
npm run watch

# 확장 테스트 (F5)
# Run > Start Debugging
```

## 🤝 기여

이슈와 PR은 언제나 환영합니다!

## 📄 라이선스

MIT License

## ❓ FAQ (자주 묻는 질문)

### Q: 특정 폴더에서만 AI 에이전트를 사용할 수 있나요?

**A: 아니요, 모든 프로젝트에서 사용할 수 있습니다.**

확장 프로그램은 VS Code 설정을 통해 어떤 프로젝트에서든 작동할 수 있습니다:

**방법 1: 워크스페이스별 설정** (권장)
- 각 프로젝트의 `.vscode/settings.json`에 Python 경로 설정
- 프로젝트마다 다른 Python 환경 사용 가능

```json
{
  "gitkoAgent.pythonPath": "C:/프로젝트A/.venv/Scripts/python.exe",
  "gitkoAgent.scriptPath": "C:/프로젝트A/scripts/gitko_cli.py",
  "gitkoAgent.workingDirectory": "C:/프로젝트A"
}
```

**방법 2: 전역 설정**
- VS Code 사용자 설정에서 기본 경로 지정
- 모든 프로젝트에서 동일한 환경 사용

Settings UI에서: `Preferences: Open Settings (UI)` → `Gitko Agent` 검색

### Q: Python 환경을 찾을 수 없다는 에러가 나옵니다

**A: 다음 순서로 확인하세요:**

1. Python 설치 확인:

```powershell
python --version  # Python 3.13 이상 필요
```

1. VS Code 설정에서 경로 지정:
   - `Ctrl + ,` → Settings 열기
   - "Gitko Agent: Python Path" 검색
   - Python 실행 파일 절대 경로 입력

1. `gitko_cli.py` 스크립트 존재 확인:
   - 스크립트가 있는 폴더 경로를 "Gitko Agent: Script Path"에 설정

### Q: 에이전트 응답이 너무 느립니다

**A: Timeout 설정 조정:**

```json
{
  "gitkoAgent.timeout": 120000  // 120초 (기본: 60초)
}
```

복잡한 리팩토링이나 대용량 파일 리뷰 시 더 긴 timeout이 필요할 수 있습니다.

### Q: Output Channel에서 로그를 볼 수 없습니다

**A: 로깅 활성화:**

```json
{
  "gitkoAgent.enableLogging": true
}
```

그 후 `View` → `Output` → 드롭다운에서 "Gitko Agent" 선택

### Q: 에이전트가 한글을 제대로 출력하지 못합니다

**A: UTF-8 인코딩 문제:**

이 확장 프로그램은 자동으로 `PYTHONIOENCODING=utf-8`을 설정합니다. 
그래도 문제가 있다면:

1. Python 스크립트 첫 줄에 추가:

```python
# -*- coding: utf-8 -*-
```

1. 터미널 인코딩 확인:

```powershell
chcp 65001  # UTF-8로 변경
```

---

## 👨‍💻 개발자

Naeda - Gitko AI Agent Orchestrator

---

**Enjoy using Gitko AI Agent!** 🚀

## 아키텍처

```text
User → Copilot Chat (@gitko)
  → Extension (TypeScript)
    → gitko_cli.py (Python)
      → GitkoIntegratedOrchestrator
        → Sian/Lubit/Gitko Agents
      → Results
    → Extension (파싱 및 표시)
  → Copilot Chat (마크다운 결과)
```

## 시스템 요구사항

- **VS Code**: 1.90.0 이상
- **GitHub Copilot**: 활성화된 구독
- **Python**: 3.13 이상 (가상환경: `D:/nas_backup/LLM_Unified/.venv`)
- **Node.js**: 18.x 이상 (npm 의존성 설치)

## 백엔드 경로

- **Python 실행 파일**: `D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe`
- **CLI 스크립트**: `D:/nas_backup/LLM_Unified/ion-mentoring/gitko_cli.py`
- **작업 디렉토리**: `D:/nas_backup/LLM_Unified/ion-mentoring`

## 개발

### 디렉토리 구조

```text
gitko-agent-extension/
├── src/
│   └── extension.ts       # Chat Participant 구현
├── out/
│   └── extension.js       # 컴파일된 JavaScript
├── package.json           # Extension 매니페스트
├── tsconfig.json          # TypeScript 설정
└── README.md              # 문서
```

### 빌드

```powershell
# TypeScript 컴파일
npm run compile
# 또는
npx tsc -p ./
```

### 테스트

```powershell
Write-Host '확장은 VS Code에서 F5 (Run > Start Debugging)로 테스트합니다.'
```

# Extension Development Host 실행
# F5 키 또는
code --extensionDevelopmentPath=d:\nas_backup\LLM_Unified\gitko-agent-extension

```

## 트러블슈팅

### @gitko가 나타나지 않음

1. GitHub Copilot Extension이 활성화되어 있는지 확인
2. VS Code 재시작 시도
3. Extension Development Host에서 테스트

### Python 백엔드 실행 오류

1. 가상환경 활성화 확인: `D:/nas_backup/LLM_Unified/.venv`
2. gitko_cli.py 수동 실행 테스트:

   ```powershell
   cd D:\nas_backup\LLM_Unified\ion-mentoring
   ..\..\.venv\Scripts\python.exe gitko_cli.py "테스트 메시지"
   ```

3. Python 경로 확인: `extension.ts`의 `pythonPath` 변수

### 결과 파싱 실패

- gitko_cli.py 출력 형식 확인
- `parseAgentOutput()` 함수의 정규표현식 검증
- 로그 확인: VS Code Developer Tools (Ctrl+Shift+I)

## 라이선스

MIT License

## Related Documentation

See project repository for detailed documentation and implementation details.
