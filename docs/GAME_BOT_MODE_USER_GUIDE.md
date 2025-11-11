# 🎮 게임 봇 모드 완전 가이드

## 🚀 Quick Start (3초 안에!)

### 방법 1: 키보드 단축키 (가장 빠름!)

```
Ctrl + Shift + Alt + N
```

→ 모든 게 자동으로! (복원 → 복사 → 채팅 → 붙여넣기)

### 방법 2: VS Code Task

1. `Ctrl + Shift + P`
2. "Tasks: Run Task" 검색
3. "🆕 Chat: New with Context (Quick)" 선택

### 방법 3: 명령 팔레트

1. `Ctrl + Shift + P`
2. "New Chat with Context (Quick)" 검색

---

## 📊 시스템 구성

### 1️⃣ 세션 복원 (`session_continuity_restore.ps1`)

- 리듬 상태, Goal Tracker, 코어 프로세스 로드
- `.copilot_context_summary.md` 자동 생성

### 2️⃣ 컨텍스트 길이 체크 (`check_context_length.py`)

- 토큰 수 추정 (3 chars ≈ 1 token)
- 경고: 80% 초과
- 위험: 90% 초과

### 3️⃣ 클립보드 복사

- 컨텍스트 요약 → 클립보드

### 4️⃣ 새 채팅 열기

- VS Code 명령: `workbench.action.chat.open`

### 5️⃣ 자동 붙여넣기 (`auto_paste_to_chat.py`)

- PyAutoGUI로 Ctrl+V 자동 실행
- 2초 대기 후 실행 (조정 가능)

---

## ⚙️ 설정 옵션

### 스크립트 파라미터

```powershell
# Dry-run (테스트만)
.\scripts\new_chat_with_context_quick.ps1 -DryRun

# 자동 붙여넣기 스킵 (수동 Ctrl+V)
.\scripts\new_chat_with_context_quick.ps1 -SkipPaste

# 대기 시간 조정 (밀리초)
.\scripts\new_chat_with_context_quick.ps1 -DelayMs 3000
```

### 키보드 단축키 변경

`.vscode/keybindings.json`:

```json
{
  "key": "ctrl+shift+alt+n",  // 원하는 키 조합
  "command": "workbench.action.tasks.runTask",
  "args": "🆕 Chat: New with Context (Quick)"
}
```

### 컨텍스트 길이 임계값 조정

`scripts/new_chat_with_context_quick.ps1`:

```powershell
# 현재: check_context_length.py --file ... --json
# 변경: --warn-threshold 0.7 --critical-threshold 0.85
```

---

## 🔍 트러블슈팅

### ❌ "pyautogui not found"

```powershell
# Task 실행: "📦 Chat: Install Python Deps (pyautogui)"
# 또는:
pip install pyautogui pyperclip
```

### ❌ "자동 붙여넣기 실패"

**원인:**

- 채팅 입력창이 포커스 안 됨
- 대기 시간 부족

**해결:**

```powershell
# 대기 시간 늘리기
.\scripts\new_chat_with_context_quick.ps1 -DelayMs 3000

# 또는 수동 모드
.\scripts\new_chat_with_context_quick.ps1 -SkipPaste
# → Ctrl+V로 직접 붙여넣기
```

### ❌ "컨텍스트 너무 김"

**자동 경고:**

- 80% 초과: 노란색 경고 (계속 진행 가능)
- 90% 초과: 빨간색 위험 (확인 필요)

**해결:**

1. 중요한 부분만 선택적으로 복사
2. 자동 요약 기능 사용 (향후 추가)
3. 컨텍스트 정리 후 재시도

### ❌ "키보드 단축키 안 먹힘"

**확인 사항:**

1. `.vscode/keybindings.json` 파일 존재?
2. VS Code 재시작 했는지?
3. 다른 확장과 키 충돌?

**해결:**

```powershell
# VS Code 명령 팔레트로 대신 사용
Ctrl + Shift + P → "New Chat with Context"
```

---

## 📈 성능 모니터링

### 컨텍스트 길이 수동 체크

```powershell
python scripts/check_context_length.py `
  --file outputs/.copilot_context_summary.md

# JSON 출력
python scripts/check_context_length.py `
  --file outputs/.copilot_context_summary.md `
  --json

# 파일 저장
python scripts/check_context_length.py `
  --file outputs/.copilot_context_summary.md `
  --json `
  --out outputs/context_length_latest.json
```

### 로그 확인

- **세션 복원:** `outputs/session_continuity_latest.md`
- **컨텍스트 요약:** `outputs/.copilot_context_summary.md`
- **길이 체크:** `outputs/context_length_latest.json`

---

## 🎯 워크플로우 예시

### 일반적인 사용 (99%)

```
1. Ctrl + Shift + Alt + N
2. Enter 누르기
3. 대화 시작!
```

### 신중한 사용 (안전 우선)

```
1. Task: "📖 Session: Restore + Open Report"
   → 현재 상태 확인

2. 컨텍스트 길이 체크:
   python scripts/check_context_length.py --file outputs/.copilot_context_summary.md

3. 괜찮으면:
   Ctrl + Shift + Alt + N

4. 길면:
   - 중요 부분만 수동 복사
   - 또는 요약 후 진행
```

### 디버깅 모드

```powershell
# 1. Dry-run 테스트
.\scripts\new_chat_with_context_quick.ps1 -DryRun

# 2. 자동 붙여넣기 스킵
.\scripts\new_chat_with_context_quick.ps1 -SkipPaste

# 3. 대기 시간 조정
.\scripts\new_chat_with_context_quick.ps1 -DelayMs 5000

# 4. 개별 단계 수동 실행
.\scripts\session_continuity_restore.ps1 -OpenReport
python scripts/check_context_length.py --file outputs/.copilot_context_summary.md
Get-Content outputs/.copilot_context_summary.md | Set-Clipboard
code --command "workbench.action.chat.open"
# Ctrl+V
```

---

## 🔮 향후 개선 계획

### Phase 1: 자동 요약 (진행 중)

- [ ] 컨텍스트 90% 초과 시 자동 요약
- [ ] LLM으로 중요 부분만 추출
- [ ] 요약 전/후 비교 리포트

### Phase 2: 지능형 분할

- [ ] 대화 주제별 컨텍스트 분리
- [ ] 멀티 채팅 자동 관리
- [ ] 컨텍스트 우선순위 자동 조정

### Phase 3: 학습 기능

- [ ] 사용 패턴 분석
- [ ] 최적 대기 시간 자동 조정
- [ ] 개인화된 임계값 설정

---

## 📚 관련 문서

- **전체 시스템:** `GAME_BOT_MODE_COMPLETE.md`
- **세션 복원:** `docs/NEW_CHAT_WITH_CONTEXT_QUICK_START.md`
- **자동화 가이드:** `.github/copilot-instructions.md`

---

## 💡 팁 & 트릭

### 🚀 더 빠르게

- 키보드 단축키 외우기: `Ctrl + Shift + Alt + N`
- VS Code 시작 시 자동 복원 활성화됨

### 🎯 더 정확하게

- 중요 파일은 `@workspace /file:...`로 명시
- 너무 긴 컨텍스트는 수동 편집

### 🔧 더 안정적으로

- Dry-run으로 먼저 테스트
- 대기 시간 여유있게 (느린 PC는 3초+)

---

## ❓ FAQ

**Q: 왜 "게임 봇 모드"인가요?**
A: 클립보드 복사 → 채팅 열기 → 자동 붙여넣기가 게임 매크로처럼 자동으로 돌아가서!

**Q: 매번 실행해야 하나요?**
A: 새 채팅 시작할 때만! 기존 채팅은 그냥 계속 쓰면 됩니다.

**Q: 컨텍스트가 너무 길면?**
A: 80% 넘으면 경고, 90% 넘으면 확인 요청. 중요한 부분만 수동 선택하거나 요약 사용.

**Q: 자동 붙여넣기 안 되면?**
A: `-SkipPaste` 옵션 쓰고 수동으로 `Ctrl+V`. 또는 대기 시간 늘리기.

**Q: 키보드 단축키 변경?**
A: `.vscode/keybindings.json` 파일 편집.

---

**🎮 이제 게임처럼 편하게 Copilot을 사용하세요!**
