param(
    [int]$Count = 6,
    [double]$Delay = 1.0,
    [int]$Lines = 50000,
    [switch]$SkipBatch
)

$ErrorActionPreference = 'Stop'

Write-Host "== Policy A/B Refresh ==" -ForegroundColor Cyan
Write-Host " count=$Count delay=$Delay lines=$Lines skipBatch=$SkipBatch" -ForegroundColor Gray

$root = Split-Path -Parent (Resolve-Path ".")

function Invoke-Python {
    param([string[]]$Args)
    $py = if (Test-Path "$root\.venv\Scripts\python.exe") { "$root\.venv\Scripts\python.exe" } else { 'python' }
    & $py @Args
}

if (-not $SkipBatch) {
    Write-Host "[1/2] Running sample batch..." -ForegroundColor Yellow
    Invoke-Python @('scripts/run_sample_batch.py', '--count', $Count, '--delay', $Delay)
}
else {
    Write-Host "[1/2] Skipping sample batch (SkipBatch set)." -ForegroundColor Gray
}

Write-Host "[2/2] Regenerating policy snapshot..." -ForegroundColor Yellow
powershell -ExecutionPolicy Bypass -File scripts/policy_ab_snapshot.ps1 -Lines $Lines | Out-Null

Write-Host "Done. Latest snapshot: outputs\policy_ab_snapshot_latest.md" -ForegroundColor Green
