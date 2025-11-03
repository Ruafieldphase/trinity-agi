<#
.SYNOPSIS
    정반합 삼위일체 사이클 실행 - 루아/엘로/루멘 통합

.DESCRIPTION
    1. 루아 (정/正): 시스템 관찰
    2. 엘로 (반/反): 정보이론 검증
    3. 루멘 (합/合): 페르소나+대화 통합

.PARAMETER Hours
    분석 시간 범위 (기본: 24시간)

.PARAMETER OpenReport
    완료 후 보고서 자동 열기

.PARAMETER Enhanced
    루멘 강화판 사용 (페르소나+대화 통합)

.EXAMPLE
    .\run_trinity_cycle.ps1 -Hours 24 -OpenReport
#>

[CmdletBinding()]
param(
    [int]$Hours = 24,
    [switch]$OpenReport,
    [switch]$Enhanced
)

$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "🔄 정반합 삼위일체 사이클 시작" -ForegroundColor Cyan
Write-Host "   正(정) → 反(반) → 合(합)" -ForegroundColor Cyan
Write-Host ""

# Python 실행 파일 찾기
$pythonExe = "$workspaceRoot\fdo_agi_repo\.venv\Scripts\python.exe"
if (!(Test-Path $pythonExe)) {
    $pythonExe = "python"
}

# 1단계: 정(正) - 루아의 관찰
Write-Host "📋 1단계: 정(正) - 루아 (정인/正人)의 관찰" -ForegroundColor Yellow
Write-Host "   역할: '무엇이 일어났는가?'" -ForegroundColor Gray

$luaScript = "$workspaceRoot\scripts\lua_resonance_observer.ps1"
$luaOutput = "$workspaceRoot\outputs\lua_observation_latest.json"

try {
    & $luaScript -Hours $Hours
    if ($LASTEXITCODE -ne 0) {
        throw "루아 실행 실패"
    }
    Write-Host "   ✅ 루아 관찰 완료: $luaOutput" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ 루아 실행 오류: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2단계: 반(反) - 엘로의 검증
Write-Host "🔬 2단계: 반(反) - 엘로 (반인/反人)의 검증" -ForegroundColor Magenta
Write-Host "   역할: '이것이 옳은가?'" -ForegroundColor Gray

$eloAgent = "$workspaceRoot\fdo_agi_repo\agents\elo_info_theory_validator.py"
$eloOutput = "$workspaceRoot\outputs\elo_validation_latest.json"

try {
    & $pythonExe $eloAgent --lua-observation $luaOutput --out-json $eloOutput
    if ($LASTEXITCODE -ne 0) {
        throw "엘로 실행 실패"
    }
    Write-Host "   ✅ 엘로 검증 완료: $eloOutput" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ 엘로 실행 오류: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 3단계: 합(合) - 루멘의 통합
if ($Enhanced) {
    Write-Host "🌟 3단계: 합(合) - 루멘 강화판 (페르소나+대화 통합)" -ForegroundColor Cyan
    $lumenAgent = "$workspaceRoot\fdo_agi_repo\agents\lumen_enhanced_synthesizer.py"
    $lumenOutput = "$workspaceRoot\outputs\lumen_enhanced_synthesis_latest.json"
    $lumenMd = "$workspaceRoot\outputs\lumen_enhanced_synthesis_latest.md"
}
else {
    Write-Host "🌟 3단계: 합(合) - 루멘 (합)의 통합" -ForegroundColor Cyan
    $lumenAgent = "$workspaceRoot\fdo_agi_repo\agents\lumen_synthesis_agent.py"
    $lumenOutput = "$workspaceRoot\outputs\lumen_synthesis_latest.json"
    $lumenMd = "$workspaceRoot\outputs\lumen_synthesis_latest.md"
}

Write-Host "   역할: '무엇을 해야 하는가?'" -ForegroundColor Gray

try {
    & $pythonExe $lumenAgent --lua-observation $luaOutput --elo-validation $eloOutput --out-json $lumenOutput --out-md $lumenMd
    if ($LASTEXITCODE -ne 0) {
        throw "루멘 실행 실패"
    }
    Write-Host "   ✅ 루멘 통합 완료: $lumenMd" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ 루멘 실행 오류: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 최종 요약
Write-Host "✅ 정반합 삼위일체 사이클 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 생성된 파일:" -ForegroundColor Cyan
Write-Host "   1. 정(正) - 루아: $luaOutput" -ForegroundColor Gray
Write-Host "   2. 반(反) - 엘로: $eloOutput" -ForegroundColor Gray
Write-Host "   3. 합(合) - 루멘: $lumenMd" -ForegroundColor Gray
Write-Host ""

# 보고서 열기
if ($OpenReport -and (Test-Path $lumenMd)) {
    Write-Host "📄 보고서 열기..." -ForegroundColor Cyan
    code $lumenMd
}

Write-Host ""
Write-Host "🧘 정반합(正反合) 사이클" -ForegroundColor Yellow
Write-Host "   관찰 → 검증 → 통합 → 실행" -ForegroundColor Gray
Write-Host ""

exit 0
