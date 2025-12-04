<#
.SYNOPSIS
    24h Production을 Windows Scheduled Task로 등록 (재부팅 안전)

.DESCRIPTION
    다음 Production을 Scheduled Task로 등록합니다:
    1. Lumen 24h Feedback System
    2. Trinity Autopoietic Cycle
    3. Unified Real-Time Dashboard
    
    재부팅 시에도 자동으로 재시작됩니다.

.PARAMETER Register
    Scheduled Task 등록

.PARAMETER Unregister
    Scheduled Task 제거

.PARAMETER Status
    현재 등록 상태 확인

.EXAMPLE
    .\register_24h_productions.ps1 -Register
    
.EXAMPLE
    .\register_24h_productions.ps1 -Status
    
.EXAMPLE
    .\register_24h_productions.ps1 -Unregister
#>

[CmdletBinding()]
param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status
)

$ErrorActionPreference = 'Stop'

$WorkspaceRoot = "C:\workspace\agi"
$TaskNames = @(
    "AGI_Lumen_24h_Production"
    "AGI_Trinity_24h_Cycle"
    "AGI_Unified_Dashboard"
)

function Show-Status {
    Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  24h Production - Scheduled Task 상태                        ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    foreach ($taskName in $TaskNames) {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        
        if ($task) {
            $info = Get-ScheduledTaskInfo -TaskName $taskName
            Write-Host "✅ $taskName" -ForegroundColor Green
            Write-Host "   상태: $($task.State)" -ForegroundColor White
            Write-Host "   마지막 실행: $($info.LastRunTime)" -ForegroundColor Gray
            Write-Host "   다음 실행: $($info.NextRunTime)" -ForegroundColor Gray
        }
        else {
            Write-Host "⚠️  $taskName" -ForegroundColor Yellow
            Write-Host "   상태: 등록 안 됨" -ForegroundColor Red
        }
        Write-Host ""
    }
}

function Register-Tasks {
    Write-Host "`n🔧 24h Production Scheduled Task 등록 중...`n" -ForegroundColor Cyan
    
    # 1. Lumen 24h Production
    Write-Host "1️⃣  Lumen 24h Production 등록..." -ForegroundColor Yellow
    $action1 = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$WorkspaceRoot\scripts\start_lumen_24h_stable.ps1`""
    
    $trigger1 = New-ScheduledTaskTrigger -AtStartup
    $trigger1.Delay = "PT5M"  # 부팅 후 5분 대기
    
    $settings1 = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 5)
    
    Register-ScheduledTask `
        -TaskName $TaskNames[0] `
        -Action $action1 `
        -Trigger $trigger1 `
        -Settings $settings1 `
        -Description "AGI Lumen 24h Feedback System - Auto restart on boot" `
        -Force | Out-Null
    
    Write-Host "   ✅ 등록 완료" -ForegroundColor Green
    
    # 2. Trinity Autopoietic Cycle
    Write-Host "`n2️⃣  Trinity Autopoietic Cycle 등록..." -ForegroundColor Yellow
    $action2 = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$WorkspaceRoot\scripts\autopoietic_trinity_cycle.ps1`" -Hours 24"
    
    $trigger2 = New-ScheduledTaskTrigger -AtStartup
    $trigger2.Delay = "PT6M"  # 부팅 후 6분 대기 (Lumen 이후)
    
    $settings2 = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable
    
    Register-ScheduledTask `
        -TaskName $TaskNames[1] `
        -Action $action2 `
        -Trigger $trigger2 `
        -Settings $settings2 `
        -Description "AGI Trinity Autopoietic Cycle 24h - Auto restart on boot" `
        -Force | Out-Null
    
    Write-Host "   ✅ 등록 완료" -ForegroundColor Green
    
    # 3. Unified Dashboard
    Write-Host "`n3️⃣  Unified Real-Time Dashboard 등록..." -ForegroundColor Yellow
    $action3 = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$WorkspaceRoot\scripts\unified_realtime_dashboard.ps1`" -RefreshSeconds 10"
    
    $trigger3 = New-ScheduledTaskTrigger -AtStartup
    $trigger3.Delay = "PT7M"  # 부팅 후 7분 대기
    
    $settings3 = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable
    
    Register-ScheduledTask `
        -TaskName $TaskNames[2] `
        -Action $action3 `
        -Trigger $trigger3 `
        -Settings $settings3 `
        -Description "AGI Unified Real-Time Dashboard - Auto restart on boot" `
        -Force | Out-Null
    
    Write-Host "   ✅ 등록 완료" -ForegroundColor Green
    
    Write-Host "`n✨ 모든 Scheduled Task 등록 완료!" -ForegroundColor Green
    Write-Host "`n재부팅 시 자동으로 다음 순서로 시작됩니다:" -ForegroundColor Yellow
    Write-Host "   부팅 + 5분 → Lumen 24h Production" -ForegroundColor White
    Write-Host "   부팅 + 6분 → Trinity Autopoietic Cycle" -ForegroundColor White
    Write-Host "   부팅 + 7분 → Unified Dashboard" -ForegroundColor White
    Write-Host ""
}

function Unregister-Tasks {
    Write-Host "`n🗑️  24h Production Scheduled Task 제거 중...`n" -ForegroundColor Yellow
    
    foreach ($taskName in $TaskNames) {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($task) {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
            Write-Host "✅ $taskName 제거 완료" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  $taskName - 등록되지 않음" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n✨ 모든 Scheduled Task 제거 완료!`n" -ForegroundColor Green
}

# Main
if ($Register) {
    Register-Tasks
}
elseif ($Unregister) {
    Unregister-Tasks
}
else {
    Show-Status
}
