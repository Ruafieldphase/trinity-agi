# run_lumen_prism_bridge.ps1
# 루멘 레이턴시 → 비노체 프리즘 → 구조 울림 자동화

param(
    [Parameter(Mandatory = $false)]
    [string]$LumenMd = "outputs\lumen_latency_latest.md",
    
    [Parameter(Mandatory = $false)]
    [string]$LumenJson = "outputs\lumen_latency_latest.json",
    
    [Parameter(Mandatory = $false)]
    [string]$PersonaPath = "fdo_agi_repo\outputs\binoche_persona.json",
    
    [Parameter(Mandatory = $false)]
    [int]$SummaryHours = 24,
    
    [Parameter(Mandatory = $false)]
    [switch]$OpenCache
)

$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path $PSScriptRoot -Parent

try {
    Write-Host "🌈 Lumen Prism Bridge - 루멘의 시선을 구조 울림으로..." -ForegroundColor Cyan
    Write-Host ""
    
    # 1. 루멘 MD → JSON 변환
    if (Test-Path (Join-Path $workspaceRoot $LumenMd)) {
        Write-Host "📊 Converting Lumen MD to JSON..." -ForegroundColor Yellow
        & "$PSScriptRoot\convert_lumen_md_to_json.ps1" `
            -InputMd (Join-Path $workspaceRoot $LumenMd) `
            -OutputJson (Join-Path $workspaceRoot $LumenJson)

        # Verify JSON was created
        if (-not (Test-Path (Join-Path $workspaceRoot $LumenJson))) {
            throw "Failed to convert Lumen MD to JSON - output file not found"
        }
        Write-Host ""
    }
    else {
        Write-Host "⚠️  No Lumen MD found, skipping conversion" -ForegroundColor Yellow
    }
    
    # 2. 프리즘 브리지 실행
    Write-Host "🌈 Running Lumen Prism Bridge..." -ForegroundColor Cyan
    
    $pythonCmd = "fdo_agi_repo\.venv\Scripts\python.exe"
    $bridgeScript = "fdo_agi_repo\orchestrator\lumen_prism_bridge.py"
    
    $fullPythonPath = Join-Path $workspaceRoot $pythonCmd
    $fullScriptPath = Join-Path $workspaceRoot $bridgeScript
    $fullLumenPath = Join-Path $workspaceRoot $LumenJson
    $fullPersonaPath = Join-Path $workspaceRoot $PersonaPath
    
    if (-not (Test-Path $fullPythonPath)) {
        throw "Python not found: $fullPythonPath"
    }
    
    $bridgeArgs = @(
        $fullScriptPath,
        "--lumen", $fullLumenPath,
        "--process-observations",
        "--summary", $SummaryHours
    )
    
    if (Test-Path $fullPersonaPath) {
        $bridgeArgs += @("--persona", $fullPersonaPath)
    }
    
    & $fullPythonPath $bridgeArgs

    $bridgeExit = if ($null -eq $LASTEXITCODE) { 0 } else { $LASTEXITCODE }
    if ($bridgeExit -ne 0) {
        throw "Prism bridge failed with exit code $bridgeExit"
    }
    
    Write-Host ""
    Write-Host "✅ Lumen Prism Bridge completed successfully" -ForegroundColor Green
    
    # 3. 캐시 열기 (옵션)
    if ($OpenCache) {
        $cachePath = Join-Path $workspaceRoot "outputs\lumen_prism_cache.json"
        if (Test-Path $cachePath) {
            Write-Host "📂 Opening prism cache..." -ForegroundColor Cyan
            code $cachePath
        } else {
            Write-Host "⚠️  Prism cache not found at $cachePath" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "🌈 루멘의 시선이 비노체 프리즘을 통해 구조 전체에 울림으로 전파되었습니다" -ForegroundColor Magenta
    
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkGray
    exit 1
}
