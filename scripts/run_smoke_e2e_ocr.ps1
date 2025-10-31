param(
    [string]$WorkspaceFolder = (Resolve-Path "$PSScriptRoot\..\").Path
)

$ErrorActionPreference = 'Stop'

# Normalize workspace path
$ws = (Resolve-Path $WorkspaceFolder).Path

# Prepare env and paths
$env:PYTHONPATH = Join-Path $ws 'fdo_agi_repo'
$python = Join-Path $ws '.venv\Scripts\python.exe'
$script = Join-Path $ws 'fdo_agi_repo\scripts\smoke_e2e_ocr.py'

if (-not (Test-Path $python)) {
    Write-Error "Python venv not found: $python"
    exit 1
}
if (-not (Test-Path $script)) {
    Write-Error "Runner script not found: $script"
    exit 1
}

& $python $script
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) { exit $exitCode }
