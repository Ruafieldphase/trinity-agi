# GitHub Copilot Instructions for AGI Workspace

## 🚀 빠른 시작 (새 채팅창)

**새 채팅에서 이 한 줄만 입력하세요:**
```
복원
```
또는
```
@workspace /file:outputs/.copilot_context_summary.md
```

---

## 🤖 자동 세션 컨텍스트 로딩

새 Copilot 채팅 세션을 시작할 때, 항상 다음 파일들을 먼저 확인하세요:

### 1. 📖 세션 연속성 리포트 (우선순위 높음)
```
@workspace /file:outputs/session_continuity_latest.md
```
- 최근 세션 상태 스냅샷
- 리듬 상태 요약
- 자율 목표 진행 상황
- 추천 다음 행동

### 2. 🌊 리듬 상태 (현재 컨텍스트)
```
@workspace /file:outputs/RHYTHM_REST_PHASE_20251107.md
@workspace /file:outputs/RHYTHM_SYSTEM_STATUS_REPORT.md
```
- 시스템 건강도
- 현재 작업 리듬
- 휴식/집중 페이즈

### 3. 🎯 자율 목표 트래커
```
@workspace /file:fdo_agi_repo/memory/goal_tracker.json
```
- 진행 중인 목표
- 완료/실패 목표
- 다음 실행 계획

### 4. ⚙️ 시스템 상태
```
@workspace /file:outputs/core_processes_latest.json
@workspace /file:outputs/quick_status_latest.json
```
- RPA Worker 상태
- Task Queue Server
- Watchdog, Monitor

### 5. 📝 에이전트 핸드오프
```
@workspace /file:docs/AGENT_HANDOFF.md
@workspace /file:AGENTS.md
```
- 최근 변경사항
- 다음 작업 항목

---

## 🚀 시작 시 자동 실행 체크리스트

새 채팅 세션에서 첫 응답 시:

1. ✅ `outputs/session_continuity_latest.md` 읽기
2. ✅ 리듬 상태 확인
3. ✅ Goal Tracker 최근 3개 요약
4. ✅ "지금 작업할 내용" 제안

**예시 응답 형식**:
```
🔄 세션 컨텍스트 복원 완료

📍 현재 상태:
- 리듬: 휴식 페이즈 (90.9% EXCELLENT)
- 목표: 4개 활성 (최근 2개 완료, 1개 실패)
- 시스템: 정상 (7분 전 체크)

💡 추천 다음 행동:
1. 리듬 리포트 확인
2. 실패한 목표 재시도
3. 자연스러운 흐름 유지

무엇을 도와드릴까요?
```

---

## 📋 컨텍스트 우선순위

1. **세션 연속성 리포트** - 가장 최근 상태
2. **Goal Tracker** - 진행 중인 작업
3. **리듬 상태** - 현재 에너지 레벨
4. **AGENT_HANDOFF.md** - 핸드오프 정보
5. **시스템 상태** - 프로세스 헬스

---

## 🎯 사용자 요청 해석 가이드

### "이어서 해줘" / "계속해줘"
→ Goal Tracker에서 `in_progress` 또는 `failed` 목표 확인

### "지금 뭐 해야 돼?"
→ `session_continuity_latest.md`의 "추천 다음 행동" 참조

### "상태 알려줘"
→ 리듬 + Goal + 시스템 상태 요약

### "새로 시작할게"
→ Goal Generator 실행 제안

---

## 🔧 자동화 명령어

사용자가 다음 키워드 사용 시 자동 액션:

- **"복원"** / **"컨텍스트"** / **"이어서"** → `.copilot_context_summary.md` 읽고 상태 요약
  - 리듬, 목표, 시스템 상태 한눈에 표시
  - 추천 다음 행동 제시
- **"리듬"** → RHYTHM 파일들 확인
- **"목표"** → goal_tracker.json 요약
- **"상태"** → quick_status + core_processes

---

**이 지침은 모든 Copilot 채팅 세션에서 자동으로 적용됩니다.**
