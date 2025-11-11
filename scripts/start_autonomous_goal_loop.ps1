<#
.SYNOPSIS
    자율 목표 실행 시스템 - 적응형 리듬 백그라운드 루프

.DESCRIPTION
    적응형 리듬에 따라 autonomous_goal_executor.py를 실행합니다.
    
    간격은 고정되지 않고, 다음 요소에 따라 동적으로 조정됩니다:
    - 시간대 (집중 시간 5-15분, 휴식 시간 30-60분)
    - 최근 성공률 (연속 성공 시 더 자주, 실패 시 덜 자주)
    - 시스템 활동도 (과부하 방지)
    
    철학: "자연스러운 흐름, 강제하지 않는 리듬"

.EXAMPLE
    .\start_autonomous_goal_loop.ps1
#>

$ErrorActionPreference = "Stop"

$WorkspaceRoot = Split-Path $PSScriptRoot -Parent
$PythonExe = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
$ExecutorScript = Join-Path $WorkspaceRoot "scripts\autonomous_goal_executor.py"
$RhythmCalculator = Join-Path $WorkspaceRoot "scripts\adaptive_rhythm_calculator.py"
$LogFile = Join-Path $WorkspaceRoot "outputs\autonomous_goal_loop.log"

# Python 경로 확인
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

# Executor 스크립트 확인
if (-not (Test-Path $ExecutorScript)) {
    Write-Host "❌ Executor 스크립트를 찾을 수 없습니다: $ExecutorScript" -ForegroundColor Red
    exit 1
}

# 기존 루프 프로세스 확인
$existing = Get-Process -Name "python", "pwsh", "powershell" -ErrorAction SilentlyContinue | 
Where-Object { $_.CommandLine -like "*autonomous_goal_loop_daemon.ps1*" }

if ($existing) {
    Write-Host "`n⚠️  백그라운드 루프가 이미 실행 중입니다." -ForegroundColor Yellow
    Write-Host "   PID: $($existing.Id -join ', ')" -ForegroundColor Gray
    Write-Host "`n💡 중지하려면: .\scripts\stop_autonomous_goal_loop.ps1" -ForegroundColor Cyan
    Write-Host "💡 상태 확인: .\scripts\stop_autonomous_goal_loop.ps1 -Status" -ForegroundColor Cyan
    exit 0
}

# 데몬 스크립트 경로
$DaemonScript = Join-Path $WorkspaceRoot "scripts\autonomous_goal_loop_daemon.ps1"

if (-not (Test-Path $DaemonScript)) {
    Write-Host "❌ Daemon 스크립트를 찾을 수 없습니다: $DaemonScript" -ForegroundColor Red
    exit 1
}

# Stop flag 제거 (clean start)
$StopFlag = Join-Path $WorkspaceRoot "outputs\stop_autonomous_goal_loop.flag"
if (Test-Path $StopFlag) {
    Write-Host "🧹 기존 정지 플래그 제거 중..." -ForegroundColor Yellow
    Remove-Item -LiteralPath $StopFlag -Force
}

Write-Host "`n🚀 적응형 리듬 백그라운드 루프 시작 중..." -ForegroundColor Cyan
Write-Host "   모드: 적응형 리듬 (5-60분 가변)" -ForegroundColor Yellow
Write-Host "   철학: 자연스러운 흐름, 강제하지 않는 리듬" -ForegroundColor Gray
Write-Host "   로그: outputs\autonomous_goal_loop.log" -ForegroundColor Gray
Write-Host ""

# 백그라운드 프로세스 시작
$job = Start-Job -ScriptBlock {
    param($DaemonScript)
    & powershell -NoProfile -ExecutionPolicy Bypass -File $DaemonScript
} -ArgumentList $DaemonScript

# Wait a moment to verify startup
Start-Sleep -Seconds 2
$jobState = (Get-Job -Id $job.Id).State

if ($jobState -eq 'Running') {
    Write-Host "✅ 적응형 리듬 루프가 시작되었습니다!" -ForegroundColor Green
    Write-Host "   Job ID: $($job.Id)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 명령어:" -ForegroundColor Cyan
    Write-Host "   상태 확인: .\scripts\stop_autonomous_goal_loop.ps1 -Status" -ForegroundColor White
    Write-Host "   리듬 확인: python scripts\adaptive_rhythm_calculator.py" -ForegroundColor White
    Write-Host "   우아한 종료: .\scripts\stop_autonomous_goal_loop.ps1" -ForegroundColor White
    Write-Host "   강제 종료: .\scripts\stop_autonomous_goal_loop.ps1 -Force" -ForegroundColor White
    Write-Host "   로그 보기: Get-Content outputs\autonomous_goal_loop.log -Tail 20 -Wait" -ForegroundColor White
    Write-Host ""
}
else {
    Write-Host "❌ 백그라운드 실행 실패. Job 상태: $jobState" -ForegroundColor Red
    Get-Job -Id $job.Id | Receive-Job
    Remove-Job -Id $job.Id -Force
    exit 1
}
