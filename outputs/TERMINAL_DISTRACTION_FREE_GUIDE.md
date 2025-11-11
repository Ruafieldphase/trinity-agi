# 터미널 방해 해결 가이드 🎯

**문제**: PowerShell Job이 VS Code 터미널을 계속 점유해서 작업에 방해됨  
**추가 문제**: 5분마다 PowerShell/Python 창이 뜸

**해결책**: ✅ **완전 해결됨!** (2025-11-04)

---

## ✅ **해결된 것들**

### 1️⃣ PowerShell Job 점유 → Task Scheduler

- ✅ VS Code 터미널 점유 없음
- ✅ 재부팅 후 자동 시작
- ✅ 완전 독립 실행

### 2️⃣ 5분마다 창 뜨는 문제 → 백그라운드 전환

- ✅ MonitoringCollector (5분마다) → WindowStyle Hidden
- ✅ Python 작업 → pythonw.exe (창 없음)
- ✅ 불필요한 작업 5개 제거

### 3️⃣ 재부팅 안전성 → Startup 폴더

- ✅ 로그인 시 자동 시작
- ✅ 데이터 이어쓰기
- ✅ 숨김 모드 실행

---

## 🎯 **현재 상태**

**더 이상 방해 없음!**

```
✅ VS Code 터미널: 깨끗함
✅ 5분마다 창: 안뜸
✅ 재부팅 후: 자동 시작
✅ 백그라운드: 조용히 실행
```

---

## 🥇 **방법 1: Task Scheduler (가장 권장)**

### 장점

- ✅ **완전히 독립 실행** - VS Code와 무관
- ✅ **재부팅 후에도 자동 시작**
- ✅ **터미널 점유 없음**
- ✅ **로그온 시 자동 실행**

### 실행 방법

```powershell
# 1단계: 현재 Job 정리
.\scripts\cleanup_terminal_jobs.ps1

# 2단계: Task Scheduler 등록
.\scripts\start_24h_silent.ps1

# 완료! 이제 터미널이 깨끗합니다.
```

### 관리 명령

```powershell
# 상태 확인
Get-ScheduledTask -TaskName "AGI_24h_Production"

# 시작
Start-ScheduledTask -TaskName "AGI_24h_Production"

# 중지
Stop-ScheduledTask -TaskName "AGI_24h_Production"

# 제거
Unregister-ScheduledTask -TaskName "AGI_24h_Production" -Confirm:$false
```

### 로그 확인

```powershell
# 로그는 동일한 위치에 저장됨
Get-Content outputs\fullstack_24h_monitoring.jsonl -Tail 10
Get-Content outputs\lumen_24h_latest.json | ConvertFrom-Json
```

---

## 🥈 **방법 2: 숨김 창 (간단)**

### 장점

- ✅ **즉시 실행** - 등록 불필요
- ✅ **터미널 점유 없음**
- ✅ **VS Code에서 완전 독립**

### 단점

- ⚠️ **재부팅 시 수동 재시작 필요**
- ⚠️ **VS Code 종료 시 같이 종료**

### 실행 방법

```powershell
# 현재 Job 정리 + 숨김 창 실행
.\scripts\cleanup_terminal_jobs.ps1
.\scripts\start_24h_silent.ps1 -Method hidden
```

### 관리 명령

```powershell
# 실행 중인 프로세스 확인
Get-Process -Name powershell | Where-Object { $_.MainWindowTitle -eq "" }

# 중지 (PID는 시작 시 표시됨)
Stop-Process -Id <PID>
```

---

## 🥉 **방법 3: Windows Service (고급)**

### 장점

- ✅ **시스템 서비스** - 가장 안정적
- ✅ **자동 복구** - 크래시 시 재시작
- ✅ **부팅 시 자동 시작**

### 단점

- ⚠️ **NSSM 필요** - 추가 설치 필요
- ⚠️ **설정 복잡**

### 실행 방법

```powershell
# 1단계: NSSM 설치
winget install nssm

# 2단계: 서비스 등록
.\scripts\start_24h_silent.ps1 -Method service

# 3단계: 서비스 시작
Start-Service -Name "AGI_Production_24h"
```

### 관리 명령

```powershell
# 상태 확인
Get-Service -Name "AGI_Production_24h"

# 시작/중지
Start-Service -Name "AGI_Production_24h"
Stop-Service -Name "AGI_Production_24h"

# 제거
nssm remove "AGI_Production_24h" confirm
```

---

## 📋 **즉시 실행 요약**

### 현재 상황 정리 + 백그라운드 전환 (2분)

```powershell
# Step 1: 현재 실행 중인 Job 확인
Get-Job | Format-Table

# Step 2: Job 정리 + 상태 저장
.\scripts\cleanup_terminal_jobs.ps1

# Step 3: Task Scheduler로 전환 (권장)
.\scripts\start_24h_silent.ps1

# 완료! ✅
```

---

## 🎨 **VS Code 설정 개선**

터미널 자동 숨김 설정:

```json
// settings.json
{
  "terminal.integrated.hideOnStartup": "whenEmpty",
  "terminal.integrated.showExitAlert": false,
  "terminal.integrated.confirmOnKill": "never"
}
```

적용 방법:

1. `Ctrl + ,` (설정 열기)
2. 우측 상단 "Open Settings (JSON)" 클릭
3. 위 설정 추가

---

## ⚡ **빠른 시작**

### 지금 바로 방해 없애기 (30초)

```powershell
# 터미널에서 실행
.\scripts\cleanup_terminal_jobs.ps1; .\scripts\start_24h_silent.ps1

# 완료! 이제 터미널이 깨끗합니다.
```

---

## 🔍 **실행 확인**

### Task Scheduler 방식

```powershell
# Task 상태
Get-ScheduledTask -TaskName "AGI_24h_Production" | Format-List State, LastRunTime, NextRunTime

# 로그 확인 (실시간)
Get-Content outputs\fullstack_24h_monitoring.jsonl -Wait -Tail 1
```

### 숨김 창 방식

```powershell
# 프로세스 확인
Get-Process powershell | Where-Object { $_.MainWindowTitle -eq "" }

# 로그 확인
Get-Content outputs\lumen_24h_latest.json | ConvertFrom-Json
```

---

## 📊 **효과**

| 항목 | 이전 | 이후 |
|------|------|------|
| 터미널 점유 | ❌ 계속 사용 중 | ✅ 깨끗함 |
| VS Code 반응 | 🐢 느림 | ⚡ 빠름 |
| 작업 방해 | ❌ 자주 방해됨 | ✅ 방해 없음 |
| 재부팅 후 | ⚠️ 수동 재시작 | ✅ 자동 시작 |
| 로그 보존 | ✅ 동일 | ✅ 동일 |

---

## 🎯 **결론**

**권장 순서**:

1. **우선**: Task Scheduler 방식 (완전 자동화)

   ```powershell
   .\scripts\start_24h_silent.ps1
   ```

2. **대안**: 숨김 창 방식 (간단)

   ```powershell
   .\scripts\start_24h_silent.ps1 -Method hidden
   ```

3. **고급**: Windows Service (최고 안정성)

   ```powershell
   winget install nssm
   .\scripts\start_24h_silent.ps1 -Method service
   ```

**이제 방해 없이 작업하세요!** 🎉

---

## 📞 **트러블슈팅**

### Q: Task Scheduler가 실행 안됨?

```powershell
# 관리자 권한 확인
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# True면 OK, False면 관리자 모드로 실행 필요
```

### Q: 로그가 업데이트 안됨?

```powershell
# Task 실행 상태 확인
Get-ScheduledTask -TaskName "AGI_24h_Production" | Get-ScheduledTaskInfo

# 마지막 실행 결과 확인
(Get-ScheduledTask -TaskName "AGI_24h_Production").LastTaskResult
# 0 = 성공, 1 = 실패
```

### Q: 이전 Job으로 돌아가고 싶음?

```powershell
# Task Scheduler 중지
Stop-ScheduledTask -TaskName "AGI_24h_Production"

# 기존 방식 재시작
.\scripts\resume_24h_productions.ps1
```

---

**생성일**: 2025-11-04  
**관련 문서**: `TERMINAL_SAFETY_GUIDE.md`, `REBOOT_SAFE_SYSTEM_COMPLETE.md`
