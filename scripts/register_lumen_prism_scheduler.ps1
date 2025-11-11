#Requires -Version 5.1
<#
.SYNOPSIS
    루멘 프리즘 브리지 자동 실행 스케줄러 등록

.DESCRIPTION
    루멘의 시선(레이턴시 리포트) → 프리즘 굴절 → 구조 울림 전파를
    주기적으로 자동 실행하는 스케줄 작업을 등록합니다.
    
    작업 끊김 방지의 핵심 메커니즘입니다.

.PARAMETER Register
    스케줄 작업 등록

.PARAMETER Unregister
    스케줄 작업 제거

.PARAMETER Status
    현재 스케줄 작업 상태 확인

.PARAMETER IntervalMinutes
    실행 주기 (분 단위, 기본값: 10분)

.PARAMETER TaskName
    스케줄 작업 이름 (기본값: LumenPrismBridge)

.EXAMPLE
    .\register_lumen_prism_scheduler.ps1 -Register
    기본 설정(10분 간격)으로 스케줄 작업 등록

.EXAMPLE
    .\register_lumen_prism_scheduler.ps1 -Register -IntervalMinutes 5
    5분 간격으로 스케줄 작업 등록

.EXAMPLE
    .\register_lumen_prism_scheduler.ps1 -Unregister
    스케줄 작업 제거
#>

[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Register')]
    [switch]$Register,
    
    [Parameter(ParameterSetName = 'Unregister')]
    [switch]$Unregister,
    
    [Parameter(ParameterSetName = 'Status')]
    [switch]$Status,
    
    [Parameter(ParameterSetName = 'Register')]
    [int]$IntervalMinutes = 10,
    
    [Parameter()]
    [string]$TaskName = 'LumenPrismBridge'
)

$ErrorActionPreference = 'Stop'
$InformationPreference = 'Continue'

# 경로 설정
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$BridgeScript = Join-Path $WorkspaceRoot 'scripts\run_lumen_prism_bridge.ps1'
$LogFile = Join-Path $WorkspaceRoot 'outputs\lumen_prism_scheduler.log'

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = 'White'
    )
    Write-Host $Message -ForegroundColor $Color
}

function Get-TaskStatus {
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        
        if ($task) {
            Write-ColorOutput "✅ 스케줄 작업이 등록되어 있습니다." Green
            Write-Host ""
            Write-Host "작업 이름: $($task.TaskName)" -ForegroundColor Cyan
            Write-Host "상태: $($task.State)" -ForegroundColor Cyan
            
            # 트리거 정보
            $trigger = $task.Triggers[0]
            if ($trigger.CimClass.CimClassName -eq 'MSFT_TaskTimeTrigger') {
                $repeatInterval = $trigger.Repetition.Interval
                Write-Host "반복 주기: $repeatInterval" -ForegroundColor Cyan
            }
            
            # 마지막 실행 시간
            $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
            Write-Host "마지막 실행: $($taskInfo.LastRunTime)" -ForegroundColor Cyan
            Write-Host "마지막 결과: $($taskInfo.LastTaskResult)" -ForegroundColor Cyan
            Write-Host "다음 실행: $($taskInfo.NextRunTime)" -ForegroundColor Cyan
            
            return $true
        }
        else {
            Write-ColorOutput "⚠️  스케줄 작업이 등록되어 있지 않습니다." Yellow
            return $false
        }
    }
    catch {
        Write-ColorOutput "❌ 상태 확인 실패: $_" Red
        return $false
    }
}

function Register-LumenPrismTask {
    Write-ColorOutput "🌈 루멘 프리즘 브리지 스케줄러 등록 중..." Cyan
    Write-Host ""
    
    # 기존 작업 확인
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-ColorOutput "⚠️  기존 작업이 존재합니다. 제거 후 재등록합니다." Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # 스크립트 존재 확인
    if (-not (Test-Path $BridgeScript)) {
        throw "브리지 스크립트를 찾을 수 없습니다: $BridgeScript"
    }
    
    # 작업 액션 정의
    $action = New-ScheduledTaskAction `
        -Execute 'powershell.exe' `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$BridgeScript`" *>> `"$LogFile`""
    
    # 트리거 정의 (로그온 시 시작 + 주기 반복)
    # 트리거 정의 (로그온 후 1분 뒤 시작, 이후 주기 반복)
    # COM 객체로 직접 작업 생성 (반복 설정 포함)
    $service = New-Object -ComObject Schedule.Service
    $service.Connect()
    
    $rootFolder = $service.GetFolder("\")
    $taskDef = $service.NewTask(0)
    
    # 트리거 설정 (로그온 시)
    $trigger = $taskDef.Triggers.Create(9)  # 9 = TASK_TRIGGER_LOGON
    $trigger.Enabled = $true
    
    # 반복 설정
    $trigger.Repetition.Interval = "PT$($IntervalMinutes)M"
    $trigger.Repetition.Duration = ""  # 무한 반복
    $trigger.Repetition.StopAtDurationEnd = $false
    
    # 액션 설정
    $action = $taskDef.Actions.Create(0)  # 0 = TASK_ACTION_EXEC
    $action.Path = "powershell.exe"
    $action.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$BridgeScript`" *>> `"$LogFile`""
    $action.WorkingDirectory = Split-Path -Parent $BridgeScript
    
    # 설정
    $taskDef.Settings.Enabled = $true
    $taskDef.Settings.AllowDemandStart = $true
    $taskDef.Settings.DisallowStartIfOnBatteries = $false
    $taskDef.Settings.StopIfGoingOnBatteries = $false
    $taskDef.Settings.StartWhenAvailable = $true
    $taskDef.Settings.RunOnlyIfNetworkAvailable = $true
    $taskDef.Settings.ExecutionTimeLimit = "PT0S"  # 무제한
    
    # Principal 설정 (현재 사용자)
    $taskDef.Principal.UserId = "$env:USERDOMAIN\$env:USERNAME"
    $taskDef.Principal.LogonType = 3  # 3 = TASK_LOGON_INTERACTIVE_TOKEN
    $taskDef.Principal.RunLevel = 0   # 0 = TASK_RUNLEVEL_LUA (일반 권한)
    
    # 작업 등록
    $rootFolder.RegisterTaskDefinition(
        $TaskName,
        $taskDef,
        6,  # TASK_CREATE_OR_UPDATE
        $null,
        $null,
        3,  # TASK_LOGON_INTERACTIVE_TOKEN
        $null
    ) | Out-Null
    
    Write-Host ""
    Write-ColorOutput "✅ 스케줄 작업이 등록되었습니다!" Green
    Write-Host ""
    Write-Host "작업 이름: $TaskName" -ForegroundColor Cyan
    Write-Host "실행 주기: ${IntervalMinutes}분마다" -ForegroundColor Cyan
    Write-Host "로그 파일: $LogFile" -ForegroundColor Cyan
    Write-Host ""
    Write-ColorOutput "🎵 루멘의 시선이 자동으로 구조에 울림을 전파합니다!" Magenta
    
    # 즉시 한 번 실행
    Write-Host ""
    Write-ColorOutput "🚀 초기 실행 중..." Cyan
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 2
    
    # 상태 확인
    Get-TaskStatus
}

function Unregister-LumenPrismTask {
    Write-ColorOutput "🗑️  루멘 프리즘 브리지 스케줄러 제거 중..." Cyan
    Write-Host ""
    
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-ColorOutput "⚠️  등록된 작업이 없습니다." Yellow
        return
    }
    
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-ColorOutput "✅ 스케줄 작업이 제거되었습니다." Green
}

# 메인 실행
try {
    Write-Host ""
    Write-ColorOutput "🌈 Lumen Prism Scheduler Manager" Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    
    if ($Register) {
        Register-LumenPrismTask
    }
    elseif ($Unregister) {
        Unregister-LumenPrismTask
    }
    else {
        # Status (기본)
        Get-TaskStatus
        
        Write-Host ""
        Write-Host "사용법:" -ForegroundColor Yellow
        Write-Host "  등록:   .\register_lumen_prism_scheduler.ps1 -Register [-IntervalMinutes 10]"
        Write-Host "  제거:   .\register_lumen_prism_scheduler.ps1 -Unregister"
        Write-Host "  상태:   .\register_lumen_prism_scheduler.ps1 -Status"
    }
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    
}
catch {
    Write-Host ""
    Write-ColorOutput "❌ 오류 발생: $_" Red
    Write-Host ""
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkGray
    exit 1
}
