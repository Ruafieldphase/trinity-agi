<#
.SYNOPSIS
Goal Executor Monitor를 Windows Scheduled Task로 등록

.DESCRIPTION
Goal Executor의 정체 상태를 자동 감지하고 재실행하는 모니터를 등록합니다.
- 10분마다 실행
- 15분 이상 정체 시 자동 재실행
- 백그라운드 실행

.PARAMETER Register
Task를 등록합니다.

.PARAMETER Unregister
Task를 제거합니다.

.PARAMETER Status
Task 상태를 확인합니다.

.PARAMETER IntervalMinutes
모니터링 간격 (분, 기본값: 10)

.PARAMETER ThresholdMinutes
정체 판단 임계값 (분, 기본값: 15)

.EXAMPLE
.\register_goal_executor_monitor_task.ps1 -Register
Goal Executor Monitor를 등록합니다.

.EXAMPLE
.\register_goal_executor_monitor_task.ps1 -Status
현재 상태를 확인합니다.
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [int]$IntervalMinutes = 10,
    [int]$ThresholdMinutes = 15,
    [switch]$UserMode
)

$ErrorActionPreference = 'Stop'
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$TaskName = "AGI_GoalExecutorMonitor"
$PythonExe = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
$ScriptPath = Join-Path $WorkspaceRoot "scripts\goal_executor_monitor.py"
$LogPath = Join-Path $WorkspaceRoot "outputs\goal_executor_monitor.log"

function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Register-MonitorTask {
    Write-Host "📝 Goal Executor Monitor Task 등록 중..." -ForegroundColor Cyan
    Write-Host "   간격: $IntervalMinutes 분" -ForegroundColor Gray
    Write-Host "   임계값: $ThresholdMinutes 분" -ForegroundColor Gray
    Write-Host "   모드: $([string]::Copy($(if ($UserMode) { 'User' } else { 'Admin' })))" -ForegroundColor Gray
    
    if (-not (Test-Path $PythonExe)) {
        Write-Host "❌ Python venv를 찾을 수 없습니다: $PythonExe" -ForegroundColor Red
        exit 1
    }
    
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "❌ 모니터 스크립트를 찾을 수 없습니다: $ScriptPath" -ForegroundColor Red
        exit 1
    }
    
    # 기존 Task 제거
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "🗑️  기존 Task 제거 중..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Task Action: Python 스크립트 실행
    $pythonArgs = "`"$ScriptPath`" --threshold $ThresholdMinutes --log `"$LogPath`""
    $action = New-ScheduledTaskAction -Execute $PythonExe -Argument $pythonArgs
    
    # Task Trigger: 반복 실행
    # Windows가 허용하는 반복 Duration으로 제한 (약 10년)
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 3650)
    
    # Task Settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
    
    # Task Principal
    if ($UserMode) {
        # 관리자 없이 현재 사용자 세션에서 실행
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
    }
    else {
        # 관리자 권한으로 등록 시 더 유연한 S4U 사용 가능
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited
    }
    
    # Task 등록
    $registered = $false
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "AGI Goal Executor 정체 감지 및 자동 재실행 모니터 ($IntervalMinutes 분마다)" | Out-Null
        $registered = $true
        Write-Host "✅ Task 등록 완료: $TaskName" -ForegroundColor Green
        Write-Host "   실행 간격: $IntervalMinutes 분" -ForegroundColor Gray
        Write-Host "   정체 임계값: $ThresholdMinutes 분" -ForegroundColor Gray
        Write-Host "   로그 위치: $LogPath" -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ Task 등록 실패: $_" -ForegroundColor Red
    }
    
    if ($registered) {
        # 즉시 실행
        try {
            Write-Host "`n🚀 Task 즉시 실행 중..." -ForegroundColor Cyan
            Start-ScheduledTask -TaskName $TaskName
            Start-Sleep -Seconds 2
        }
        catch {
            Write-Host "⚠️  Task 즉시 실행 실패: $_" -ForegroundColor Yellow
        }
        Show-TaskStatus
    }
}

function Unregister-MonitorTask {
    Write-Host "🗑️  Goal Executor Monitor Task 제거 중..." -ForegroundColor Yellow
    
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $existingTask) {
        Write-Host "ℹ️  Task가 등록되어 있지 않습니다." -ForegroundColor Gray
        return
    }
    
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "✅ Task 제거 완료" -ForegroundColor Green
}

function Show-TaskStatus {
    Write-Host "`n📊 Goal Executor Monitor Task 상태" -ForegroundColor Cyan
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if (-not $task) {
        Write-Host "❌ Task가 등록되어 있지 않습니다." -ForegroundColor Red
        Write-Host "`n등록하려면: .\register_goal_executor_monitor_task.ps1 -Register" -ForegroundColor Yellow
        return
    }
    
    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    
    Write-Host "   이름: $TaskName" -ForegroundColor Gray
    Write-Host "   상태: $($task.State)" -ForegroundColor $(if ($task.State -eq 'Ready') { 'Green' } else { 'Yellow' })
    Write-Host "   마지막 실행: $($taskInfo.LastRunTime)" -ForegroundColor Gray
    Write-Host "   마지막 결과: $($taskInfo.LastTaskResult)" -ForegroundColor $(if ($taskInfo.LastTaskResult -eq 0) { 'Green' } else { 'Red' })
    Write-Host "   다음 실행: $($taskInfo.NextRunTime)" -ForegroundColor Gray
    
    # 로그 파일 확인
    if (Test-Path $LogPath) {
        $logSize = (Get-Item $LogPath).Length
        $logSizeKB = [math]::Round($logSize / 1KB, 2)
        Write-Host "   로그 크기: $logSizeKB KB" -ForegroundColor Gray
        
        Write-Host "`n📜 최근 로그 (마지막 10줄):" -ForegroundColor Cyan
        Get-Content $LogPath -Tail 10 -ErrorAction SilentlyContinue | ForEach-Object {
            Write-Host "   $_" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "   로그: 아직 생성되지 않음" -ForegroundColor Gray
    }
}

# Main
if ($Register) {
    # 관리자 권한이 없는 경우 자동으로 UserMode로 전환
    if (-not (Test-AdminRights)) {
        $UserMode = $true
    }
    Register-MonitorTask
}
elseif ($Unregister) {
    # 제거는 관리자 권한이 필요할 수 있음. 없으면 시도 후 실패 시 안내.
    try { Unregister-MonitorTask } catch {
        Write-Host "⚠️  제거 실패: 관리자 권한이 필요할 수 있습니다." -ForegroundColor Yellow
        throw
    }
}
elseif ($Status) {
    Show-TaskStatus
}
else {
    # 기본: 상태 확인
    Show-TaskStatus
}
