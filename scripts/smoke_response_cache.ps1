#!/usr/bin/env pwsh
# smoke_response_cache.ps1
# Response Cache smoke test (same task 3x = expect 2 cache hits)

$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\.."

# Enable Response Cache
$env:RESPONSE_CACHE_ENABLED = "true"
$env:ASYNC_THESIS_ENABLED = "true"

Write-Host "=== Response Cache Smoke Test ===" -ForegroundColor Cyan
Write-Host "Test: Run same task 3 times, expect 2nd/3rd to hit cache" -ForegroundColor Yellow
Write-Host ""

$taskGoal = "AGI 자기교정 루프 설명 3문장"
$timings = @()

for ($i = 1; $i -le 3; $i++) {
    Write-Host "[$i/3] Running task..." -ForegroundColor Cyan
    
    $start = Get-Date
    & "$PSScriptRoot\..\fdo_agi_repo\.venv\Scripts\python.exe" `
        "$PSScriptRoot\..\fdo_agi_repo\scripts\run_task.py" `
        --title "smoke_cache_$i" `
        --goal $taskGoal 2>&1 | Out-Null
    $end = Get-Date
    
    $elapsed = ($end - $start).TotalSeconds
    $timings += $elapsed
    
    Write-Host "  Completed in $([math]::Round($elapsed, 2))s" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan
Write-Host "Run 1 (cold): $([math]::Round($timings[0], 2))s" -ForegroundColor Yellow
Write-Host "Run 2 (warm): $([math]::Round($timings[1], 2))s" -ForegroundColor Yellow
Write-Host "Run 3 (warm): $([math]::Round($timings[2], 2))s" -ForegroundColor Yellow

$baseline = $timings[0]
$cached_avg = ($timings[1] + $timings[2]) / 2
$improvement = (($baseline - $cached_avg) / $baseline) * 100

Write-Host ""
if ($improvement -gt 20) {
    Write-Host "✅ PASS: Cache improved by $([math]::Round($improvement, 1))%" -ForegroundColor Green
    exit 0
}
elseif ($improvement -gt 5) {
    Write-Host "⚠️ MARGINAL: Cache improved by $([math]::Round($improvement, 1))% (expected >20%)" -ForegroundColor Yellow
    exit 0
}
else {
    Write-Host "❌ FAIL: Cache only improved by $([math]::Round($improvement, 1))% (expected >20%)" -ForegroundColor Red
    Write-Host "   (May be false negative if LLM already fast)" -ForegroundColor Gray
    exit 1
}
