# AGI Task Scheduler 중지 및 정리

$ErrorActionPreference = "SilentlyContinue"

Write-Host "🛑 AGI Task Scheduler를 중지합니다..." -ForegroundColor Red

# Task 목록
$taskNames = @(
    "AGI_RhythmGuardian",
    "AGI_Heartbeat",
    "AGI_RhythmThink",
    "AGI_AuraController",
    "AGI_BackgroundSelfBridge",
    "AGI_AutonomousGoalExecutor"
)

# 각 Task 중지 및 삭제
foreach ($taskName in $taskNames) {
    Write-Host "   중지 중: $taskName" -ForegroundColor Gray
    schtasks /End /TN $taskName 2>$null | Out-Null
    schtasks /Delete /TN $taskName /F 2>$null | Out-Null
}

# Python 프로세스 강제 종료
Write-Host "   Python 프로세스 종료 중..." -ForegroundColor Gray
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force

# Guardian PID 파일 삭제
$pidFile = "C:\workspace\agi\logs\rhythm_guardian.pid"
if (Test-Path $pidFile) {
    Remove-Item $pidFile -Force
    Write-Host "   Guardian PID 파일 삭제됨" -ForegroundColor Gray
}

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "✅ AGI 시스템 완전히 중지됨" -ForegroundColor Green
