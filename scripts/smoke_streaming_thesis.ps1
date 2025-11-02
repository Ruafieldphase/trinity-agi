#!/usr/bin/env pwsh
# Phase 2.6 Streaming Thesis 검증 스크립트

param(
    [string]$Mode = "streaming"  # "streaming" or "baseline"
)

$ErrorActionPreference = "Stop"
Write-Host "🎵 Phase 2.6: Streaming Thesis 검증" -ForegroundColor Cyan
Write-Host "   Mode: $Mode" -ForegroundColor Yellow
Write-Host ""

# 환경변수 설정
if ($Mode -eq "baseline") {
    $env:THESIS_STREAMING = "false"
}
else {
    $env:THESIS_STREAMING = "true"
}

# Thesis 실행
$venvPython = "c:\workspace\agi\fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "python"
}

Write-Host "🔍 Thesis 실행..." -ForegroundColor Green

& $venvPython -c @"
import sys
sys.path.insert(0, 'c:/workspace/agi/fdo_agi_repo')
from orchestrator.contracts import TaskSpec
from personas.thesis import run_thesis

task = TaskSpec(
    task_id='smoke-streaming-thesis',
    title='Streaming Thesis 검증',
    goal='AGI 자기교정 루프 실증 3문장 작성',
    context='Phase 2.6 Streaming Thesis 검증'
)

result = run_thesis(task, {}, None, '')
print('✅ Thesis 완료')
print(f'Summary: {len(result.summary)} chars')
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Thesis 실행 실패" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📊 Ledger 분석..." -ForegroundColor Green

$ledgerLines = Get-Content "c:\workspace\agi\fdo_agi_repo\memory\resonance_ledger.jsonl" -Tail 1

if ($ledgerLines) {
    $entry = $ledgerLines | ConvertFrom-Json
    
    Write-Host "   Event: $($entry.event)" -ForegroundColor Cyan
    Write-Host "   Persona: $($entry.persona)" -ForegroundColor Cyan
    Write-Host "   Duration: $($entry.duration_sec)s" -ForegroundColor Yellow
    
    if ($entry.PSObject.Properties.Name -contains "ttft_sec") {
        Write-Host "   TTFT: $($entry.ttft_sec)s" -ForegroundColor Green
        Write-Host "   Perceived Improvement: $($entry.perceived_improvement_pct)%" -ForegroundColor Green
    }
    else {
        Write-Host "   TTFT: N/A (non-streaming)" -ForegroundColor Gray
    }
    
    Write-Host "   Streaming: $($entry.streaming)" -ForegroundColor Cyan
    Write-Host "   OK: $($entry.ok)" -ForegroundColor $(if ($entry.ok) { "Green" } else { "Red" })
}

Write-Host ""
Write-Host "✅ Smoke Test 완료!" -ForegroundColor Green
