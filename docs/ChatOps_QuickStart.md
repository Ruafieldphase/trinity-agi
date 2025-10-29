# 🚀 ChatOps 빠른 시작 가이드

자연어로 스트리밍을 제어하는 원클릭 워크플로우입니다.

## ⚡ VS Code 태스크 (추천)

Command Palette (`Ctrl+Shift+P`) → `Tasks: Run Task` → 아래 태스크 선택

### 📋 핵심 태스크 목록

#### 🎯 처음 시작할 때

```
🎙️ ChatOps: Onboarding Guide     # 온보딩 가이드 표시
🔑 ChatOps: Install Secret        # Client Secret 설치
✅ ChatOps: OAuth Setup           # OAuth 인증
ChatOps Test: Status              # 상태 확인
```

#### 📡 방송 제어

```
📡 ChatOps: Start Streaming       # 방송 시작
⏹️ ChatOps: Stop Streaming        # 방송 중지
🎬 ChatOps: Switch Scene          # 씬 전환 (대화형)
```

#### 🤖 봇 제어

```
🤖 ChatOps: Start Bot            # YouTube 자동응답 봇 시작
🛑 ChatOps: Stop Bot             # 봇 중지
ChatOps Test: Dry-Run            # 테스트 모드
```

#### 🔍 상태 & 점검

```
ChatOps Test: Status             # 상태 확인 (안전)
ChatOps Test: Preflight          # 의존성 점검
ChatOps: Natural Command         # 자유 입력 (대화형)
```

## 💬 터미널 명령어

```powershell
# 기본 형식
powershell -File scripts/chatops_router.ps1 -Say "자연어 명령"

# 예시
chatops_router.ps1 -Say "상태 보여줘"
chatops_router.ps1 -Say "방송 시작해줘"
chatops_router.ps1 -Say "씬 Coding 바꿔줘"
chatops_router.ps1 -Say "봇 켜줘"
chatops_router.ps1 -Say "온보딩 도와줘"
```

## 🎬 시나리오별 워크플로우

### 시나리오 1: 완전 새 사용자

```
1. 🎙️ ChatOps: Onboarding Guide    → 가이드 읽기
2. 🔑 ChatOps: Install Secret       → Client Secret 등록
3. ✅ ChatOps: OAuth Setup          → OAuth 인증
4. ChatOps Test: Status             → 상태 확인
5. 📡 ChatOps: Start Streaming      → 방송 시작!
```

### 시나리오 2: 일상 방송 시작

```
1. ChatOps Test: Status             → 빠른 상태 확인
2. 📡 ChatOps: Start Streaming      → 방송 시작
3. 🤖 ChatOps: Start Bot            → 자동응답 활성화
4. 🎬 ChatOps: Switch Scene         → 필요시 씬 전환
```

### 시나리오 3: 문제 해결

```
1. ChatOps Test: Status             → 문제 파악
2. ChatOps Test: Preflight          → 의존성 확인
3. 🎙️ ChatOps: Onboarding Guide    → 설정 가이드 재확인
4. ✅ ChatOps: OAuth Setup          → 필요시 재인증
```

## 🎯 자연어 명령 레퍼런스

### 방송 제어

| 명령 | 동작 |
|------|------|
| "방송 시작해줘" | 스트리밍 시작 |
| "방송 멈춰" | 스트리밍 중지 |
| "씬 [이름] 바꿔줘" | 씬 전환 |

### 상태 확인

| 명령 | 동작 |
|------|------|
| "상태 보여줘" | 안전 상태 요약 |
| "퀵 상태" | 빠른 확인 |
| "obs 상태" | OBS 상세 정보 |

### 봇 제어

| 명령 | 동작 |
|------|------|
| "봇 켜줘" | 자동응답 시작 |
| "봇 꺼줘" | 봇 중지 |
| "드라이런" | 테스트 모드 |

### 온보딩 & 설정

| 명령 | 동작 |
|------|------|
| "온보딩 도와줘" | 온보딩 가이드 |
| "시크릿 등록해줘" | Client Secret 설치 |
| "oauth" | OAuth 인증 |
| "프리플라이트" | 의존성 점검 |
| "OBS 의존성 설치" | OBS 제어 라이브러리 설치 (최초 1회) |

## 💡 프로 팁

### VS Code에서 더 빠르게

1. **키보드 단축키 설정**
   - File → Preferences → Keyboard Shortcuts
   - `Tasks: Run Task` 검색 후 단축키 지정 (예: `Ctrl+Shift+T`)

2. **자주 쓰는 태스크 즐겨찾기**
   - `.vscode/tasks.json`에서 `"group": "build"` 또는 `"group": "test"` 설정

3. **터미널 별칭 만들기**

   ```powershell
   # PowerShell 프로필에 추가 (~\Documents\PowerShell\Microsoft.PowerShell_profile.ps1)
   function chatops { powershell -File d:\nas_backup\scripts\chatops_router.ps1 -Say $args[0] }
   
   # 사용 예
   chatops "상태 보여줘"
   chatops "방송 시작"
   ```

### 자주 묻는 질문

**Q: 한글이 깨져요**
A: VS Code 통합 터미널 사용 권장. PowerShell 5.1 콘솔은 UTF-8 제한이 있지만 기능은 정상 작동합니다.

**Q: OBS 연결 실패**
A: OBS Studio → Tools → WebSocket Server Settings → Enable WebSocket server 체크 (Port 4455)

**Q: YouTube 봇 오류**
A:

1. `ChatOps Test: Preflight` 실행
2. `🔑 ChatOps: Install Secret` 실행
3. `✅ ChatOps: OAuth Setup` 실행

**Q: 상태 조회가 실패해도 괜찮나요?**
A: 네! 모든 상태 조회는 "Zero-Fail"로 설계되어 환경 문제가 있어도 exit 0을 반환합니다.

## 📚 더 알아보기

- [상세 사용자 가이드](./ChatOps_README.md)
- [검증 보고서](./ChatOps_Verification_Report.md)
- [원본 스크립트](../scripts/chatops_router.ps1)
- [의도 파서](../scripts/chatops_intent.py)

## 🎓 핵심 철학

1. **자연어 우선**: "방송 시작해줘"처럼 말하듯이 명령
2. **Zero-Fail**: 상태 조회는 절대 실패하지 않음
3. **자체 완결**: 가이드가 시스템에 내재
4. **원클릭**: VS Code에서 모든 작업 완료

---

**시작하기**: Command Palette → `Tasks: Run Task` → `🎙️ ChatOps: Onboarding Guide`

**마지막 업데이트**: 2025-10-27
