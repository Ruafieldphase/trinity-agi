# 세션 연속성 가이드 (Session Continuity Guide)

**새 Copilot 채팅에서 작업을 자동으로 이어가는 방법**

---

## 🚀 빠른 시작 (30초)

### ⭐ 방법 1: 한 단어로 복원 (가장 간단!)

새 채팅창을 열고 다음 중 **하나만** 입력:

```
복원
```

또는

```
컨텍스트
```

또는

```
이어서
```

---

## 🆕 새 채팅 열기 (원클릭!)

### ⚡ 가장 빠른 방법 (추천!)

**VS Code Tasks 실행**:

```
Ctrl+Shift+P → Tasks: Run Task → 🆕 Chat: New with Context (Quick)
```

**동작**:

1. ✅ 컨텍스트가 자동으로 클립보드에 복사됨
2. ✅ 새 Copilot 채팅 창이 열림
3. ✅ `Ctrl+V` → `Enter`로 즉시 붙여넣기!

### 🔑 키보드 단축키 설정 (선택사항)

**`File > Preferences > Keyboard Shortcuts (JSON)` 열고 추가**:

```json
[
    {
        "key": "ctrl+shift+alt+n",
        "command": "workbench.action.tasks.runTask",
        "args": "🆕 Chat: New with Context (Quick)"
    }
]
```

이제 `Ctrl+Shift+Alt+N` 한 번으로 새 채팅 + 컨텍스트 자동 로드! 🚀

### 📋 사용 가능한 Tasks

1. **🆕 Chat: New with Context (Quick)**
   - 간단 요약 (`.copilot_context_summary.md`)
   - 추천: 일반적인 작업 재개

2. **🆕 Chat: New with Full Report**
   - 상세 리포트 (`session_continuity_latest.md`)
   - 추천: 복잡한 문제 해결, 전체 컨텍스트 필요시

---

### 방법 2: 파일 직접 로드

```
@workspace /file:outputs/.copilot_context_summary.md
```

---

## 🎯 목적

VS Code를 닫았다가 다시 열 때, 또는 새 창을 열 때 **이전 작업 컨텍스트를 자동으로 복원**하여 바로 작업을 이어갈 수 있도록 합니다.

---

## ✨ 자동 복원 기능

### 워크스페이스를 열면 자동으로

1. ✅ **최근 세션 스냅샷** 확인 (`outputs/session_memory/*.json`)
2. ✅ **리듬 상태** 확인 (RHYTHM_REST_PHASE, RHYTHM_SYSTEM_STATUS_REPORT)
3. ✅ **자율 목표** 요약 (Goal Tracker 최근 3개)
4. ✅ **코어 프로세스** 상태 (최근 30분 이내 데이터)
5. ✅ **추천 다음 행동** 제시

### 출력 파일

- **`outputs/session_continuity_latest.md`**: 복원 리포트 (상세)
- **`outputs/.copilot_context_summary.md`**: Copilot 채팅용 요약 (간단)
- 자동으로 생성되며 최근 상태를 요약

---

## 🤖 새 Copilot 채팅에서도 자동 컨텍스트

### GitHub Copilot 통합

워크스페이스에는 **`.github/copilot-instructions.md`** 파일이 있어서,
새 Copilot 채팅 세션을 시작할 때도 자동으로 이전 컨텍스트를 이어갑니다.

### 빠른 로드 방법

새 Copilot 채팅 창에서:

```
@workspace /file:outputs/.copilot_context_summary.md
```

입력하면 **즉시 현재 상태 요약**을 받을 수 있습니다:

- 리듬 상태
- 자율 목표 Top 3
- 시스템 건강도
- 추천 다음 행동

### 자동 생성

워크스페이스를 열 때마다 `session_continuity_restore.ps1`가
자동으로 `generate_copilot_context.ps1`를 호출하여 최신 요약을 생성합니다.

---

## 🚀 사용 방법

### 1️⃣ 자동 모드 (기본)

워크스페이스를 여는 순간 **백그라운드에서 자동 실행**됩니다.

```
VS Code 열기 → 자동으로 복원 → outputs/session_continuity_latest.md 생성
```

- **태스크**: `🔄 Session: Auto Restore Continuity`
- **설정**: `runOn: "folderOpen"` (이미 활성화됨)

### 2️⃣ 수동 실행 + 리포트 자동 열기

VS Code 명령 팔레트 (Ctrl+Shift+P):

```
Tasks: Run Task → 📖 Session: Restore + Open Report
```

또는 터미널에서:

```powershell
.\scripts\session_continuity_restore.ps1 -OpenReport
```

### 3️⃣ 조용히 실행 (로그 없이)

```powershell
.\scripts\session_continuity_restore.ps1 -Silent
```

---

## 📊 복원 리포트 예시

```markdown
# 세션 연속성 복원 리포트

**복원 시간**: 2025-11-07 12:00:00

## 최근 세션 스냅샷
- **파일**: `outputs\session_memory\session_20251107_113000.json`
- **생성**: 2025-11-07 11:30:00

## 리듬 상태
- **리포트**: `outputs\RHYTHM_REST_PHASE_20251107.md`
- **미리보기**:
  ```

# 🌊 Rhythm Rest Phase - 2025-11-07

  **상태**: 자연스러운 휴식 페이즈
  **시스템 건강도**: 90.9% EXCELLENT

  ```

## 자율 목표 시스템
- **상태**: 활성
- **총 목표**: 15
- **최근 업데이트**: 2025-11-07 11:49:44

### 최근 목표 (Top 3)
- ✅ **Increase Data Collection** (completed)
- ❌ **Execute High-Impact Goals** (failed)
- 🔄 **Monitor System Health** (in_progress)

## 코어 프로세스 상태
- **상태 파일**: `outputs\core_processes_latest.json`
- **생성**: 15.3분 전
- 상세 정보는 파일 참조

## 추천 다음 행동

1. **리듬 리포트 확인**: `outputs\RHYTHM_REST_PHASE_20251107.md` 읽기
2. **목표 계속**: 자율 목표 실행기 확인 (Goal: Execute + Open Tracker)
3. **자연스러운 흐름**: 위 추천사항은 선택사항. 지금 하고 싶은 것부터 시작하세요.

---
*자동 생성: session_continuity_restore.ps1*
```

---

## 🔧 커스터마이징

### 복원할 항목 추가/제거

`scripts/session_continuity_restore.ps1` 편집:

```powershell
# 새 항목 추가 예시
function Get-MyCustomData {
    # 여기에 로직 추가
    return $data
}

# Main Restore Logic 섹션에서 호출
$customData = Get-MyCustomData
if ($customData) {
    Write-Status "✅ Custom Data 발견"
    $report += "## My Custom Section"
    $report += "- Data: $customData"
}
```

### 자동 실행 비활성화

`.vscode/tasks.json`에서 해당 태스크 제거 또는 주석 처리:

```json
// {
//     "label": "🔄 Session: Auto Restore Continuity",
//     "runOptions": { "runOn": "folderOpen" }
// }
```

---

## 🎯 핵심 이점

1. **즉시 작업 재개**: "뭐 하고 있었더라?" 고민 없음
2. **컨텍스트 유지**: 리듬, 목표, 시스템 상태 한눈에
3. **자동화**: 수동으로 여러 명령 실행할 필요 없음
4. **추천 행동**: "다음에 뭐 할까?" 가이드 제공

---

## 📝 관련 파일

- **스크립트**: `scripts/session_continuity_restore.ps1`
- **태스크 정의**: `.vscode/tasks.json`
- **출력 리포트**: `outputs/session_continuity_latest.md`
- **세션 스냅샷**: `outputs/session_memory/*.json`
- **리듬 리포트**: `outputs/RHYTHM_*.md`
- **Goal Tracker**: `fdo_agi_repo/memory/goal_tracker.json`

---

## 🚨 문제 해결

### 자동 복원이 안 됨

1. `.vscode/tasks.json`에서 태스크 확인:

   ```json
   "runOptions": { "runOn": "folderOpen" }
   ```

2. VS Code 설정 확인:
   - `File > Preferences > Settings`
   - `Task: Auto Detect` = on

### 리포트가 생성되지 않음

터미널에서 수동 실행하여 에러 확인:

```powershell
.\scripts\session_continuity_restore.ps1 -OpenReport
```

### 추천 행동이 부족함

`scripts/session_continuity_restore.ps1`의 `$recommendations` 배열에 항목 추가:

```powershell
$recommendations += "새 추천 행동 내용"
```

---

**이제 새 창을 열 때마다 자동으로 컨텍스트가 복원됩니다!** 🎉
