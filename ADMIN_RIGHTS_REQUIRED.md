# 🔐 관리자 권한 필요 - 해결 방법

**문제**: "Access is denied" 에러 발생
**원인**: 일반 PowerShell에서 실행 (관리자 권한 아님)
**해결**: 관리자 권한 PowerShell에서 실행 필요

---

## ✅ 올바른 실행 방법

### 1️⃣ 관리자 PowerShell 열기

**방법 A**: 시작 메뉴 사용

1. **Windows 키** 누르기
2. **"PowerShell"** 타이핑
3. **Windows PowerShell** 우클릭
4. **"관리자 권한으로 실행"** 클릭

**방법 B**: 단축키 사용

1. **Win + X** 누르기
2. **"Windows PowerShell (관리자)"** 클릭

**방법 C**: 검색 사용

1. 작업 표시줄 검색창에 **"PowerShell"** 입력
2. **"관리자 권한으로 실행"** 클릭

---

### 2️⃣ 작업 디렉토리 이동

관리자 PowerShell에서:

```powershell
cd C:\workspace\agi
```

---

### 3️⃣ Watchdog 등록

```powershell
.\scripts\register_watchdog_task.ps1 -Register
```

**예상 출력**:

```
✓ Task 'AgiWatchdog' registered successfully
```

---

### 4️⃣ Master Orchestrator 등록

```powershell
.\scripts\register_master_orchestrator.ps1 -Register
```

**예상 출력**:

```
✓ Task 'AgiMasterOrchestrator' registered successfully
```

---

### 5️⃣ 등록 확인

```powershell
# Watchdog 상태 확인
.\scripts\register_watchdog_task.ps1 -Status

# Master Orchestrator 상태 확인
.\scripts\register_master_orchestrator.ps1 -Status
```

---

## 🎯 한 번에 실행 (복사 & 붙여넣기)

**관리자 PowerShell**에서 아래 전체를 복사해서 실행:

```powershell
# 작업 디렉토리 이동
cd C:\workspace\agi

# Watchdog 등록
Write-Host "`n[1/2] Registering Watchdog..." -ForegroundColor Cyan
.\scripts\register_watchdog_task.ps1 -Register

# Master Orchestrator 등록
Write-Host "`n[2/2] Registering Master Orchestrator..." -ForegroundColor Cyan
.\scripts\register_master_orchestrator.ps1 -Register

# 등록 확인
Write-Host "`n✓ Registration Complete! Checking status..." -ForegroundColor Green
Get-ScheduledTask -TaskName "*Agi*" | Format-Table TaskName, State, LastRunTime

Write-Host "`n🎉 AI Self-Managing System is now ACTIVE!" -ForegroundColor Green
```

---

## ✅ 완료 후

일반 PowerShell (또는 VS Code)로 돌아가서 Bootstrap 재실행:

```powershell
# VS Code Terminal에서:
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\workspace\agi\scripts\bootstrap_autonomous_system.ps1"
```

**또는 VS Code Task**:

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

## 🐛 여전히 "Access Denied"가 나온다면?

### 원인 1: UAC (사용자 계정 컨트롤) 설정

**확인**:

```powershell
# 현재 관리자 권한 확인
([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
```

**True** = 관리자 권한 O  
**False** = 관리자 권한 X → PowerShell 재시작 필요

### 원인 2: Windows 계정 권한 부족

**해결**: Windows 관리자 계정으로 로그인 또는 IT 담당자에게 문의

### 원인 3: 그룹 정책 제한

**확인**:

```powershell
gpedit.msc
```

→ "작업 스케줄러" 관련 정책 확인

---

## 📚 참고

- Scheduled Task는 Windows 시스템 리소스를 사용하므로 반드시 관리자 권한 필요
- 한 번만 등록하면 이후 AI가 자동으로 모든 것 관리
- 재부팅 후에도 자동 실행됨

---

## 🎊 성공 시나리오

```
1. 관리자 PowerShell 열기                  ✅
2. cd C:\workspace\agi                      ✅
3. Watchdog 등록                            ✅
4. Master Orchestrator 등록                 ✅
5. VS Code에서 Bootstrap 재실행            ✅
6. AI 완전 자율 모드 활성화! 🎉            ✅
```

---

**다음**: 관리자 PowerShell에서 위 명령어를 실행해주세요! 😊
