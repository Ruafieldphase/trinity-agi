<#
.SYNOPSIS
Meta Supervisor 백그라운드 실행

.DESCRIPTION
PowerShell 백그라운드 Job으로 Meta Supervisor를 15분 간격으로 실행합니다.
관리자 권한 불필요하며, 즉시 시작됩니다.

.PARAMETER KillExisting
기존 실행 중인 Meta Supervisor Job을 종료하고 새로 시작

.PARAMETER IntervalMinutes
실행 간격 (분, 기본 15분)

.EXAMPLE
.\start_meta_supervisor_daemon.ps1
기존 Job 확인 후 필요시 시작

.EXAMPLE
.\start_meta_supervisor_daemon.ps1 -KillExisting
기존 Job 종료하고 새로 시작
#>

param(
    [switch]$KillExisting,
    [int]$IntervalMinutes = 15
)

$ErrorActionPreference = "Stop"
$workspaceRoot = Split-Path $PSScriptRoot -Parent
$pythonExe = Join-Path $workspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
$scriptPath = Join-Path $PSScriptRoot "meta_supervisor.py"
$ensureGoalMonitor = Join-Path $PSScriptRoot "ensure_goal_executor_monitor.ps1"
$jobName = "MetaSupervisorDaemon"

if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ Meta Supervisor 스크립트 없음: $scriptPath" -ForegroundColor Red
    exit 1
}

# Python 실행 파일 확인
if (-not (Test-Path $pythonExe)) {
    Write-Host "⚠️  가상환경 Python 없음, 시스템 Python 사용" -ForegroundColor Yellow
    $pythonExe = "python"
}

# 기존 Job 확인
$existingJob = Get-Job -Name $jobName -ErrorAction SilentlyContinue

if ($existingJob) {
    if ($KillExisting) {
        Write-Host "🛑 기존 Meta Supervisor Job 종료 중..." -ForegroundColor Yellow
        Stop-Job -Name $jobName -ErrorAction SilentlyContinue
        Remove-Job -Name $jobName -Force -ErrorAction SilentlyContinue
        Write-Host "✅ 기존 Job 종료 완료" -ForegroundColor Green
        Write-Host ""
    }
    else {
        Write-Host "ℹ️  Meta Supervisor가 이미 실행 중입니다." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Job 정보:"
        Write-Host "  ID: $($existingJob.Id)"
        Write-Host "  상태: $($existingJob.State)"
        Write-Host "  시작 시각: $($existingJob.PSBeginTime)"
        Write-Host ""
        Write-Host "💡 재시작하려면: .\start_meta_supervisor_daemon.ps1 -KillExisting"
        Write-Host "💡 종료하려면: .\stop_meta_supervisor_daemon.ps1"
        exit 0
    }
}

# Ensure Goal Executor Monitor scheduled task exists (user mode)
try {
    if (Test-Path $ensureGoalMonitor) {
        Write-Host "🔎 Ensuring Goal Executor Monitor registration..." -ForegroundColor Cyan
        & $ensureGoalMonitor -IntervalMinutes 10 -ThresholdMinutes 15 -Quiet
    }
}
catch {
    Write-Host "⚠️  Goal Monitor ensure failed: $_" -ForegroundColor Yellow
}

# 백그라운드 스크립트 블록
$scriptBlock = {
    param($pythonPath, $scriptPath, $intervalMinutes)
    
    $iteration = 0
    while ($true) {
        $iteration++
        Write-Host "🌊 Meta Supervisor Iteration #$iteration - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        
        try {
            # Meta Supervisor 실행
            & $pythonPath $scriptPath
            $exitCode = $LASTEXITCODE
            
            if ($exitCode -eq 0) {
                Write-Host "✅ 정상 (exit code: 0)" -ForegroundColor Green
            }
            elseif ($exitCode -eq 1) {
                Write-Host "⚠️  경고 (exit code: 1)" -ForegroundColor Yellow
            }
            elseif ($exitCode -eq 2) {
                Write-Host "🚨 심각 (exit code: 2)" -ForegroundColor Red
            }
            else {
                Write-Host "❌ 실패 (exit code: $exitCode)" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "❌ 예외 발생: $_" -ForegroundColor Red
        }
        
        Write-Host "⏳ $intervalMinutes 분 대기 중..."
        Write-Host ""
        
        Start-Sleep -Seconds ($intervalMinutes * 60)
    }
}

# Job 시작
Write-Host "🚀 Meta Supervisor 백그라운드 실행 시작..." -ForegroundColor Cyan
Write-Host ""
Write-Host "설정:"
Write-Host "  간격: $IntervalMinutes 분"
Write-Host "  Python: $pythonExe"
Write-Host "  스크립트: $scriptPath"
Write-Host ""

$job = Start-Job -Name $jobName -ScriptBlock $scriptBlock -ArgumentList $pythonExe, $scriptPath, $IntervalMinutes

Write-Host "✅ 백그라운드 Job 시작 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "Job 정보:"
Write-Host "  ID: $($job.Id)"
Write-Host "  이름: $jobName"
Write-Host "  상태: $($job.State)"
Write-Host ""
Write-Host "💡 관리 명령:"
Write-Host "  상태 확인: .\check_meta_supervisor_daemon_status.ps1"
Write-Host "  로그 보기: Get-Job -Name $jobName | Receive-Job -Keep"
Write-Host "  종료: .\stop_meta_supervisor_daemon.ps1"
Write-Host ""
Write-Host "🌊 Meta Supervisor가 $IntervalMinutes 분마다 시스템을 모니터링합니다."
