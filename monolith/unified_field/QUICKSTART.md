# 🚀 Gitko Extension Quick Start Guide

**5분 안에 시작하기!**

---

## 📋 체크리스트

시작하기 전에 확인:
- [ ] VS Code 1.90.0 이상 설치
- [ ] GitHub Copilot Extension 설치 및 활성화
- [ ] Python 3.8+ 설치 (선택사항, Computer Use 기능용)

---

## ⚡ 빠른 설치

### 방법 1: Extension Development Host (개발/테스트)

```powershell
# 1. 프로젝트 클론
git clone <repository-url>
cd gitko-agent-extension

# 2. 의존성 설치
npm install

# 3. VS Code에서 열기
code .

# 4. F5 키 - Extension Development Host 실행
```

### 방법 2: VSIX 설치 (프로덕션)

```powershell
# 1. VSIX 다운로드 또는 빌드
vsce package  # 빌드하는 경우

# 2. 설치
code --install-extension gitko-agent-extension-0.3.0.vsix

# 3. VS Code 재시작
```

---

## 🎯 첫 실행

### 1. 설정 검증 (권장)

```
Ctrl+Shift+P → "Gitko: Validate Configuration"
```

모든 경로와 설정을 자동으로 확인합니다.

### 2. 대시보드 열기

세 가지 주요 대시보드:

```bash
# Task Queue Monitor
Ctrl+Shift+P → "Gitko: Show Task Queue Monitor"

# Performance Monitor (NEW in v0.3.0!)
Ctrl+Shift+P → "Gitko: Show Performance Monitor"

# Resonance Ledger
Ctrl+Shift+P → "Gitko: Show Resonance Ledger"
```

### 3. GitHub Copilot과 함께 사용

Copilot Chat에서:

```
# 직접 호출
@gitko "이 코드를 리팩토링해줘"

# 또는 Copilot이 자동으로 Agent 선택
"이 함수를 최적화하고 싶어"
```

---

## 📊 주요 기능 살펴보기

### 1. Performance Monitor (v0.3.0 신규)

실시간 성능 추적 대시보드:

- ✅ 모든 작업의 실행 시간 추적
- ✅ 성공률 통계
- ✅ 평균/최소/최대 실행 시간
- ✅ JSON 내보내기

**사용법**:
```
1. Ctrl+Shift+P → "Show Performance Monitor"
2. Computer Use 작업 실행
3. 대시보드에서 실시간 메트릭 확인
```

### 2. HTTP Task Poller

백그라운드 작업 처리:

- Port 8091 Task Queue Server 연결
- 2초마다 새 작업 확인
- 자동 재시도 (v0.2.1+)

**활성화**:
```powershell
# 기본값: 자동 시작
# 수동 제어:
Ctrl+Shift+P → "Gitko: Enable HTTP Poller"
Ctrl+Shift+P → "Gitko: Disable HTTP Poller"
```

### 3. Computer Use (OCR/RPA)

화면 인식 및 자동화:

```typescript
// 텍스트로 요소 찾아서 클릭
await clickElementByText("확인");

// 화면 전체 스캔
const elements = await scanScreen();
```

**명령어**:
```
Ctrl+Shift+P → "Gitko: Computer Use - Click by Text"
Ctrl+Shift+P → "Gitko: Computer Use - Scan Screen"
```

---

## ⚙️ 기본 설정

### 최소 설정 (자동 탐지)

설정 없이 바로 사용 가능! Extension이 자동으로 경로를 찾습니다.

### 추천 설정 (프로젝트별)

`.vscode/settings.json`:

```json
{
  "gitkoAgent.enableLogging": true,
  "gitko.enableHttpPoller": true,
  "gitko.httpPollingInterval": 2000
}
```

### 고급 설정 (Computer Use)

```json
{
  "gitkoAgent.computerUsePythonPath": "D:/nas_backup/LLM_Unified/.venv/Scripts/python.exe",
  "gitkoAgent.computerUseScriptPath": "D:/nas_backup/LLM_Unified/ion-mentoring/computer_use.py",
  "gitkoAgent.ocrBackend": "auto",
  "gitko.enableComputerUseOverHttp": false
}
```

---

## 🎓 5분 튜토리얼

### Step 1: 설정 검증 (30초)

```
1. Ctrl+Shift+P
2. "Gitko: Validate Configuration" 입력
3. 결과 확인
```

**기대 결과**: ✅ All configurations are valid!

### Step 2: Performance Monitor 열기 (30초)

```
1. Ctrl+Shift+P
2. "Gitko: Show Performance Monitor" 입력
3. 대시보드 확인
```

**기대 결과**: 빈 대시보드 (아직 작업 없음)

### Step 3: Copilot으로 코드 작업 (2분)

```
1. 아무 코드 파일 열기
2. Copilot Chat 열기 (Ctrl+Alt+I)
3. @gitko "이 함수 리팩토링" 입력
4. 결과 확인
```

**기대 결과**: Sian Agent가 코드를 분석하고 개선안 제시

### Step 4: 성능 메트릭 확인 (1분)

```
1. Performance Monitor 다시 열기
2. 실행된 작업 통계 확인
3. 💾 Export 클릭 → JSON 다운로드
```

**기대 결과**: 작업 실행 시간 및 성공률 확인

### Step 5: Task Queue Monitor (1분)

```
1. Ctrl+Shift+P
2. "Gitko: Show Task Queue Monitor" 입력
3. 대기 중인 작업 확인
```

**기대 결과**: Task Queue 상태 실시간 모니터링

---

## 🐛 문제 해결

### ❌ @gitko가 안 보여요

**해결책**:
1. GitHub Copilot Extension 활성화 확인
2. VS Code 재시작
3. Extension Development Host 사용 중인지 확인

### ❌ Python 경로 오류

**해결책**:
```
1. Ctrl+Shift+P → "Gitko: Validate Configuration"
2. 에러 메시지 확인
3. settings.json에 올바른 경로 설정:
   "gitkoAgent.pythonPath": "C:/Python38/python.exe"
```

### ❌ HTTP Poller가 연결 안 됨

**해결책**:
```powershell
# 1. Task Queue Server 실행 확인
# 2. Port 8091 사용 중인지 확인
netstat -ano | findstr :8091

# 3. Output Channel 확인
View → Output → "Gitko HTTP Poller"
```

### ❌ Computer Use 작업 실패

**해결책**:
```
1. Tesseract OCR 설치:
   .\install_tesseract_winget.ps1

2. RapidOCR로 자동 폴백 확인
3. Output Channel 로그 확인
```

---

## 📚 다음 단계

### 배우기

1. [README.md](README.md) - 전체 기능 가이드
2. [RELEASE_NOTES_v0.3.0.md](RELEASE_NOTES_v0.3.0.md) - 최신 기능
3. [SETUP_GUIDE.md](SETUP_GUIDE.md) - 상세 설정 가이드

### 탐색하기

```bash
# 모든 명령어 보기
Ctrl+Shift+P → "Gitko:"

# Output 채널
View → Output → "Gitko Extension"
View → Output → "Gitko HTTP Poller"

# 설정 페이지
Ctrl+, → "Gitko"
```

### 고급 기능

- **Agent 커스터마이징**: Agent 동작 방식 조정
- **Performance 분석**: 병목 지점 파악
- **HTTP API 통합**: 외부 시스템 연동

---

## 🎯 체크포인트

5분 후 달성해야 할 것:

- [x] Extension 설치 완료
- [x] 설정 검증 통과
- [x] 3개 대시보드 확인
- [x] Copilot으로 첫 작업 실행
- [x] Performance 메트릭 확인

**축하합니다! 🎉 Gitko Extension을 시작했습니다!**

---

## 💡 팁

### 단축키 추가 (선택사항)

`Keyboard Shortcuts` (Ctrl+K Ctrl+S):

```json
{
  "key": "ctrl+alt+p",
  "command": "gitko.showPerformanceViewer"
},
{
  "key": "ctrl+alt+t",
  "command": "gitko.showTaskQueueMonitor"
}
```

### 생산성 향상

1. **자주 사용하는 대시보드 고정**
2. **Output Channel 항상 열어두기**
3. **정기적으로 성능 메트릭 Export**

---

## 🆘 도움이 필요하신가요?

- **문서**: README.md, SETUP_GUIDE.md
- **로그**: Output Channel 확인
- **이슈**: GitHub Issues
- **설정**: `Ctrl+Shift+P` → "Validate Configuration"

---

**Happy Coding! 🚀**
