<#
.SYNOPSIS
    자기생산 + 정반합 삼위일체 사이클 자동 실행 등록/해제

.DESCRIPTION
    Windows Task Scheduler에 일일 자동 실행을 등록합니다.
    - 매일 지정된 시간에 자동 실행
    - Wake-to-run 지원 (시스템이 Sleep일 경우 깨워서 실행)
    - 실행 결과 로그 자동 저장

.PARAMETER Register
    Task를 등록합니다

.PARAMETER Unregister
    Task를 해제합니다

.PARAMETER Time
    실행 시간 (HH:mm 형식, 예: "10:00")

.PARAMETER Hours
    분석 시간 범위 (기본: 24시간)

.EXAMPLE
    .\register_trinity_cycle_task.ps1 -Register -Time "10:00"
    매일 오전 10시에 24시간 데이터를 분석하도록 등록

.EXAMPLE
    .\register_trinity_cycle_task.ps1 -Unregister
    등록된 Task 제거
#>

param(
    [switch]$Register,
    [switch]$Unregister,
    [string]$Time = "10:00",
    [int]$Hours = 24
)

$ErrorActionPreference = "Stop"
$TaskName = "AGI_AutopoieticTrinityCycle"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# UTF-8 출력
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Admin 권한 체크 (Register/Unregister 시에만 필요)
if ($Register -or $Unregister) {
    if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Host "❌ 이 작업은 관리자 권한이 필요합니다." -ForegroundColor Red
        Write-Host "   PowerShell을 관리자 권한으로 실행한 후 다시 시도하세요." -ForegroundColor Yellow
        exit 1
    }
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Show-Status {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  🔄 자기생산 + 정반합 삼위일체 사이클 스케줄러" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""

    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        
        if ($task) {
            $info = Get-ScheduledTaskInfo -TaskName $TaskName
            
            Write-Host "✅ Task 등록 상태: " -NoNewline -ForegroundColor Green
            Write-Host "활성화됨" -ForegroundColor White
            Write-Host ""
            
            Write-Host "📋 설정 정보:" -ForegroundColor Yellow
            Write-Host "   Task 이름: $TaskName"
            Write-Host "   실행 시간: $($task.Triggers[0].StartBoundary)"
            Write-Host "   마지막 실행: $($info.LastRunTime)"
            Write-Host "   다음 실행: $($info.NextRunTime)"
            Write-Host "   마지막 결과: $($info.LastTaskResult)"
            Write-Host ""
            
            Write-Host "📂 실행 로그:" -ForegroundColor Yellow
            $logFile = Join-Path $WorkspaceRoot "outputs\trinity_cycle_scheduled.log"
            if (Test-Path $logFile) {
                Write-Host "   위치: $logFile"
                Write-Host "   크기: $([math]::Round((Get-Item $logFile).Length / 1KB, 2)) KB"
            }
            else {
                Write-Host "   (아직 실행되지 않음)"
            }
        }
        else {
            Write-Host "ℹ️  Task 등록 상태: " -NoNewline -ForegroundColor Yellow
            Write-Host "등록 안 됨" -ForegroundColor Gray
            Write-Host ""
            Write-Host "💡 등록 방법:" -ForegroundColor Cyan
            Write-Host ("   .\register_trinity_cycle_task.ps1 -Register -Time `"{0}`"" -f $Time)
        }
    }
    catch {
        Write-Host "❌ 오류: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

function Register-Task {
    Write-Host ""
    Write-Host "📝 Task 등록 중..." -ForegroundColor Cyan
    Write-Host "   Task 이름: $TaskName"
    Write-Host "   실행 시간: 매일 $Time"
    Write-Host "   분석 범위: 최근 $Hours 시간"
    Write-Host ""

    # 기존 Task 제거
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "🗑️  기존 Task 제거 중..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "   ✅ 기존 Task 제거 완료" -ForegroundColor Green
    }

    # 스크립트 경로
    $scriptPath = Join-Path $WorkspaceRoot "scripts\autopoietic_trinity_cycle.ps1"
    $logFile = Join-Path $WorkspaceRoot "outputs\trinity_cycle_scheduled.log"

    # 실행 명령
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Hours $Hours >> `"$logFile`" 2>&1"

    # 트리거 (매일 지정 시간)
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time

    # 설정
    $settings = New-ScheduledTaskSettingsSet `
$settings.Hidden = $true
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -WakeToRun `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 5)

    # 현재 사용자로 실행
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Highest

    # Task 등록
    try {
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description "자기생산 + 정반합 삼위일체 사이클 자동 실행 (매일 $Time)" `
        | Out-Null

        Write-Host "✅ Task 등록 완료!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 등록 정보:" -ForegroundColor Yellow
        Write-Host "   실행 스크립트: $scriptPath"
        Write-Host "   실행 로그: $logFile"
        Write-Host "   Wake-to-run: 활성화됨 (Sleep 중에도 깨워서 실행)"
        Write-Host ""
        Write-Host "💡 확인 방법:" -ForegroundColor Cyan
        Write-Host "   1. Task Scheduler 실행 (taskschd.msc)"
        Write-Host "   2. `"$TaskName`" 검색"
        Write-Host "   또는"
        Write-Host "   .\register_trinity_cycle_task.ps1  (인자 없이 실행)"
        Write-Host ""
    }
    catch {
        Write-Host "❌ Task 등록 실패: $_" -ForegroundColor Red
        exit 1
    }
}

function Unregister-Task {
    Write-Host ""
    Write-Host "🗑️  Task 제거 중..." -ForegroundColor Yellow
    Write-Host "   Task 이름: $TaskName"
    Write-Host ""

    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        
        if ($task) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "✅ Task 제거 완료!" -ForegroundColor Green
            Write-Host ""
        }
        else {
            Write-Host "ℹ️  Task가 등록되어 있지 않습니다." -ForegroundColor Yellow
            Write-Host ""
        }
    }
    catch {
        Write-Host "❌ Task 제거 실패: $_" -ForegroundColor Red
        exit 1
    }
}

# ============================================================
# Main
# ============================================================

if ($Register) {
    Register-Task
    Show-Status
}
elseif ($Unregister) {
    Unregister-Task
}
else {
    Show-Status
}

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
