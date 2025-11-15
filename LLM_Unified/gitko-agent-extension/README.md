# Gitko AI Agent Orchestrator

🤖 GitHub Copilot과 통합된 멀티 에이전트 오케스트레이션 시스템

**Version**: v0.3.1

---

## 🚀 빠른 시작 (5분)

### 1. 설치

```powershell
# VSIX 설치
code --install-extension gitko-agent-extension-0.3.1.vsix

# 또는 개발 모드
cd gitko-agent-extension
npm install
# F5 키로 Extension Development Host 실행
```

### 2. 기본 설정

`settings.json`:
```json
{
  "gitkoAgent.pythonPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "gitkoAgent.scriptPath": "${workspaceFolder}/scripts/gitko_cli.py"
}
```

### 3. 사용

```text
# GitHub Copilot Chat에서
"이 코드를 개선해줘" → Sian Agent 자동 실행

# 또는 직접 호출
@gitko /review 코드 리뷰해줘
```

**📖 상세 가이드**: [QUICKSTART.md](QUICKSTART.md)

---

## ✨ 주요 기능

### 🔧 자동 에이전트 선택
GitHub Copilot이 문맥을 분석하여 최적의 에이전트를 자동 선택합니다.

| 에이전트 | 전문 분야 | 자동 호출 키워드 |
|---------|----------|----------------|
| **Sian** | 코드 리팩토링, 성능 최적화 | 개선, 리팩토링, 최적화 |
| **Lubit** | 코드 리뷰, 보안 검사 | 리뷰, 검토, 보안 |
| **Gitko** | 멀티 에이전트 조율 | 전체, 종합, 프로젝트 |

### 💬 명시적 호출
```text
@gitko /review    - 코드 리뷰
@gitko /improve   - 코드 개선
@gitko /parallel  - 병렬 작업
```

### 🖱️ Computer Use (RPA/OCR)
- **화면 스캔**: `Gitko: Computer Use - Scan Screen`
- **텍스트 클릭**: `Gitko: Computer Use - Click by Text`
- **HTTP Task Queue**: AI가 원격으로 데스크톱 제어 가능

### 🛡️ 보안 기능
- **Rate Limiting**: 일일/분당 작업 제한 (100/일, 10/분)
- **Killswitch**: 긴급 정지 토글 (`Gitko Security: Toggle Computer Use Killswitch`)
- **Destructive Action Confirmation**: 위험한 명령 실행 전 확인
- **Audit Log**: 모든 Computer Use 작업 기록 및 내보내기

### 📊 실시간 모니터링
- **Task Queue Monitor**: 작업 큐 상태 실시간 확인
- **Resonance Ledger**: AGI 학습 과정 시각화
- **Activity Tracker**: 사용 패턴 추적

---

## 📖 문서

| 문서 | 설명 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 5분 빠른 시작 가이드 |
| [치트시트](docs/CHEATSHEET.md) | 1분 빠른 참조 |
| [사용 예제](docs/USAGE_EXAMPLES.md) | 실전 활용법 |
| [설정 가이드](docs/SETUP_GUIDE.md) | 상세 설정 방법 |
| [프로젝트 구조](PROJECT_STRUCTURE.md) | 디렉토리 구조 |
| [배포 가이드](docs/DEPLOYMENT_CHECKLIST.md) | 프로덕션 배포 |
| [릴리스 노트](RELEASE_NOTES.md) | 최신 변경사항 (v0.3.1) |

---

## ⚙️ 필수 요구사항

- **VS Code**: 1.90.0 이상
- **GitHub Copilot**: 활성화된 구독
- **Python**: 3.8 이상
- **Node.js**: 18.x 이상 (개발 시)

---

## 🔧 주요 설정

### 기본 설정

| 설정 | 설명 | 기본값 |
|------|------|--------|
| `pythonPath` | Python 실행 파일 | 자동 탐지 |
| `scriptPath` | gitko_cli.py 경로 | 자동 탐지 |
| `enableLogging` | 로깅 활성화 | `true` |
| `timeout` | 실행 타임아웃 (ms) | `300000` (5분) |

### Computer Use 설정

| 설정 | 설명 | 기본값 |
|------|------|--------|
| `ocrBackend` | OCR 엔진 선택 | `auto` |
| `enableComputerUseOverHttp` | 원격 제어 허용 | `false` (안전) |
| `httpPollingInterval` | 폴링 주기 (ms) | `2000` |

**📚 전체 설정**: [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

---

## 🛠️ 개발

### 로컬 개발

```powershell
# 의존성 설치
npm install

# 컴파일
npm run compile

# Watch 모드
npm run watch

# 디버깅: F5
```

### 테스트

```powershell
# 자동 테스트
.\tests\test-extension.ps1

# 통합 테스트
.\tests\test_integration.ps1

# 문제 진단
.\scripts\troubleshoot.ps1
```

### 패키징

```powershell
# VSIX 생성
npm install -g @vscode/vsce
vsce package

# 결과: gitko-agent-extension-0.3.1.vsix
```

---

## 🐛 문제 해결

### Python 환경을 찾을 수 없습니다

```powershell
# Python 경로 확인
where python

# 설정에 수동 지정
"gitkoAgent.pythonPath": "C:/path/to/python.exe"
```

### OCR이 작동하지 않습니다

```powershell
# Tesseract 자동 설치 (관리자)
.\scripts\setup\install_tesseract_admin.ps1

# 설치 확인
.\scripts\setup\configure_tesseract.ps1
```

### 에이전트가 응답하지 않습니다

1. Output Channel 확인: `View` → `Output` → `Gitko Agent`
2. Python 스크립트 수동 테스트:
   ```powershell
   python gitko_cli.py "테스트"
   ```
3. 타임아웃 증가: `"gitkoAgent.timeout": 600000`

**📘 더 많은 문제 해결**: [scripts/troubleshoot.ps1](scripts/troubleshoot.ps1)

---

## 🏗️ 아키텍처

```
User Input
    ↓
GitHub Copilot Chat
    ↓
Gitko Extension (TypeScript)
    ↓
gitko_cli.py (Python Backend)
    ↓
Agent Network (Sian/Lubit/Gitko)
    ↓
Results → Copilot → User
```

**📐 상세 구조**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

## 📊 프로젝트 통계

```powershell
# 코드 통계 확인
.\scripts\project-stats.ps1
```

---

## 🤝 기여

이슈와 PR은 언제나 환영합니다!

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 라이선스

MIT License

---

## 👨‍💻 개발자

**Naeda** - Gitko AI Agent Orchestrator

---

**🚀 Enjoy using Gitko AI Agent!**

> 💡 **Tip**: 더 많은 사용 예제는 [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md)를 참고하세요.
