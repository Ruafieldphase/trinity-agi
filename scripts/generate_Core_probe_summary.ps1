param(
    [int]$Hours = 24,
    [switch]$OpenMd
)

$ErrorActionPreference = 'Stop'

# Paths
$workspace = Split-Path -Parent $PSScriptRoot
$venvPy = Join-Path $workspace 'LLM_Unified/.venv/Scripts/python.exe'
$scriptPy = Join-Path $workspace 'scripts/summarize_core_probe.py'

$outDir = Join-Path $workspace 'outputs'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

# Choose python
if (Test-Path $venvPy) { $python = $venvPy } else { $python = 'python' }

Write-Host "Summarizing Core probe log for last $Hours hours..." -ForegroundColor Cyan
$env:PYTHONIOENCODING = 'utf-8'
& $python $scriptPy --hours $Hours
$code = $LASTEXITCODE
if ($code -ne 0) { Write-Error "Summary failed with exit code $code"; exit $code }

if ($OpenMd) {
    try { Start-Process code (Join-Path $workspace 'outputs/core_probe_summary_latest.md') } catch {}
}

Write-Host "Core probe summary generated." -ForegroundColor Green
exit 0
