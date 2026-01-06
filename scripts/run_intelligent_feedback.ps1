# 지능형 피드백 적용 시스템 실행 스크립트
# 페르소나 피드백을 분석하여 구현 가능한 개선 계획을 생성합니다

param(
    [switch]$OpenReport
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

Write-Host "`n🧠 지능형 피드백 적용 시스템`n" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

# Python 스크립트 실행
$pythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$scriptPath = "$WorkspaceRoot\fdo_agi_repo\scripts\intelligent_feedback_applicator.py"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

& $pythonExe $scriptPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ 실패!`n" -ForegroundColor Red
    exit 1
}

Write-Host "`n════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
Write-Host "✅ 구현 계획 생성 완료!`n" -ForegroundColor Green

# 리포트 열기
if ($OpenReport) {
    $reportFile = "$WorkspaceRoot\outputs\feedback_implementation_plan.md"
    
    if (Test-Path $reportFile) {
        Write-Host "📖 리포트 열기...`n" -ForegroundColor Cyan
        code $reportFile
    }
    else {
        Write-Host "⚠️ 리포트를 찾을 수 없습니다`n" -ForegroundColor Yellow
    }
}

Write-Host "💡 사용법:" -ForegroundColor Yellow
Write-Host "  기본 실행:       .\run_intelligent_feedback.ps1" -ForegroundColor Gray
Write-Host "  리포트 열기:     .\run_intelligent_feedback.ps1 -OpenReport`n" -ForegroundColor Gray

Write-Host "📂 생성 파일:" -ForegroundColor Cyan
Write-Host "  • outputs\feedback_implementation_plan.md" -ForegroundColor Gray
Write-Host "  • outputs\feedback_implementation_plan.json`n" -ForegroundColor Gray

Write-Host "🎯 워크플로우:" -ForegroundColor Yellow
Write-Host "  1. 페르소나 피드백 수집 (Resonance, BQI)" -ForegroundColor Gray
Write-Host "  2. 루빗에게 구현 방안 문의" -ForegroundColor Gray
Write-Host "  3. 구현 계획 생성" -ForegroundColor Gray
Write-Host "  4. 안전한 변경 사항 검토 및 적용`n" -ForegroundColor Gray

Write-Host "🔒 안전 장치:" -ForegroundColor Cyan
Write-Host "  • 자동 적용 전 사람 검토 필수" -ForegroundColor Gray
Write-Host "  • 모든 변경 사항 로그 기록" -ForegroundColor Gray
Write-Host "  • 롤백 메커니즘 준비`n" -ForegroundColor Gray