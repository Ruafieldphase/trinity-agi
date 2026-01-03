# � Daily Session Summary 자동화

### 개요

- `session_memory/generate_daily_summary.py` 스크립트는 최근 24시간 내 모든 세션을 집계하여 Markdown 요약 리포트를 자동 생성합니다.
- 결과 파일은 `outputs/daily_summaries/YYYY-MM-DD.md`로 저장됩니다.

### 사용법

#### 터미널에서 직접 실행

```powershell
python session_memory/generate_daily_summary.py
```

#### 주요 기능

- 24시간 내 세션 전체 요약 (상태, 퍼소나, resonance 등)
- 퍼소나별/상태별 통계, resonance 최고/최저, 태그 분포 등 하이라이트
- Markdown 포맷으로 자동 저장

#### 예시 출력

```
# Daily Session Summary (2025-10-29)
- Total sessions: **4**
- Completed: 4  Active: 0  Paused: 0  Abandoned: 0
- Avg Resonance: 0.90

## Stats by Persona
| Persona | Sessions | Completed | Avg Resonance | Avg Hours |
|---------|----------|-----------|---------------|-----------|
| Perple | 1 | 1 | 0.90 | 0.0 |

## Session List (last 24h)
| Title | Started | Ended | Status | Persona | Resonance | Tasks | Artifacts | Tags |
|-------|---------|-------|--------|---------|-----------|-------|-----------|------|
| Session Memory System - ChatOps  | 2025-10-29T13:17 | 2025-10-29T13:17 | completed | None | 0.95 | 5 | 5 | session-memory,chatops,phase-1-complete |
| ... (생략)

- Highest Resonance: 0.95
- Lowest Resonance: 0.85
```

---

# �🚀 ChatOps 빠른 시작 가이드

> **English NL commands supported**: You can now say `start the session`, `add a task`, `end session`, `recent sessions`, `search sessions for bqi`, `session stats`, `session details`, `save conversations`, `wrap up the day`, `start the stream`, `stop the stream`, `start the bot`, `stop the bot`, `switch to ai dev`, `preflight`, or `install obs deps` directly in English and ChatOps will route them correctly.

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
Core: Quick Health Probe        # Core 게이트(관문) 빠른 점검
Monitoring: Generate Dashboard (24h HTML)  # 통합 대시보드 생성/열기
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

```text
1. 🎙️ ChatOps: Onboarding Guide    → 가이드 읽기
2. 🔑 ChatOps: Install Secret       → Client Secret 등록
3. ✅ ChatOps: OAuth Setup          → OAuth 인증
4. ChatOps Test: Status             → 상태 확인
5. 📡 ChatOps: Start Streaming      → 방송 시작!
```

### 시나리오 2: 일상 방송 시작

```text
1. ChatOps Test: Status             → 빠른 상태 확인
2. 📡 ChatOps: Start Streaming      → 방송 시작
3. 🤖 ChatOps: Start Bot            → 자동응답 활성화
4. 🎬 ChatOps: Switch Scene         → 필요시 씬 전환
```

### 시나리오 3: 문제 해결

```text
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
| "Core 관문을 열자" | Core 게이트 헬스 프로브 실행 |
| "Core 상태 확인" | Core 게이트 헬스 프로브 실행 |
| "Core health check" | Core 게이트 헬스 프로브 실행 |
| "Core 대시보드" | Core 24시간 대시보드(HTML) 생성/열기 |
| "Core dashboard" | Core 24시간 대시보드(HTML) 생성/열기 |

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
A: 다음을 확인해 주세요.

1) VS Code 통합 터미널 사용 권장 (기본 UTF-8)
2) 이 저장소의 ChatOps 스크립트는 UTF-8 BOM을 적용하여 Windows PowerShell 5.1에서도 한글이 정상 표시됩니다.
3) 외부 콘솔을 쓸 경우, 아래를 먼저 실행하세요:

```powershell
chcp 65001 > $null; [Console]::OutputEncoding = [Text.Encoding]::UTF8; $OutputEncoding = [Text.Encoding]::UTF8
```

여전히 문제가 있으면 PowerShell 7(pwsh) 사용을 권장합니다.

**Q: OBS 연결 실패**
A: OBS Studio → Tools → WebSocket Server Settings → Enable WebSocket server 체크 (Port 4455)

**Q: YouTube 봇 오류**
A:

1. `ChatOps Test: Preflight` 실행
2. `🔑 ChatOps: Install Secret` 실행
3. `✅ ChatOps: OAuth Setup` 실행

**Q: 상태 조회가 실패해도 괜찮나요?**
A: 네! 모든 상태 조회는 "Zero-Fail"로 설계되어 환경 문제가 있어도 exit 0을 반환합니다.

## � 옵션: Core 프로브 모니터

운영 중 상시로 Core 게이트 상태를 샘플링하고 싶다면 예약 작업을 등록하세요.
관리자 권한이 필요할 수 있습니다.

```powershell
# 10분 주기로 수집, 즉시 1회 실행
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/register_core_probe_task.ps1 -Register -IntervalMinutes 10 -RunNow

# 상태 확인
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/register_core_probe_task.ps1 -Status

# 해제
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/register_core_probe_task.ps1 -Unregister
```

수집된 로그는 `outputs/core_probe_log.jsonl`에 JSONL 포맷으로 누적됩니다.

## �📚 더 알아보기

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
