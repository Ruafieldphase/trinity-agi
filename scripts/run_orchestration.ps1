# 자동화된 오케스트레이션 실행 스크립트
# 페르소나 협업을 자동으로 실행합니다

param(
    [Parameter(Mandatory = $true)]
    [string]$Topic,
    
    [switch]$OpenReport
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

Write-Host "`n🎭 자동화된 오케스트레이션`n" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
Write-Host "주제: $Topic`n" -ForegroundColor Yellow

# Python 스크립트 실행
$scriptPath = "$PSScriptRoot\auto_orchestration.py"

if (-not (Test-Path $scriptPath)) {
    Write-Host "❌ 스크립트를 찾을 수 없습니다: $scriptPath`n" -ForegroundColor Red
    exit 1
}

python $scriptPath $Topic

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ 실패!`n" -ForegroundColor Red
    exit 1
}

Write-Host "`n════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
Write-Host "✅ 오케스트레이션 완료!`n" -ForegroundColor Green

# 리포트 열기
$reportPath = "$WorkspaceRoot\outputs\orchestration_latest.md"

if ($OpenReport -and (Test-Path $reportPath)) {
    Write-Host "📖 리포트 열기...`n" -ForegroundColor Cyan
    code $reportPath
}

Write-Host "💡 사용법:" -ForegroundColor Yellow
Write-Host "  기본: .\run_orchestration.ps1 -Topic '주제'" -ForegroundColor Gray
Write-Host "  열기: .\run_orchestration.ps1 -Topic '주제' -OpenReport`n" -ForegroundColor Gray

Write-Host "📋 생성된 파일:" -ForegroundColor Cyan
Write-Host "  • outputs\orchestration_latest.md" -ForegroundColor Gray
Write-Host "  • outputs\orchestration_log.jsonl`n" -ForegroundColor Gray