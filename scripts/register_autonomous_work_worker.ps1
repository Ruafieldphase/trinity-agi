<#
.SYNOPSIS
Autonomous Work Worker를 Windows 스케줄러에 등록/해제/확인

.DESCRIPTION
- 현재 사용자 로그온 시 자동으로 자율 워커를 시작합니다.
- 옵션에 따라 즉시 실행도 가능합니다.

.PARAMETER Register
스케줄러 작업 등록

.PARAMETER Unregister
스케줄러 작업 해제

.PARAMETER Status
스케줄러 작업 상태 확인

.PARAMETER Time
매일 특정 시간에 실행하도록 등록 (형식: HH:mm). 지정 안 하면 로그인 시 실행

.PARAMETER IntervalSeconds
워커 실행 간격 (초). 기본 300

.PARAMETER RunNow
등록 후 즉시 한 번 실행

.EXAMPLE
# 로그인 시 자동 실행 등록
./register_autonomous_work_worker.ps1 -Register

.EXAMPLE
# 매일 03:35 실행 등록
./register_autonomous_work_worker.ps1 -Register -Time 03:35

.EXAMPLE
# 상태 확인
./register_autonomous_work_worker.ps1 -Status

.EXAMPLE
# 등록 해제
./register_autonomous_work_worker.ps1 -Unregister
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$Time,
    [int]$IntervalSeconds = 300,
    [switch]$RunNow
)

$ErrorActionPreference = 'Stop'

$taskName = 'AutonomousWorkWorker'
$workspace = Split-Path -Parent $PSScriptRoot
$scriptToRun = Join-Path $workspace 'scripts\start_autonomous_work_worker.ps1'

function Test-ScheduledTasksModule {
    if (-not (Get-Module -ListAvailable -Name ScheduledTasks)) {
        Write-Host '⚠️  ScheduledTasks 모듈이 필요합니다 (Windows 8+/Server 2012+ 기본 제공)' -ForegroundColor Yellow
    }
}

function Get-ExistingTask {
    try {
        return Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    }
    catch {
        return $null
    }
}

function Register-WorkerTask {
    param(
        [string]$AtTime
    )

    $pwsh = (Get-Command powershell).Source
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptToRun`" -KillExisting -Detached -IntervalSeconds $IntervalSeconds"

    if ($AtTime) {
        # 매일 특정 시간에 실행
        $trigger = New-ScheduledTaskTrigger -Daily -At (Get-Date $AtTime)
    }
    else {
        # 로그인 시 실행
        $trigger = New-ScheduledTaskTrigger -AtLogOn
    }

    $action = New-ScheduledTaskAction -Execute $pwsh -Argument $arguments -WorkingDirectory $workspace

    $taskPrincipal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

    $taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    if (Get-ExistingTask) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    }

    try {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $taskPrincipal -Settings $taskSettings | Out-Null

        Write-Host "✅ Registered scheduled task: $taskName" -ForegroundColor Green
        if ($AtTime) {
            Write-Host "   Trigger: Daily at $AtTime" -ForegroundColor Gray
        }
        else {
            Write-Host "   Trigger: At logon" -ForegroundColor Gray
        }
        Write-Host "   Action: $pwsh $arguments" -ForegroundColor Gray
        Write-Host "   WorkDir: $workspace" -ForegroundColor Gray
    }
    catch {
        Write-Host "⚠️  Register-ScheduledTask failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   Falling back to schtasks.exe" -ForegroundColor Yellow

        $trPayload = "$pwsh -NoProfile -ExecutionPolicy Bypass -File `"$scriptToRun`" -KillExisting -Detached -IntervalSeconds $IntervalSeconds"
        $trArg = '"' + $trPayload + '"'
        $argsList = @('/Create')
        if ($AtTime) { $argsList += @('/SC', 'DAILY', '/ST', $AtTime) } else { $argsList += @('/SC', 'ONLOGON') }
        $argsList += @('/TN', $taskName, '/TR', $trArg, '/RU', $env:USERNAME, '/RL', 'LIMITED', '/IT', '/F')
        Write-Host "   > schtasks $($argsList -join ' ')" -ForegroundColor Gray
        $proc = Start-Process -FilePath schtasks.exe -ArgumentList $argsList -NoNewWindow -Wait -PassThru
        if ($proc.ExitCode -eq 0) {
            Write-Host "✅ Registered (schtasks): $taskName" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  schtasks failed with code $($proc.ExitCode). Falling back to Startup folder shortcut." -ForegroundColor Yellow
            $startupDir = Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
            if (-not (Test-Path $startupDir)) { New-Item -ItemType Directory -Path $startupDir -Force | Out-Null }
            $cmdPath = Join-Path $startupDir 'AutonomousWorkWorker.cmd'
            $line = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $scriptToRun + '" -KillExisting -Detached -IntervalSeconds ' + $IntervalSeconds
            Set-Content -Path $cmdPath -Value $line -Encoding ASCII
            Write-Host "✅ Registered via Startup folder: $cmdPath" -ForegroundColor Green
        }
    }
}

if ($Register) {
    Test-ScheduledTasksModule
    Register-WorkerTask -AtTime $Time

    if ($RunNow) {
        $started = $false
        try {
            Start-ScheduledTask -TaskName $taskName
            Write-Host '🚀 Started task immediately (ScheduledTask)' -ForegroundColor Green
            $started = $true
        }
        catch {
            Write-Host "⚠️  Could not start task immediately: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        if (-not $started) {
            Write-Host '↪️  Fallback: starting worker directly (Detached)' -ForegroundColor Yellow
            try { & $scriptToRun -KillExisting -Detached -IntervalSeconds $IntervalSeconds; $started = $true }
            catch { Write-Host "❌ Fallback start failed: $($_.Exception.Message)" -ForegroundColor Red }
        }
    }
    exit 0
}

if ($Unregister) {
    $task = Get-ExistingTask
    if ($task) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "🧹 Unregistered task: $taskName" -ForegroundColor Green
    }
    else {
        Write-Host 'ℹ️  Task not found' -ForegroundColor Yellow
    }
    exit 0
}

if ($Status) {
    $task = Get-ExistingTask
    if ($task) {
        $state = (Get-ScheduledTaskInfo -TaskName $taskName)
        Write-Host "📋 Task: $taskName" -ForegroundColor Cyan
        Write-Host "   State: $($state.State)" -ForegroundColor Gray
        Write-Host "   LastRunTime: $($state.LastRunTime)" -ForegroundColor Gray
        Write-Host "   NextRunTime: $($state.NextRunTime)" -ForegroundColor Gray
        Write-Host "   LastTaskResult: $($state.LastTaskResult)" -ForegroundColor Gray
    }
    else {
        Write-Host 'ℹ️  Scheduled Task not found' -ForegroundColor Yellow
    }

    # Startup 폴더 등록 상태도 함께 표시 (워커 + 워치독)
    $startupDir = Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
    $cmdPath = Join-Path $startupDir 'AutonomousWorkWorker.cmd'
    $watchCmd = Join-Path $startupDir 'AutonomousWorkWatchdog.cmd'
    if (Test-Path $cmdPath) {
        Write-Host "📎 Startup entry: PRESENT" -ForegroundColor Green
        $cmdLine = Get-Content -Path $cmdPath -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmdLine) { Write-Host "   Command: $cmdLine" -ForegroundColor Gray }
    }
    else {
        Write-Host "📎 Startup entry: ABSENT" -ForegroundColor Yellow
    }
    if (Test-Path $watchCmd) {
        Write-Host "📎 Watchdog entry: PRESENT" -ForegroundColor Green
        $cmdLine2 = Get-Content -Path $watchCmd -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmdLine2) { Write-Host "   Command: $cmdLine2" -ForegroundColor Gray }
    }
    else {
        Write-Host "📎 Watchdog entry: ABSENT" -ForegroundColor Yellow
    }
    
    # 실행 중 프로세스 상태도 출력
    try {
        Write-Host ""; Write-Host "🔎 Worker runtime status:" -ForegroundColor Cyan
        & $scriptToRun -Status
    }
    catch { Write-Host "⚠️  Could not query runtime status: $($_.Exception.Message)" -ForegroundColor Yellow }
    exit 0
}

# 도움말 출력
Write-Host "Usage: register_autonomous_work_worker.ps1 -Register|-Unregister|-Status [-Time HH:mm] [-IntervalSeconds N] [-RunNow]" -ForegroundColor Yellow
exit 1
