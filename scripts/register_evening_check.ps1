param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [switch]$NoAdmin
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = 'Stop'
$taskName = 'AGI_Evening_Milestone_Check'

if ($Unregister) {
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "🗑️ Task unregistered: $taskName" -ForegroundColor Yellow
    }
    else {
        Write-Host "ℹ️ Task not found: $taskName" -ForegroundColor Gray
    }
    exit 0
}

if ($Status) {
    $t = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if (-not $t) {
        Write-Host "❌ Task not found: $taskName" -ForegroundColor Red
        exit 1
    }
    $info = $t | Get-ScheduledTaskInfo
    Write-Host "📋 Task Status: $taskName" -ForegroundColor Cyan
    Write-Host "  State: $($info.State)" -ForegroundColor White
    Write-Host "  Last run: $($info.LastRunTime)" -ForegroundColor White
    Write-Host "  Next run: $($info.NextRunTime)" -ForegroundColor White
    Write-Host "  Last result: $($info.LastTaskResult)" -ForegroundColor White
    exit 0
}

if ($Register) {
    Write-Host "📝 Registering evening milestone check..." -ForegroundColor Cyan

    # 매일 20:00 실행 (KST)
    $trigger = New-ScheduledTaskTrigger -Daily -At 20:00

    # 작업 생성
    $scriptPath = "$WorkspaceRoot\scripts\evening_milestone_check.ps1"
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument @"
-NoProfile -ExecutionPolicy Bypass -File "$scriptPath"
"@

    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    # Principal 설정
    $principalHigh = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
    $principalUser = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

    try {
        if ($NoAdmin) {
            Write-Host "  Registering with LeastPrivilege (-NoAdmin)" -ForegroundColor Yellow
            Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principalUser -Description "Phase 10.1 evening milestone check (20:00 KST)" | Out-Null
        }
        else {
            Write-Host "  Attempting registration with RunLevel=Highest" -ForegroundColor Gray
            Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principalHigh -Description "Phase 10.1 evening milestone check (20:00 KST)" | Out-Null
        }
    }
    catch {
        Write-Host "  ⚠️ Registration with RunLevel=Highest failed or access denied. Retrying with LeastPrivilege..." -ForegroundColor Yellow
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principalUser -Description "Phase 10.1 evening milestone check (20:00 KST)" | Out-Null
    }

    Write-Host "✅ Task registered successfully!" -ForegroundColor Green
    Write-Host "`n📅 Schedule:" -ForegroundColor White
    Write-Host "  Time: 20:00 KST daily" -ForegroundColor White
    Write-Host "  Script: evening_milestone_check.ps1" -ForegroundColor White
    Write-Host "`n💡 Tip: Check status with .\register_evening_check.ps1 -Status" -ForegroundColor Gray
    exit 0
}

Write-Host "Usage: .\\register_evening_check.ps1 -Register|-Unregister|-Status [-NoAdmin]" -ForegroundColor Yellow