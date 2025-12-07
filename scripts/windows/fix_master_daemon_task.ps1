# Fix Master Daemon Scheduled Task (관리자 권한 필요)
# 우클릭 → "관리자 권한으로 실행"

$ErrorActionPreference = "Stop"

Write-Host "`n=== Master Daemon Scheduled Task 수정 ===" -ForegroundColor Cyan

$taskName = "AGI_Master_Daemon"
$scriptPath = "C:\workspace\agi\scripts\master_daemon.ps1"
$configPath = "C:\workspace\agi\config\master_daemon_config.json"

try {
    # 기존 작업 제거
    Write-Host "기존 작업 제거 중..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    
    # Trigger: 로그온 시 실행
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    
    # Action: 올바른 경로로 실행
    $arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Start -ConfigPath `"$configPath`""
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments -WorkingDirectory "C:\workspace\agi"
    
    # Settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -Hidden `
        -ExecutionTimeLimit (New-TimeSpan -Days 365)
    
    # Register
    Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Force | Out-Null
    
    Write-Host "✅ Master Daemon 작업 재등록 완료" -ForegroundColor Green
    Write-Host "`n작업 상세:" -ForegroundColor Cyan
    Write-Host "  Execute: powershell.exe" -ForegroundColor Gray
    Write-Host "  Script: $scriptPath" -ForegroundColor Gray
    Write-Host "  Working Dir: C:\workspace\agi" -ForegroundColor Gray
    
    # 즉시 실행
    Write-Host "`nMaster Daemon 시작 중..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $taskName
    Start-Sleep -Seconds 3
    
    # 상태 확인
    $task = Get-ScheduledTask -TaskName $taskName
    Write-Host "`n✅ 작업 상태: $($task.State)" -ForegroundColor Green
    
    # Daemon 상태 확인
    Write-Host "`n=== Daemon 프로세스 확인 ===" -ForegroundColor Cyan
    & $scriptPath -Status
    
}
catch {
    Write-Host "❌ 오류 발생: $_" -ForegroundColor Red
    Write-Host "`nStack Trace:" -ForegroundColor Yellow
    Write-Host $_.ScriptStackTrace -ForegroundColor Gray
}

Read-Host "`nPress Enter to exit"
