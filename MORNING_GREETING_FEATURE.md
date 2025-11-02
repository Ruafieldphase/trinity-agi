# Morning Greeting Feature 🌅

## 개요

이제 **"좋은 아침이야"**라고 말하면 자동으로 Morning Kickoff가 실행됩니다!

## 사용 방법

### 1. ChatOps 명령어로

```powershell
# 터미널에서
$env:CHATOPS_SAY = "좋은 아침이야"
.\scripts\chatops_router.ps1

# 또는 English
$env:CHATOPS_SAY = "good morning"
.\scripts\chatops_router.ps1
```

### 2. VS Code Task로

**Task: `ChatOps: 좋은 아침 🌅`**

1. `Ctrl+Shift+P`
2. "Tasks: Run Task"
3. "ChatOps: 좋은 아침 🌅" 선택

### 3. 지원되는 인사말

다음 표현들이 모두 작동합니다:

| 한국어 | English |
|--------|---------|
| 좋은 아침 | good morning |
| 좋은 아침이야 | morning |
| 굿모닝 | - |
| 아침이야 | - |

## Morning Kickoff가 하는 일

```
1. 🌅 시스템 인사
2. 📊 최근 1시간 모니터링 리포트 생성
3. ✨ 대시보드 업데이트
   - outputs/monitoring_dashboard_latest.html
   - outputs/monitoring_report_latest.md
4. 💡 다음 단계 안내
```

## 자동 실행 vs 수동 인사

### 자동 (Scheduled Task)

```
매일 10:00 → Morning Kickoff 자동 실행
```

- 컴퓨터가 켜져 있으면 정확히 10:00에 실행
- 컴퓨터가 꺼져 있으면 다음 부팅 시 실행

### 수동 (ChatOps)

```
사용자: "좋은 아침이야"
시스템: Morning Kickoff 즉시 실행
```

- 원하는 시간에 언제든지 실행 가능
- 10시 전에 일찍 시작할 때 유용

## 예시 워크플로우

### 시나리오 1: 일찍 출근

```
08:30  → 컴퓨터 부팅
08:31  → "좋은 아침이야" (ChatOps)
         → Morning Kickoff 실행 완료
08:35  → 작업 시작
```

### 시나리오 2: 정시 출근

```
09:55  → 컴퓨터 부팅
10:00  → Morning Kickoff 자동 실행
10:05  → 작업 시작
```

### 시나리오 3: 늦은 출근

```
12:00  → 컴퓨터 부팅
12:00  → Morning Kickoff 자동 실행 (missed task)
12:05  → 작업 시작
```

## 기술적 세부사항

### 구현 위치

1. **Intent 매칭**: `scripts/chatops_intent.py`
   ```python
   # Morning Kickoff
   if re.search(r"(좋은\s*아침|굿\s*모닝|good\s*morning|아침이야)", u):
       return "morning_kickoff"
   ```

2. **Action 핸들러**: `scripts/chatops_router.ps1`
   ```powershell
   function Start-MorningKickoff {
       # Morning Kickoff 실행 로직
   }
   ```

3. **라우팅**: `chatops_router.ps1` switch 문
   ```powershell
   '^morning_kickoff$' {
       Info '[Action] 🌅 Morning Kickoff'
       exit (Run-And-Report { Start-MorningKickoff })
   }
   ```

### 이벤트 로깅

모든 Morning Kickoff 실행은 자동으로 기록됩니다:

```
outputs/chatops_events.jsonl
```

## 장점

### 1. 자연스러운 인터페이스

```
"좋은 아침이야" → 시스템 시작
```

복잡한 명령어 대신 자연어 인사로 작업 시작

### 2. 유연한 실행 시간

- 자동: 매일 10:00
- 수동: 원하는 시간에

### 3. 일관된 워크플로우

```
인사 → 리포트 생성 → 작업 시작
```

매일 같은 리듬으로 하루 시작

## 다음 단계

Morning Kickoff 후 추천 명령어:

```powershell
# 1. 시스템 상태 확인
$env:CHATOPS_SAY = "AGI 상태 보여줘"
.\scripts\chatops_router.ps1

# 2. 통합 대시보드
$env:CHATOPS_SAY = "통합 대시보드"
.\scripts\chatops_router.ps1

# 3. 24시간 요약
$env:CHATOPS_SAY = "AGI 24시간 요약"
.\scripts\chatops_router.ps1
```

## 참고 문서

- [Morning Kickoff 자동화](./MORNING_KICKOFF_AUTOMATION_COMPLETE.md)
- [ChatOps 가이드](./docs/CHATOPS_GUIDE.md)
- [Agent Handoff](./docs/AGENT_HANDOFF.md)

---

**🌅 좋은 아침입니다!**

이제 시스템이 당신의 인사에 응답합니다.
