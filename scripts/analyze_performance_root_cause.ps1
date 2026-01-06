# Performance Root Cause Analysis
# Schema 통합만으로는 해결되지 않는 근본 원인 분석

param(
    [int]$TaskCount = 3,
    [switch]$Verbose
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = 'Continue'

Write-Host "`n=== Performance Root Cause Analysis ===" -ForegroundColor Cyan

# Measure current performance
Write-Host "`n[1/5] Measuring current task execution performance..." -ForegroundColor Yellow

$tasks = @()
for ($i = 1; $i -le $TaskCount; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    
    $result = & {
        cd $WorkspaceRoot\fdo_agi_repo
        if (Test-Path .venv\Scripts\python.exe) {
            .venv\Scripts\python.exe -m scripts.run_task --title "perf_test_$i" --goal "quick test" 2>&1
        }
        else {
            python -m scripts.run_task --title "perf_test_$i" --goal "quick test" 2>&1
        }
    }
    
    $sw.Stop()
    
    $tasks += [PSCustomObject]@{
        TaskNum  = $i
        Duration = $sw.Elapsed.TotalSeconds
        Success  = $LASTEXITCODE -eq 0
    }
    
    $durationStr = $sw.Elapsed.TotalSeconds.ToString('F2')
    $statusIcon = if ($LASTEXITCODE -eq 0) { '✅' }else { '❌' }
    Write-Host "  Task ${i}: ${durationStr}s $statusIcon"
}

$avgDuration = ($tasks | Measure-Object -Property Duration -Average).Average
Write-Host "`n  Average duration: $($avgDuration.ToString('F2'))s"

# Check for blocking operations
Write-Host "`n[2/5] Analyzing blocking operations..." -ForegroundColor Yellow

$ledger = "$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl"
if (Test-Path $ledger) {
    $ledgerSize = (Get-Item $ledger).Length / 1MB
    $lineCount = (Get-Content $ledger -Raw).Split("`n").Count
    
    Write-Host "  Ledger size: $($ledgerSize.ToString('F2')) MB"
    Write-Host "  Line count: $lineCount"
    
    if ($ledgerSize -gt 10) {
        Write-Host "  ⚠️  WARNING: Large ledger file (>10MB)" -ForegroundColor Yellow
        Write-Host "     This can slow down tail_ledger() operations"
    }
    
    if ($lineCount -gt 50000) {
        Write-Host "  ⚠️  WARNING: Many events (>50k lines)" -ForegroundColor Yellow
        Write-Host "     Consider archiving old events"
    }
}

# Check vector store
Write-Host "`n[3/5] Checking vector store size..." -ForegroundColor Yellow

$vectorStore = "$WorkspaceRoot\fdo_agi_repo\memory\rag_vector_store"
if (Test-Path $vectorStore) {
    $vectorSize = (Get-ChildItem $vectorStore -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    $fileCount = (Get-ChildItem $vectorStore -Recurse -File).Count
    
    Write-Host "  Vector store size: $($vectorSize.ToString('F2')) MB"
    Write-Host "  File count: $fileCount"
    
    if ($vectorSize -gt 100) {
        Write-Host "  ⚠️  WARNING: Large vector store (>100MB)" -ForegroundColor Yellow
        Write-Host "     RAG queries may be slow"
    }
}

# Check for slow imports
Write-Host "`n[4/5] Testing import performance..." -ForegroundColor Yellow

$importTest = @"
import time
start = time.time()

# Test critical imports
from orchestrator.pipeline import PLAN
from orchestrator.memory_bus import tail_ledger
from personas.thesis import run_thesis

elapsed = time.time() - start
print(f"Import time: {elapsed:.3f}s")

if elapsed > 2.0:
    print("⚠️  WARNING: Slow imports (>2s)")
elif elapsed > 1.0:
    print("⚠️  Imports slightly slow (>1s)")
else:
    print("✅ Imports OK")
"@

$importResult = & {
    cd $WorkspaceRoot\fdo_agi_repo
    if (Test-Path .venv\Scripts\python.exe) {
        echo $importTest | .venv\Scripts\python.exe
    }
    else {
        echo $importTest | python
    }
}
Write-Host "  $importResult"

# Check for concurrent processes
Write-Host "`n[5/5] Checking for resource competition..." -ForegroundColor Yellow

$pythonProcs = Get-Process -Name "python*" -ErrorAction SilentlyContinue
if ($pythonProcs.Count -gt 3) {
    Write-Host "  ⚠️  Multiple Python processes detected: $($pythonProcs.Count)" -ForegroundColor Yellow
    Write-Host "     May cause resource contention"
    
    if ($Verbose) {
        $pythonProcs | Format-Table Id, ProcessName, CPU, WorkingSet, StartTime
    }
}

# Check GitHub Copilot
$copilotProcs = Get-Process | Where-Object { $_.ProcessName -like "*copilot*" -or $_.ProcessName -like "*node*" }
if ($copilotProcs) {
    $totalMem = ($copilotProcs | Measure-Object -Property WorkingSet -Sum).Sum / 1MB
    Write-Host "  ℹ️  Copilot/Node processes: $($copilotProcs.Count) ($($totalMem.ToString('F0')) MB)"
}

# Summary
Write-Host "`n=== Root Cause Summary ===" -ForegroundColor Cyan

$issues = @()

if ($avgDuration -gt 20) {
    $issues += "Slow task execution (avg $($avgDuration.ToString('F1'))s)"
}

if ($ledgerSize -gt 10 -or $lineCount -gt 50000) {
    $issues += "Large ledger file needs archiving"
}

if ($vectorSize -gt 100) {
    $issues += "Large vector store"
}

if ($pythonProcs.Count -gt 3) {
    $issues += "Multiple Python processes"
}

if ($issues.Count -eq 0) {
    Write-Host "✅ No significant performance issues detected" -ForegroundColor Green
    Write-Host "`nPerformance may be normal or due to external factors:"
    Write-Host "  - Network latency to LLM APIs"
    Write-Host "  - System background tasks"
    Write-Host "  - GitHub Copilot processing load"
}
else {
    Write-Host "⚠️  Potential Issues:" -ForegroundColor Yellow
    $issues | ForEach-Object { Write-Host "  - $_" }
    
    Write-Host "`nRecommended Actions:" -ForegroundColor Cyan
    if ($ledgerSize -gt 10 -or $lineCount -gt 50000) {
        Write-Host "  1. Archive old ledger events:"
        Write-Host "     python scripts/archive_old_ledger.py --keep-days 7"
    }
    if ($vectorSize -gt 100) {
        Write-Host "  2. Rebuild vector store with compression:"
        Write-Host "     python scripts/rebuild_vector_store.py --compress"
    }
    if ($pythonProcs.Count -gt 3) {
        Write-Host "  3. Stop unnecessary Python processes"
    }
}

Write-Host ""
exit 0