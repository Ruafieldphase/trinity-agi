# 🆕 새 Copilot 채팅 + 컨텍스트 자동 로드

**이전 작업을 자동으로 이어가는 가장 빠른 방법!**

---

## ⚡ 빠른 시작 (3초!)

### 방법 1: VS Code Task 실행

```
Ctrl+Shift+P → Tasks: Run Task → 🆕 Chat: New with Context (Quick)
```

**자동으로**:

1. ✅ 컨텍스트가 클립보드에 복사됨
2. ✅ 새 Copilot 채팅 창 열림
3. ✅ `Ctrl+V` → `Enter`로 붙여넣기!

---

### 방법 2: 키보드 단축키 (추천!)

**설정 방법**:

1. `File > Preferences > Keyboard Shortcuts` 열기
2. 오른쪽 상단 파일 아이콘 클릭 (JSON 편집)
3. 다음 추가:

```json
[
    {
        "key": "ctrl+shift+alt+n",
        "command": "workbench.action.tasks.runTask",
        "args": "🆕 Chat: New with Context (Quick)"
    }
]
```

**사용**:

```
Ctrl+Shift+Alt+N → 새 채팅 + 컨텍스트 자동 로드!
```

---

### 방법 3: PowerShell 직접 실행

```powershell
.\scripts\new_chat_with_context.ps1
```

**옵션**:

- 기본: 간단 요약 (`.copilot_context_summary.md`)
- 상세: `.\scripts\new_chat_with_context.ps1 -ContextFile "outputs\session_continuity_latest.md"`

---

## 📋 사용 가능한 Tasks

| Task | 컨텍스트 소스 | 추천 용도 |
|------|--------------|----------|
| **🆕 Chat: New with Context (Quick)** | `.copilot_context_summary.md` | 일반 작업 재개 |
| **🆕 Chat: New with Full Report** | `session_continuity_latest.md` | 복잡한 문제, 전체 컨텍스트 필요 |

---

## 🎯 워크플로우 예시

### 아침 시작

```
1. VS Code 열기 → 자동 복원
2. Ctrl+Shift+Alt+N → 새 채팅
3. Ctrl+V → Enter
4. "오늘 뭐 할까?" 입력
```

### 점심 후 재개

```
1. Ctrl+Shift+Alt+N
2. Ctrl+V → "이어서" 입력
```

### 복잡한 디버깅

```
1. Ctrl+Shift+P → Tasks: Run Task
2. "🆕 Chat: New with Full Report" 선택
3. Ctrl+V → 상세 컨텍스트로 시작
```

---

## 🔧 커스터마이징

### 다른 컨텍스트 파일 사용

```powershell
.\scripts\new_chat_with_context.ps1 -ContextFile "docs/CURRENT_WORK.md"
```

### 클립보드 복사 건너뛰기

```powershell
.\scripts\new_chat_with_context.ps1 -NoClipboard
```

---

## 📚 관련 문서

- **상세 가이드**: `docs/SESSION_CONTINUITY_GUIDE.md`
- **Copilot 지침**: `.github/copilot-instructions.md`
- **스크립트 소스**: `scripts/new_chat_with_context.ps1`

---

## 🐛 문제 해결

### "채팅 창이 자동으로 열리지 않아요"

수동으로 열어주세요:

- `Ctrl+Shift+I` (Copilot Chat)
- 또는 View > Command Palette > "Chat: Focus on Chat View"

컨텍스트는 이미 클립보드에 복사되어 있으므로 `Ctrl+V`로 붙여넣기만 하면 됩니다!

### "컨텍스트 파일이 없다고 나와요"

먼저 세션 복원 실행:

```powershell
.\scripts\session_continuity_restore.ps1
```

또는

```
Tasks: Run Task → 📖 Session: Restore + Open Report
```

---

**💡 Tip**: 가장 빠른 방법은 **키보드 단축키 설정**! 한 번 설정하면 `Ctrl+Shift+Alt+N` 한 번으로 모든 것이 준비됩니다! 🚀
