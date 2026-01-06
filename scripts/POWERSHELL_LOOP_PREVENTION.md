# PowerShell 무한 루프 방지 가이드

## 🚨 문제 상황 (2025-12-15 발생)

PowerShell 창이 계속해서 새로 생성되는 문제가 발생했습니다.

### 원인
- `start_agi_system.ps1`과 `start_core_24h_new_window.ps1` 등의 스크립트가 `Start-Process powershell -NoExit`를 사용
- 자동 재시작 로직이나 무한 루프가 있는 스크립트들이 동시에 실행됨
- 각 스크립트가 새 PowerShell 창을 계속 생성

### 문제가 있는 패턴
```powershell
# 위험한 패턴 - 새 창을 계속 생성할 수 있음
Start-Process powershell -ArgumentList "-NoExit", "-Command", $command

# 무한 루프와 결합되면 더욱 위험
while ($true) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $command
    Start-Sleep -Seconds 5
}
```

## ✅ 해결 방법

### 즉시 조치 (긴급 상황)
```powershell
# 긴급 중지 스크립트 실행
.\agi\scripts\emergency_stop_all_powershell.ps1
```

### 수동 중지 방법
1. **작업 관리자 사용** (Ctrl + Shift + Esc)
   - "프로세스" 탭에서 "powershell.exe" 모두 선택
   - "작업 끝내기" 클릭

2. **CMD에서 강제 종료**
   ```cmd
   taskkill /F /IM powershell.exe
   ```

3. **관리자 PowerShell에서**
   ```powershell
   Get-Process powershell | Where-Object {$_.Id -ne $PID} | Stop-Process -Force
   ```

## 🛡️ 재발 방지 조치

### 1. 스크립트 작성 시 주의사항

#### ❌ 피해야 할 패턴
```powershell
# 나쁜 예 1: 무한 루프 + 새 창 생성
while ($true) {
    Start-Process powershell -NoExit -Command "..."
}

# 나쁜 예 2: 조건 없는 재귀 실행
Start-Process powershell -NoExit -Command ".\this_same_script.ps1"
```

#### ✅ 안전한 패턴
```powershell
# 좋은 예 1: 현재 세션에서 실행 (새 창 없음)
Invoke-Expression $command

# 좋은 예 2: 백그라운드 작업 사용
Start-Job -ScriptBlock { ... }

# 좋은 예 3: 종료 조건이 있는 루프
$maxRetries = 5
$retryCount = 0
while ($retryCount -lt $maxRetries) {
    # 작업 수행
    $retryCount++
}

# 좋은 예 4: 새 창이 필요한 경우 PID 추적
$proc = Start-Process powershell -ArgumentList "-NoExit", "-Command", $command -PassThru
# PID를 파일에 저장하여 나중에 중지 가능
$proc.Id | Out-File ".\running_process.pid"
```

### 2. 자동 시작 스크립트 관리

#### 확인 항목
- [ ] Windows 시작프로그램에 AGI 스크립트가 등록되어 있는가?
- [ ] Task Scheduler에 자동 실행 작업이 있는가?
- [ ] 스크립트 내부에 자동 재시작 로직이 있는가?

#### 점검 명령어
```powershell
# Task Scheduler 확인
Get-ScheduledTask | Where-Object {$_.TaskPath -like '*agi*'}

# 시작프로그램 확인
Get-ItemProperty HKCU:\Software\Microsoft\Windows\CurrentVersion\Run

# 실행 중인 PowerShell 프로세스 확인
Get-Process powershell* | Select-Object Id, ProcessName, StartTime, CPU
```

### 3. 안전한 스크립트 실행 체크리스트

스크립트를 실행하기 전에:
- [ ] 스크립트에 `while ($true)` 또는 무한 루프가 있는가?
- [ ] `Start-Process powershell -NoExit`를 사용하는가?
- [ ] 종료 조건이 명확한가?
- [ ] 프로세스 추적 메커니즘이 있는가?
- [ ] 긴급 중지 방법을 알고 있는가?

## 📋 문제가 있는 스크립트 목록

다음 스크립트들은 새 창을 생성하므로 주의 필요:

1. `start_agi_system.ps1` - 대시보드 실행 시 새 창 생성
2. `start_core_24h_new_window.ps1` - 24시간 실행을 위한 새 창 생성

무한 루프가 있는 스크립트:
- `start_rhythm_sync_daemon.ps1`
- `start_immune_recovery_loop.ps1`
- `start_meta_supervisor_daemon.ps1`
- `start_24h_validation.ps1`
- `start_24h_silent.ps1`
- `start_24h_productions_background.ps1`
- `start_autonomous_work_worker.ps1`
- `start_metrics_collector_daemon.ps1`
- `start_phase5_system.ps1`
- `start_cache_validation_monitor.ps1`
- `start_worker_monitor.ps1`
- `start_ai_dev_stream.ps1`

**주의**: 이 스크립트들을 동시에 또는 잘못된 조합으로 실행하지 마세요!

## 🔧 유틸리티 스크립트

### 긴급 중지 스크립트
```powershell
.\agi\scripts\emergency_stop_all_powershell.ps1
```

### 프로세스 모니터링
```powershell
# 실시간 프로세스 개수 모니터링
while ($true) {
    $count = (Get-Process powershell* -ErrorAction SilentlyContinue).Count
    Write-Host "$(Get-Date -Format 'HH:mm:ss') - PowerShell 프로세스: $count 개" -ForegroundColor Cyan
    if ($count -gt 5) {
        Write-Host "⚠️  경고: PowerShell 프로세스가 너무 많습니다!" -ForegroundColor Red
    }
    Start-Sleep -Seconds 5
}
```

## 📞 긴급 연락처

문제가 계속되면:
1. 이 문서의 "즉시 조치" 섹션 실행
2. 컴퓨터 재시작
3. Core/Binoche에게 연락

---

**마지막 업데이트**: 2025-12-15
**작성자**: Sena (Claude Agent)
