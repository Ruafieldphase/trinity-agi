#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Register Autonomous Goal Executor as Windows Scheduled Task

.DESCRIPTION
    자동 목표 실행기를 Windows 작업 스케줄러에 등록합니다.
    - 매일 새벽 3:30에 실행
    - 시스템 유휴 시간에만 실행 (선택)
    - 로그 자동 기록
    - Wake timer 지원 (시스템이 절전 모드에서 깨어남)

.PARAMETER Register
    작업 등록 (기본값)

.PARAMETER Unregister
    작업 제거

.PARAMETER Status
    작업 상태 확인

.PARAMETER Time
    실행 시각 (기본: 03:30)

.PARAMETER RunNow
    등록 후 즉시 실행

.PARAMETER Force
    기존 작업 덮어쓰기

.EXAMPLE
    .\register_autonomous_executor_task.ps1 -Register
    .\register_autonomous_executor_task.ps1 -Unregister
    .\register_autonomous_executor_task.ps1 -Status
    .\register_autonomous_executor_task.ps1 -Register -Time "04:00" -RunNow
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$Time = "03:30",
    [switch]$RunNow,
    [switch]$Force
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

# 설정
$TaskName = "AGI_AutonomousGoalExecutor"
$PythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$ScriptPath = "$WorkspaceRoot\scripts\autonomous_goal_executor.py"
$LogDir = "$WorkspaceRoot\outputs\logs"
$LogFile = "$LogDir\autonomous_executor_$(Get-Date -Format 'yyyy-MM-dd').log"

# 로그 디렉토리 생성
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Get-TaskStatus {
    Write-ColorOutput "`n=== Autonomous Goal Executor Task Status ===" "Cyan"
    
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        
        if ($null -eq $task) {
            Write-ColorOutput "❌ Task not registered" "Red"
            Write-ColorOutput "   Run with -Register to create the task" "Yellow"
            return $false
        }
        
        Write-ColorOutput "✅ Task registered: $TaskName" "Green"
        Write-ColorOutput "   State: $($task.State)" "Cyan"
        
        $trigger = $task.Triggers | Select-Object -First 1
        if ($trigger) {
            Write-ColorOutput "   Trigger: Daily at $($trigger.StartBoundary.Substring(11,5))" "Cyan"
        }
        
        $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($info) {
            Write-ColorOutput "   Last Run: $($info.LastRunTime)" "Cyan"
            Write-ColorOutput "   Last Result: $($info.LastTaskResult)" "Cyan"
            Write-ColorOutput "   Next Run: $($info.NextRunTime)" "Cyan"
        }
        
        return $true
    }
    catch {
        Write-ColorOutput "❌ Error checking task: $_" "Red"
        return $false
    }
}

function Register-Task {
    Write-ColorOutput "`n=== Registering Autonomous Goal Executor Task ===" "Cyan"
    
    # Python 실행 파일 확인
    if (-not (Test-Path $PythonExe)) {
        Write-ColorOutput "❌ Python not found: $PythonExe" "Red"
        Write-ColorOutput "   Please ensure virtual environment is set up" "Yellow"
        exit 1
    }
    
    # 스크립트 확인
    if (-not (Test-Path $ScriptPath)) {
        Write-ColorOutput "❌ Script not found: $ScriptPath" "Red"
        exit 1
    }
    
    # 기존 작업 확인
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask -and -not $Force) {
        Write-ColorOutput "⚠️  Task already exists: $TaskName" "Yellow"
        Write-ColorOutput "   Use -Force to overwrite" "Yellow"
        exit 1
    }
    
    if ($existingTask) {
        Write-ColorOutput "🔄 Removing existing task..." "Yellow"
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # 시간 파싱
    $hours, $minutes = $Time.Split(":")
    $startTime = Get-Date -Hour ([int]$hours) -Minute ([int]$minutes) -Second 0
    
    Write-ColorOutput "📅 Schedule: Daily at $Time" "Cyan"
    Write-ColorOutput "🐍 Python: $PythonExe" "Cyan"
    Write-ColorOutput "📜 Script: $ScriptPath" "Cyan"
    Write-ColorOutput "📝 Log: $LogFile" "Cyan"
    
    # Action 정의
    $actionArgs = "-NoProfile -ExecutionPolicy Bypass -Command `"& '$PythonExe' '$ScriptPath' > '$LogFile' 2>&1`""
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs -WorkingDirectory $WorkspaceRoot
    
    # Trigger 정의 (매일)
    $trigger = New-ScheduledTaskTrigger -Daily -At $startTime
    
    # Settings 정의
    $settings = New-ScheduledTaskSettingsSet `
$settings.Hidden = $true
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    
    # Principal 정의 (현재 사용자, 제한된 권한)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Limited
    
    # 작업 등록
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "Autonomous Goal Executor - 자동으로 정의된 목표를 실행하고 추적" `
            -Force | Out-Null
        
        Write-ColorOutput "`n✅ Task registered successfully!" "Green"
        
        # 상태 확인
        Start-Sleep -Milliseconds 500
        Get-TaskStatus | Out-Null
        
        # 즉시 실행
        if ($RunNow) {
            Write-ColorOutput "`n🚀 Running task now..." "Cyan"
            Start-ScheduledTask -TaskName $TaskName
            Start-Sleep -Seconds 2
            
            $info = Get-ScheduledTaskInfo -TaskName $TaskName
            Write-ColorOutput "   Status: $($info.LastTaskResult)" "Cyan"
        }
    }
    catch {
        Write-ColorOutput "❌ Failed to register task: $_" "Red"
        exit 1
    }
}

function Unregister-Task {
    Write-ColorOutput "`n=== Unregistering Autonomous Goal Executor Task ===" "Cyan"
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        Write-ColorOutput "ℹ️  Task not found: $TaskName" "Yellow"
        return
    }
    
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-ColorOutput "✅ Task unregistered successfully!" "Green"
    }
    catch {
        Write-ColorOutput "❌ Failed to unregister task: $_" "Red"
        exit 1
    }
}

# 메인 로직
if ($Unregister) {
    Unregister-Task
}
elseif ($Status -or (-not $Register -and -not $Unregister)) {
    Get-TaskStatus | Out-Null
}
elseif ($Register) {
    Register-Task
}

Write-ColorOutput ""