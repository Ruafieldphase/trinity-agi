# =============================================================================
# run_music_audio_analysis.ps1
# =============================================================================
# 음악 오디오 특징 추출 실행 스크립트
# Reaper 통합 준비 완료
# =============================================================================

param(
    [int]$SampleLimit = 5,
    [switch]$AllFiles,
    [switch]$OpenReport
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

$scriptName = "🎵 Music Audio Analysis"
$pythonScript = "$WorkspaceRoot\fdo_agi_repo\copilot\music_audio_analyzer.py"
$musicDir = "$WorkspaceRoot\music"
$outputMd = "$WorkspaceRoot\outputs\music_audio_features_latest.md"
$outputJson = "$WorkspaceRoot\outputs\music_audio_features_latest.json"

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "  $scriptName" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Python 경로 결정
$pythonExe = "$WorkspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "🔍 환경 체크" -ForegroundColor Yellow
Write-Host "   Python: " -NoNewline
Write-Host $pythonExe -ForegroundColor Cyan
Write-Host "   Music Dir: " -NoNewline
Write-Host $musicDir -ForegroundColor Cyan

# 음악 폴더 확인
if (!(Test-Path -LiteralPath $musicDir)) {
    Write-Host ""
    Write-Host "❌ 음악 폴더가 없습니다: $musicDir" -ForegroundColor Red
    exit 1
}

$musicFiles = Get-ChildItem -Path $musicDir -Filter "*.mp3" -File | Select-Object -First 3
if ($musicFiles.Count -eq 0) {
    Write-Host ""
    Write-Host "❌ MP3 파일이 없습니다." -ForegroundColor Red
    exit 1
}

Write-Host "   음악 파일: " -NoNewline
Write-Host "$($musicFiles.Count)개 발견" -ForegroundColor Green
Write-Host ""

# 실행
Write-Host "🎵 오디오 특징 추출 중..." -ForegroundColor Yellow
Write-Host ""

$args = @(
    $pythonScript,
    "--music-dir", $musicDir,
    "--sample-limit", $SampleLimit
)

if ($AllFiles) {
    $args += "--all-files"
}

try {
    & $pythonExe @args
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -ne 0) {
        Write-Host ""
        Write-Host "❌ 분석 실패 (Exit: $exitCode)" -ForegroundColor Red
        exit $exitCode
    }
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  ✅ 분석 완료!" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
    
    # 출력 파일 확인
    if (Test-Path -LiteralPath $outputMd) {
        Write-Host "📄 리포트: " -NoNewline
        Write-Host $outputMd -ForegroundColor Yellow
    }
    
    if (Test-Path -LiteralPath $outputJson) {
        Write-Host "📊 데이터: " -NoNewline
        Write-Host $outputJson -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "🎸 Reaper 통합 준비 완료!" -ForegroundColor Magenta
    Write-Host "   - 템포, 키, 에너지 데이터 추출됨" -ForegroundColor White
    Write-Host "   - Rhythm 상태와 자동 매핑 가능" -ForegroundColor White
    Write-Host ""
    
    # 리포트 열기
    if ($OpenReport -and (Test-Path -LiteralPath $outputMd)) {
        Write-Host "📖 리포트 열기..." -ForegroundColor Cyan
        & code $outputMd
    }
    
}
catch {
    Write-Host ""
    Write-Host "❌ 실행 오류: $_" -ForegroundColor Red
    exit 1
}