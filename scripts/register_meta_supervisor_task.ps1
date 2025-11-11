<#
.SYNOPSIS
Meta Supervisor 자동 실행 등록

.DESCRIPTION
Windows Task Scheduler에 Meta Supervisor를 등록하여
정기적으로 시스템 건강도를 모니터링하고 자동 개입합니다.

.PARAMETER Register
스케줄 등록 (기본 동작)

.PARAMETER Unregister
스케줄 삭제

.PARAMETER Status
스케줄 상태 확인

.PARAMETER IntervalMinutes
실행 간격 (분, 기본 30분)

.PARAMETER TaskName
작업 이름 (기본: "AGI_MetaSupervisor")

.EXAMPLE
.\register_meta_supervisor_task.ps1 -Register
30분 간격으로 Meta Supervisor 등록

.EXAMPLE
.\register_meta_supervisor_task.ps1 -Unregister
스케줄 삭제
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [int]$IntervalMinutes = 30,
    [string]$TaskName = "AGI_MetaSupervisor"
)

$ErrorActionPreference = "Stop"
$workspaceRoot = Split-Path $PSScriptRoot -Parent
$pythonExe = Join-Path $workspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
$scriptPath = Join-Path $PSScriptRoot "meta_supervisor.py"

if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ Meta Supervisor 스크립트 없음: $scriptPath" -ForegroundColor Red
    exit 1
}

# 작업 존재 여부 확인
function Test-TaskExists {
    param([string]$Name)
    $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    return $null -ne $task
}

# 상태 확인
if ($Status -or (-not $Register -and -not $Unregister)) {
    Write-Host "📊 Meta Supervisor 스케줄 상태" -ForegroundColor Cyan
    Write-Host ""
    
    if (Test-TaskExists -Name $TaskName) {
        $task = Get-ScheduledTask -TaskName $TaskName
        $info = Get-ScheduledTaskInfo -TaskName $TaskName
        
        Write-Host "✅ 스케줄 등록됨" -ForegroundColor Green
        Write-Host ""
        Write-Host "  작업 이름: $TaskName"
        Write-Host "  상태: $($task.State)"
        Write-Host "  마지막 실행: $($info.LastRunTime)"
        Write-Host "  다음 실행: $($info.NextRunTime)"
        Write-Host "  마지막 결과: $($info.LastTaskResult)"
        
        # 트리거 정보
        $triggers = $task.Triggers
        if ($triggers.Count -gt 0) {
            Write-Host ""
            Write-Host "  트리거:"
            foreach ($trigger in $triggers) {
                if ($trigger.Repetition.Interval) {
                    Write-Host "    - 반복 간격: $($trigger.Repetition.Interval)"
                }
            }
        }
    }
    else {
        Write-Host "❌ 스케줄 미등록" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "등록 방법:"
        Write-Host "  .\register_meta_supervisor_task.ps1 -Register"
    }
    
    if (-not $Register -and -not $Unregister) {
        exit 0
    }
}

# 삭제
if ($Unregister) {
    Write-Host "🗑️  Meta Supervisor 스케줄 삭제 중..." -ForegroundColor Yellow
    
    if (Test-TaskExists -Name $TaskName) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "✅ 삭제 완료: $TaskName" -ForegroundColor Green
    }
    else {
        Write-Host "ℹ️  이미 삭제됨 또는 존재하지 않음" -ForegroundColor Gray
    }
    
    exit 0
}

# 등록
if ($Register) {
    Write-Host "📅 Meta Supervisor 스케줄 등록 중..." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  간격: $IntervalMinutes 분"
    Write-Host "  작업 이름: $TaskName"
    Write-Host ""
    
    # 기존 작업 삭제
    if (Test-TaskExists -Name $TaskName) {
        Write-Host "ℹ️  기존 작업 삭제 중..." -ForegroundColor Gray
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Python 실행 파일 확인
    if (-not (Test-Path $pythonExe)) {
        Write-Host "⚠️  가상환경 Python 없음, 시스템 Python 사용" -ForegroundColor Yellow
        $pythonExe = "python"
    }
    
    # 액션 정의
    $action = New-ScheduledTaskAction `
        -Execute $pythonExe `
        -Argument "`"$scriptPath`"" `
        -WorkingDirectory $workspaceRoot
    
    # 트리거 정의 (로그온 후 즉시 시작, 이후 반복)
    # Duration을 큰 값으로 설정 (약 10년)
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 3650)
    
    # 설정
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
    
    # 주체 (현재 사용자, 최고 권한)
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Highest
    
    # 작업 등록
    try {
        $task = Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "AGI 시스템 건강도를 모니터링하고 자동 개입합니다."
        
        Write-Host "✅ 등록 완료!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 작업 정보:"
        Write-Host "  - 작업 이름: $TaskName"
        Write-Host "  - 반복 간격: $IntervalMinutes 분"
        Write-Host "  - 다음 실행: $((Get-ScheduledTaskInfo -TaskName $TaskName).NextRunTime)"
        Write-Host ""
        Write-Host "💡 팁:"
        Write-Host "  - 상태 확인: .\register_meta_supervisor_task.ps1 -Status"
        Write-Host "  - 즉시 실행: Start-ScheduledTask -TaskName '$TaskName'"
        Write-Host "  - 삭제: .\register_meta_supervisor_task.ps1 -Unregister"
        
    }
    catch {
        Write-Host "❌ 등록 실패: $_" -ForegroundColor Red
        exit 1
    }
    
    exit 0
}
