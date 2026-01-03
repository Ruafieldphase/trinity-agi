#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Register Autonomous Goal Executor as Windows Scheduled Task (schtasks version)

.DESCRIPTION
    자동 목표 실행기를 Windows 작업 스케줄러에 등록합니다.
    schtasks.exe를 사용하여 관리자 권한 없이도 등록 가능합니다.
    
    - 매일 새벽 3:30에 실행
    - 로그 자동 기록
    - 현재 사용자 권한으로 실행

.PARAMETER Register
    작업 등록 (기본값)

.PARAMETER Unregister
    작업 제거

.PARAMETER Status
    작업 상태 확인

.PARAMETER Time
    실행 시각 (기본: 03:30)

.PARAMETER Force
    기존 작업 덮어쓰기

.EXAMPLE
    .\register_autonomous_executor_task_v2.ps1 -Register
    .\register_autonomous_executor_task_v2.ps1 -Unregister
    .\register_autonomous_executor_task_v2.ps1 -Status
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [string]$Time = "03:30",
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
        $result = schtasks /Query /TN $TaskName /FO LIST /V 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "❌ Task not registered" "Red"
            Write-ColorOutput "   Run with -Register to create the task" "Yellow"
            return $false
        }
        
        Write-ColorOutput "✅ Task registered: $TaskName" "Green"
        
        # 상태 파싱
        $lines = $result -split "`n"
        foreach ($line in $lines) {
            if ($line -match "Status:\s+(.+)") {
                Write-ColorOutput "   Status: $($matches[1].Trim())" "Cyan"
            }
            elseif ($line -match "Next Run Time:\s+(.+)") {
                Write-ColorOutput "   Next Run: $($matches[1].Trim())" "Cyan"
            }
            elseif ($line -match "Last Run Time:\s+(.+)") {
                Write-ColorOutput "   Last Run: $($matches[1].Trim())" "Cyan"
            }
            elseif ($line -match "Last Result:\s+(.+)") {
                Write-ColorOutput "   Last Result: $($matches[1].Trim())" "Cyan"
            }
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
    
    # 기존 작업 확인 (오류 무시)
    $taskExists = $false
    try {
        $null = schtasks /Query /TN $TaskName 2>&1
        $taskExists = $LASTEXITCODE -eq 0
    }
    catch {
        $taskExists = $false
    }
    
    if ($taskExists -and -not $Force) {
        Write-ColorOutput "⚠️  Task already exists: $TaskName" "Yellow"
        Write-ColorOutput "   Use -Force to overwrite" "Yellow"
        exit 1
    }
    
    if ($taskExists) {
        Write-ColorOutput "🔄 Removing existing task..." "Yellow"
        try {
            schtasks /Delete /TN $TaskName /F 2>&1 | Out-Null
        }
        catch {
            # Ignore deletion errors
        }
    }
    
    Write-ColorOutput "📅 Schedule: Daily at $Time" "Cyan"
    Write-ColorOutput "🐍 Python: $PythonExe" "Cyan"
    Write-ColorOutput "📜 Script: $ScriptPath" "Cyan"
    Write-ColorOutput "📝 Log dir: $LogDir" "Cyan"
    
    # 간단한 배치 스크립트 생성
    $batchFile = "$WorkspaceRoot\scripts\run_autonomous_executor.bat"
    $batchContent = @"
@echo off
cd /d "$WorkspaceRoot"
"$PythonExe" "$ScriptPath" > "$LogDir\autonomous_executor_%date:~0,10%.log" 2>&1
"@
    $batchContent | Out-File -FilePath $batchFile -Encoding ASCII -Force
    
    Write-ColorOutput "📄 Batch file: $batchFile" "Cyan"
    
    # schtasks로 작업 생성
    try {
        $createArgs = @(
            "/Create"
            "/TN", $TaskName
            "/TR", "`"$batchFile`""
            "/SC", "DAILY"
            "/ST", $Time
            "/F"
        )
        
        $output = & schtasks @createArgs 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "❌ Failed to register task" "Red"
            Write-ColorOutput "   Output: $output" "Red"
            exit 1
        }
        
        Write-ColorOutput "`n✅ Task registered successfully!" "Green"
        
        # 상태 확인
        Start-Sleep -Milliseconds 500
        Get-TaskStatus | Out-Null
    }
    catch {
        Write-ColorOutput "❌ Failed to register task: $_" "Red"
        exit 1
    }
}

function Unregister-Task {
    Write-ColorOutput "`n=== Unregistering Autonomous Goal Executor Task ===" "Cyan"
    
    $existingCheck = schtasks /Query /TN $TaskName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput "ℹ️  Task not found: $TaskName" "Yellow"
        return
    }
    
    try {
        schtasks /Delete /TN $TaskName /F | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Task unregistered successfully!" "Green"
        }
        else {
            Write-ColorOutput "❌ Failed to unregister task" "Red"
            exit 1
        }
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