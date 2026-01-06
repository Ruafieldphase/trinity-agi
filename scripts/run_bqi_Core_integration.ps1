# BQI Phase 6 + Core 통합 실행 스크립트
# 비노슈 학습에 Core 페르소나 피드백을 통합합니다

param(
    [switch]$OpenReport,
    [switch]$RunLearnerFirst
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

Write-Host "`n🎯 BQI Phase 6 + Core 통합`n" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

# BQI 학습 먼저 실행 (옵션)
if ($RunLearnerFirst) {
    Write-Host "1️⃣ BQI 학습 실행 중...`n" -ForegroundColor Yellow
    
    $learnerScript = "$WorkspaceRoot\fdo_agi_repo\scripts\run_bqi_learner.ps1"
    if (Test-Path $learnerScript) {
        & $learnerScript
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n⚠️ BQI 학습 실패, 계속 진행합니다`n" -ForegroundColor Yellow
        }
        else {
            Write-Host "`n✅ BQI 학습 완료`n" -ForegroundColor Green
        }
    }
}

# Python 스크립트 실행
$pythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$scriptPath = "$WorkspaceRoot\fdo_agi_repo\scripts\rune\bqi_core_integration.py"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

& $pythonExe $scriptPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ 실패!`n" -ForegroundColor Red
    exit 1
}

Write-Host "`n════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
Write-Host "✅ BQI Phase 6 + Core 통합 완료!`n" -ForegroundColor Green

# 리포트 열기
$reportPath = "$WorkspaceRoot\fdo_agi_repo\outputs\bqi_core_integration_latest.md"

if ($OpenReport -and (Test-Path $reportPath)) {
    Write-Host "📖 리포트 열기...`n" -ForegroundColor Cyan
    code $reportPath
}

Write-Host "💡 사용법:" -ForegroundColor Yellow
Write-Host "  기본 실행:       .\run_bqi_core_integration.ps1" -ForegroundColor Gray
Write-Host "  학습 후 실행:    .\run_bqi_core_integration.ps1 -RunLearnerFirst" -ForegroundColor Gray
Write-Host "  리포트 열기:     .\run_bqi_core_integration.ps1 -OpenReport`n" -ForegroundColor Gray