# Resonance Loop + 루멘 통합 실행 스크립트
# AGI 자기교정 루프에 페르소나 피드백을 통합합니다

param(
    [switch]$OpenReport
)

$ErrorActionPreference = "Stop"

Write-Host "`n🎯 Resonance Loop + 루멘 통합`n" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

# Python 스크립트 실행
$pythonExe = "$PSScriptRoot\..\fdo_agi_repo\.venv\Scripts\python.exe"
$scriptPath = "$PSScriptRoot\..\fdo_agi_repo\scripts\resonance_lumen_integration.py"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

& $pythonExe $scriptPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ 실패!`n" -ForegroundColor Red
    exit 1
}

Write-Host "`n════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
Write-Host "✅ Resonance Loop + 루멘 통합 완료!`n" -ForegroundColor Green

# 리포트 열기
$reportPath = "$PSScriptRoot\..\fdo_agi_repo\outputs\resonance_lumen_integration_latest.md"

if ($OpenReport -and (Test-Path $reportPath)) {
    Write-Host "📖 리포트 열기...`n" -ForegroundColor Cyan
    code $reportPath
}

Write-Host "💡 사용법:" -ForegroundColor Yellow
Write-Host "  스크립트만 실행: .\run_resonance_lumen_integration.ps1" -ForegroundColor Gray
Write-Host "  리포트 열기:     .\run_resonance_lumen_integration.ps1 -OpenReport`n" -ForegroundColor Gray
