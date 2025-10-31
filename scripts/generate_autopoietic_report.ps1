param(
    [int]$Hours = 24,
    [switch]$OpenMd
)

$ErrorActionPreference = 'Stop'

# Paths
$workspace = Split-Path -Parent $PSScriptRoot
$venvPy = Join-Path $workspace 'LLM_Unified/.venv/Scripts/python.exe'
$scriptPy = Join-Path $workspace 'fdo_agi_repo/analysis/analyze_autopoietic_loop.py'
$outMd = Join-Path $workspace 'outputs/autopoietic_loop_report_latest.md'

# Ensure outputs dir exists
$outDir = Split-Path $outMd -Parent
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

# Choose python
if (Test-Path $venvPy) {
    $python = $venvPy
}
else {
    $python = 'python'
}

# Run analysis
Write-Host "Running Autopoietic Loop analysis for last $Hours hours..." -ForegroundColor Cyan
$env:PYTHONIOENCODING = 'utf-8'
& $python $scriptPy --hours $Hours
$code = $LASTEXITCODE
if ($code -ne 0) { Write-Error "Analysis failed with exit code $code"; exit $code }

# Optionally open MD in VS Code
if ($OpenMd) {
    try {
        code $outMd
    }
    catch {
        Write-Warning "Could not open $outMd in VS Code automatically."
    }
}

Write-Host "Autopoietic Loop report generated: $outMd" -ForegroundColor Green
exit 0
