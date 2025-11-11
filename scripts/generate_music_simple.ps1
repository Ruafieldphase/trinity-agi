# Reaper 음악 생성 래퍼 (간단 버전)
# 페이즈별 음악 프로젝트 생성 + Reaper에서 열기

param(
    [ValidateSet("wake_up", "coding", "focus", "rest", "transition")]
    [string]$Category = "coding",
    
    [switch]$List,
    [switch]$Open
)

$ErrorActionPreference = "Stop"
$ws = Split-Path -Parent $PSScriptRoot

if ($List) {
    Write-Host "`n🎼 Available Music Categories:" -ForegroundColor Green
    Write-Host "=" * 60
    
    $categories = @{
        "wake_up"    = "각성용 - BPM 135, HIGH energy, 3분"
        "coding"     = "코딩 흐름 - BPM 120, MEDIUM energy, 15분"
        "focus"      = "깊은 집중 - BPM 75, LOW energy, 20분"
        "rest"       = "휴식/회복 - BPM 50, VERY LOW, 10분"
        "transition" = "페이즈 전환 - BPM 90, LOW energy, 5분"
    }
    
    foreach ($cat in $categories.GetEnumerator() | Sort-Object Name) {
        Write-Host "`n$($cat.Key.ToUpper())" -ForegroundColor Cyan
        Write-Host "  $($cat.Value)" -ForegroundColor Gray
    }
    
    Write-Host ""
    exit 0
}

Write-Host "`n🎵 Generating $($Category.ToUpper()) music project..." -ForegroundColor Green
Write-Host "=" * 60

# Python 실행
$pyExe = "$ws\fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $pyExe)) {
    $pyExe = "python"
}

$scriptPath = "$ws\scripts\generate_adaptive_music.py"

& $pyExe $scriptPath --category $Category

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Generation failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 가장 최근 생성된 프로젝트 찾기
$projectsDir = "$ws\reaper_projects"
$latestProject = Get-ChildItem "$projectsDir\${Category}_*.rpp" -ErrorAction SilentlyContinue |
Sort-Object LastWriteTime -Descending |
Select-Object -First 1

if ($latestProject -and $Open) {
    Write-Host "`n🚀 Opening in Reaper..." -ForegroundColor Yellow
    
    # Reaper 실행 파일 찾기
    $reaperPaths = @(
        "C:\Program Files\REAPER (x64)\reaper.exe",
        "C:\Program Files\REAPER\reaper.exe"
    )
    
    $reaperExe = $reaperPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    
    if ($reaperExe) {
        Start-Process $reaperExe -ArgumentList "`"$($latestProject.FullName)`""
        Write-Host "✅ Reaper launched" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️ Reaper not found. Install from: https://www.reaper.fm/" -ForegroundColor Yellow
        Write-Host "   Project saved: $($latestProject.FullName)" -ForegroundColor Cyan
    }
}

Write-Host "`n✅ Complete!" -ForegroundColor Green

if (-not $Open) {
    Write-Host "`nTip: Add -Open to automatically launch Reaper" -ForegroundColor Yellow
}
