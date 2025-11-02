# 🔧 AI 자율 관리 시스템 최종 활성화 가이드

**날짜**: 2025-11-02  
**상태**: ExecutionPolicy 변경 완료 ✅  
**다음 단계**: 관리자 권한으로 Watchdog + Master Orchestrator 등록

---

## ✅ 이미 완료된 것들

AI가 자동으로 처리한 것:

- ✅ Task Queue Server 예약 작업 등록
- ✅ Task Queue Server 프로세스 시작  
- ✅ RPA Worker 프로세스 시작
- ✅ Python venv 확인
- ✅ 모든 헬스 체크

---

## 🔐 관리자 권한 필요 (마지막 2단계)

### 1️⃣ Watchdog 등록

**관리자 PowerShell**에서 실행:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\workspace\agi\scripts\register_watchdog_task.ps1" -Register
```

**역할**: 프로세스 감시 + 자동 복구

---

### 2️⃣ Master Orchestrator 등록

**관리자 PowerShell**에서 실행:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\workspace\agi\scripts\register_master_orchestrator.ps1" -Register
```

**역할**: 모든 핵심 시스템 자동 시작 (부팅 시 또는 로그온 시)

---

## 🎯 실행 방법

### Option A: VS Code Tasks 사용 (권장)

1. **Ctrl+Shift+P** → "Tasks: Run Task" 검색
2. 다음 태스크를 **관리자 권한 PowerShell**에서 실행:
   - `🤖 AGI: Register Watchdog (Boot)`
   - `🤖 AGI: Register Master Orchestrator (Boot)`

### Option B: 수동 실행

1. **시작 메뉴** → **PowerShell** 우클릭 → **관리자 권한으로 실행**

2. **Watchdog 등록**:

   ```powershell
   cd C:\workspace\agi
   .\scripts\register_watchdog_task.ps1 -Register
   ```

3. **Master Orchestrator 등록**:

   ```powershell
   .\scripts\register_master_orchestrator.ps1 -Register
   ```

4. **확인**:

   ```powershell
   # Watchdog 상태
   .\scripts\register_watchdog_task.ps1 -Status
   
   # Master Orchestrator 상태
   .\scripts\register_master_orchestrator.ps1 -Status
   ```

---

## ✅ 등록 후 확인

VS Code에서 Bootstrap 재실행:

```
Ctrl+Shift+P → Tasks: Run Task → 🤖 AI: Bootstrap Self-Managing System (Once)
```

**예상 결과**:

```
✅ AI Self-Managing System ACTIVATED
All dependencies running!
AI now manages everything.
```

---

## 🎊 완료 후

**AI가 자동으로 관리하는 것**:

- ✅ Task Queue Server (8091) 자동 시작/복구
- ✅ RPA Worker 자동 시작/복구  
- ✅ Watchdog 자동 감시 (60초마다)
- ✅ Master Orchestrator 자동 실행 (부팅/로그온 시)
- ✅ Monitoring Collector 예약 실행

**사용자가 하는 것**:

- ✅ 코딩에만 집중! 🚀

---

## 🐛 문제 해결

### 문제: "Access Denied" 에러

**원인**: 관리자 권한이 아닌 일반 PowerShell에서 실행

**해결**:

1. PowerShell을 **관리자 권한으로 다시 시작**
2. 위 명령어 재실행

### 문제: 스크립트 실행 정책 에러

**원인**: 이미 해결됨! (`RemoteSigned`로 변경 완료)

### 문제: 등록은 되는데 실행이 안됨

**확인**:

```powershell
# Scheduled Task 상태 확인
Get-ScheduledTask -TaskName "*Watchdog*" | Format-List
Get-ScheduledTask -TaskName "*Orchestrator*" | Format-List
```

**수동 실행**:

```powershell
# Watchdog 수동 실행 테스트
Start-ScheduledTask -TaskName "AGI_Watchdog"

# Master Orchestrator 수동 실행 테스트  
Start-ScheduledTask -TaskName "AGI_Master_Orchestrator"
```

---

## 📚 참고

- 전체 가이드: `SELF_MANAGING_SYSTEM.md`
- 통합 리포트: `SELF_MANAGING_INTEGRATION_COMPLETE.md`
- AI 상태 확인: VS Code Task → `🤖 AI: Check Self-Managing Status`

---

**다음**: 위 2개 명령어만 실행하면 AI 완전 자율 모드 활성화! 🎉
