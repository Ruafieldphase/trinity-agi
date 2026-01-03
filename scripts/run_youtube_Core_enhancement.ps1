# YouTube 학습 + Core 강화 실행 스크립트
# 최신 YouTube 분석 결과에 페르소나 인사이트를 통합합니다

param(
    [switch]$OpenReport,
    [string]$VideoId
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

Write-Host "`n🎬 YouTube 학습 + Core 강화`n" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Gray

# Python 스크립트 실행
$pythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
$scriptPath = "$WorkspaceRoot\fdo_agi_repo\integrations\youtube_core_enhancer.py"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

& $pythonExe $scriptPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ 실패!`n" -ForegroundColor Red
    exit 1
}

Write-Host "`n════════════════════════════════════════════════════════════`n" -ForegroundColor Gray
Write-Host "✅ YouTube 학습 강화 완료!`n" -ForegroundColor Green

# 리포트 열기
if ($OpenReport) {
    $outputDir = "$WorkspaceRoot\outputs"
    
    # 최신 강화 리포트 찾기
    $latestReport = Get-ChildItem -Path $outputDir -Filter "youtube_enhanced_*.md" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
    
    if ($latestReport) {
        Write-Host "📖 리포트 열기: $($latestReport.Name)`n" -ForegroundColor Cyan
        code $latestReport.FullName
    }
    else {
        Write-Host "⚠️ 리포트를 찾을 수 없습니다`n" -ForegroundColor Yellow
    }
}

Write-Host "💡 사용법:" -ForegroundColor Yellow
Write-Host "  기본 실행:       .\run_youtube_core_enhancement.ps1" -ForegroundColor Gray
Write-Host "  리포트 열기:     .\run_youtube_core_enhancement.ps1 -OpenReport`n" -ForegroundColor Gray

Write-Host "📂 생성 파일 위치:" -ForegroundColor Cyan
Write-Host "  • outputs\youtube_enhanced_*.md" -ForegroundColor Gray
Write-Host "  • outputs\youtube_enhanced_*.json`n" -ForegroundColor Gray

Write-Host "🎯 다음 단계:" -ForegroundColor Yellow
Write-Host "  1. RPA로 새 영상 학습: YouTube: Learn from URL (Pipeline)" -ForegroundColor Gray
Write-Host "  2. 자동 강화: 이 스크립트 재실행`n" -ForegroundColor Gray