# Parallel Antithesis Prep - Smoke Test
# Phase 2: Antithesis 준비 작업 병렬화 검증

param(
    [switch]$EnableParallel = $false,
    [switch]$Verbose = $false
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "🧪 Parallel Antithesis Prep - Smoke Test" -ForegroundColor Cyan
Write-Host "Mode: $(if ($EnableParallel) { 'PARALLEL ENABLED' } else { 'SEQUENTIAL (baseline)' })" -ForegroundColor Yellow
Write-Host ""

# 환경 설정
if ($EnableParallel) {
    $env:PARALLEL_ANTITHESIS_PREP_ENABLED = "true"
    # app.yaml 업데이트
    $configPath = Join-Path $WorkspaceRoot "fdo_agi_repo\configs\app.yaml"
    if (Test-Path $configPath) {
        $config = Get-Content $configPath -Raw
        $config = $config -replace "parallel_antithesis_prep:\s+enabled:\s+false", "parallel_antithesis_prep:`n    enabled: true"
        Set-Content $configPath -Value $config -Encoding UTF8
        Write-Host "✅ app.yaml updated (parallel_antithesis_prep: enabled: true)" -ForegroundColor Green
    }
}
else {
    $env:PARALLEL_ANTITHESIS_PREP_ENABLED = "false"
}

# Python 실행
$pythonExe = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

# 스모크 테스트 (간단한 태스크 1개)
Write-Host "Running smoke test task..." -ForegroundColor Cyan
$taskJson = @{
    task_id = "smoke-parallel-anti-$(Get-Date -Format 'HHmmss')"
    title   = "Parallel Antithesis Prep Smoke Test"
    goal    = "AGI 리듬 검증 (간단한 3문장)"
} | ConvertTo-Json -Compress

$scriptPath = Join-Path $WorkspaceRoot "fdo_agi_repo\scripts\run_task.py"
$startTime = Get-Date

try {
    $output = & $pythonExe $scriptPath --title "Parallel Anti Smoke" --goal "AGI 리듬 검증 (간단한 3문장)" 2>&1
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($Verbose) {
        Write-Host ""
        Write-Host "=== Output ===" -ForegroundColor Gray
        Write-Host $output
        Write-Host "=============" -ForegroundColor Gray
        Write-Host ""
    }
    
    if ($exitCode -eq 0) {
        Write-Host "✅ Task completed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Task failed (exit code: $exitCode)" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Error running task: $_" -ForegroundColor Red
    exit 1
}

# Ledger 분석
Write-Host ""
Write-Host "📊 Analyzing Ledger..." -ForegroundColor Cyan

$ledgerPath = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\resonance_ledger.jsonl"
if (-not (Test-Path $ledgerPath)) {
    Write-Host "⚠️  Ledger not found" -ForegroundColor Yellow
    exit 0
}

# 최근 이벤트만 추출 (마지막 100줄)
$recentEvents = Get-Content $ledgerPath -Tail 100 | ForEach-Object {
    try { $_ | ConvertFrom-Json } catch { $null }
} | Where-Object { $_ -ne $null }

# Parallel prep 이벤트 확인
$parallelEvents = $recentEvents | Where-Object {
    $_.event -like "*parallel*" -or $_.event -like "*antithesis*"
}

if ($EnableParallel) {
    Write-Host ""
    Write-Host "=== Parallel Events ===" -ForegroundColor Magenta
    $parallelEvents | ForEach-Object {
        Write-Host "  - $($_.event) (task: $($_.task_id))" -ForegroundColor White
    }
    
    $prepEnabled = $parallelEvents | Where-Object { $_.event -eq "parallel_antithesis_prep_enabled" }
    $prepDone = $parallelEvents | Where-Object { $_.event -eq "parallel_antithesis_prep_done" }
    $usingPrep = $parallelEvents | Where-Object { $_.event -eq "antithesis_using_prep_context" }
    
    if ($prepEnabled -and $prepDone -and $usingPrep) {
        Write-Host ""
        Write-Host "✅ Parallel Antithesis Prep: VERIFIED" -ForegroundColor Green
        Write-Host "   - prep_enabled: YES" -ForegroundColor Gray
        Write-Host "   - prep_done: YES" -ForegroundColor Gray
        Write-Host "   - using_prep_context: YES" -ForegroundColor Gray
    }
    else {
        Write-Host ""
        Write-Host "⚠️  Parallel Antithesis Prep: INCOMPLETE" -ForegroundColor Yellow
        Write-Host "   - prep_enabled: $(if ($prepEnabled) { 'YES' } else { 'NO' })" -ForegroundColor Gray
        Write-Host "   - prep_done: $(if ($prepDone) { 'YES' } else { 'NO' })" -ForegroundColor Gray
        Write-Host "   - using_prep_context: $(if ($usingPrep) { 'YES' } else { 'NO' })" -ForegroundColor Gray
    }
}

# 레이턴시 계산
$thesisEvents = $recentEvents | Where-Object { $_.event -in @("thesis_start", "thesis_end") }
$antithesisEvents = $recentEvents | Where-Object { $_.event -in @("antithesis_start", "antithesis_end") }

if ($thesisEvents.Count -ge 2 -and $antithesisEvents.Count -ge 2) {
    $thesisStart = ($thesisEvents | Where-Object { $_.event -eq "thesis_start" })[-1]
    $thesisEnd = ($thesisEvents | Where-Object { $_.event -eq "thesis_end" })[-1]
    $antiStart = ($antithesisEvents | Where-Object { $_.event -eq "antithesis_start" })[-1]
    $antiEnd = ($antithesisEvents | Where-Object { $_.event -eq "antithesis_end" })[-1]
    
    if ($thesisEnd.duration_sec) {
        $thesisDuration = [math]::Round($thesisEnd.duration_sec, 2)
        Write-Host ""
        Write-Host "⏱️  Thesis Duration: ${thesisDuration}s" -ForegroundColor Cyan
    }
    
    if ($antiEnd.duration_sec) {
        $antiDuration = [math]::Round($antiEnd.duration_sec, 2)
        Write-Host "⏱️  Antithesis Duration: ${antiDuration}s" -ForegroundColor Cyan
    }
    
    Write-Host "⏱️  Total Duration: $([math]::Round($duration, 2))s" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "✅ Smoke test complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run baseline: .\scripts\smoke_parallel_antithesis.ps1" -ForegroundColor Gray
Write-Host "  2. Run parallel: .\scripts\smoke_parallel_antithesis.ps1 -EnableParallel" -ForegroundColor Gray
Write-Host "  3. Compare latency improvements" -ForegroundColor Gray