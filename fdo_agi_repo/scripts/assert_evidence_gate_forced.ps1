param(
    [double]$LastHours = 24.0,
    [int]$MinAdded = 1,
    [switch]$NoRequireForced,
    [int]$PrintSamples = 3
)

$ErrorActionPreference = 'Stop'

# Resolve repo root (this script lives in fdo_agi_repo/scripts)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$PyScript = Join-Path $ScriptDir 'assert_evidence_gate_forced.py'
$Ledger = Join-Path $RepoRoot 'memory/resonance_ledger.jsonl'

# Choose Python from repo venv if available
$VenvPy = Join-Path $RepoRoot '.venv/Scripts/python.exe'
if (Test-Path $VenvPy) {
    $Python = $VenvPy
}
else {
    $Python = 'python'
}

$ArgsList = @(
    $PyScript,
    '--ledger-path', $Ledger,
    '--last-hours', $LastHours,
    '--min-added', $MinAdded,
    '--print-samples', $PrintSamples
)

if ($NoRequireForced) {
    $ArgsList += '--no-require-forced'
}

# Run
& $Python @ArgsList
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Error "Forced evidence assertion FAILED with exit code $exitCode"
    exit $exitCode
}

Write-Host "Forced evidence assertion PASSED" -ForegroundColor Green
