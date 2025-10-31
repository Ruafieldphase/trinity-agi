param(
    [string]$Title = "evidence-check",
    [string]$Goal = "Run a minimal task to validate evidence gate __force_evidence__",
    [int]$LastHours = 6,
    [int]$MinAdded = 1,
    [switch]$NoAlert,
    [switch]$SendAlert
)

$ErrorActionPreference = 'Stop'

# Resolve repo root and Python
$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) { $Python = $VenvPython } elseif (Get-Command python -ErrorAction SilentlyContinue) { $Python = "python" } else { Write-Error "Python not found (checked venv and system)"; exit 1 }

# Ensure goal contains the force marker
if ($Goal -notmatch "__force_evidence__") {
    $Goal = "$Goal __force_evidence__"
}

# Preserve and set env var for this session
$prev = $env:EVIDENCE_GATE_FORCE
$env:EVIDENCE_GATE_FORCE = "1"

Write-Host "[Step 1/2] Launching forced AGI task..." -ForegroundColor Cyan
$runTask = Join-Path $RepoRoot "scripts\run_task.py"
if (-not (Test-Path $runTask)) { Write-Error "run_task.py not found at $runTask"; exit 1 }

# Run the task
& $Python $runTask --title $Title --goal $Goal
$taskExit = $LASTEXITCODE
if ($taskExit -ne 0) {
    Write-Warning "run_task.py returned non-zero exit code: $taskExit (continuing to assertion)"
}

# Restore env var
if ($null -ne $prev) { $env:EVIDENCE_GATE_FORCE = $prev } else { Remove-Item Env:\EVIDENCE_GATE_FORCE -ErrorAction SilentlyContinue }

Write-Host "[Step 2/2] Asserting forced evidence events in last $LastHours hour(s)..." -ForegroundColor Cyan
$assertPs1 = Join-Path $RepoRoot "scripts\assert_evidence_gate_forced.ps1"
if (-not (Test-Path $assertPs1)) { Write-Error "assert_evidence_gate_forced.ps1 not found at $assertPs1"; exit 1 }

# Run assertion (require forced=true by default)
& $assertPs1 -LastHours $LastHours -MinAdded $MinAdded
$assertExit = $LASTEXITCODE

if ($assertExit -eq 0) {
    Write-Host "[OK] Forced evidence check PASSED" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "[ERROR] Forced evidence check FAILED (exit=$assertExit)" -ForegroundColor Red
    if ($SendAlert -and -not $NoAlert) {
        try {
            $alertPs1 = Join-Path $RepoRoot "scripts\alert_system.ps1"
            if (Test-Path $alertPs1) {
                Write-Host "Dispatching alert via alert_system.ps1..." -ForegroundColor Yellow
                & $alertPs1
            }
        }
        catch { Write-Warning "Alert dispatch failed: $($_.Exception.Message)" }
    }
    exit $assertExit
}
