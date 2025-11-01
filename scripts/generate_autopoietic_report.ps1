param(
    [ValidateSet('24h','7d','30d')]
    [string]$Window = '24h',
    [int]$Hours = 0,
    [switch]$OpenMd,
    [switch]$WriteLatest
)

$ErrorActionPreference = 'Stop'

# Paths
$workspace = Split-Path -Parent $PSScriptRoot
$venvPy = Join-Path $workspace 'LLM_Unified/.venv/Scripts/python.exe'
$scriptPy = Join-Path $workspace 'fdo_agi_repo/analysis/analyze_autopoietic_loop.py'
$outDir = Join-Path $workspace 'outputs'
$outMdLatest = Join-Path $outDir 'autopoietic_loop_report_latest.md'
$outJsonLatest = Join-Path $outDir 'autopoietic_loop_report_latest.json'

# Resolve window -> hours if Hours not explicitly set
if ($Hours -le 0) {
    switch ($Window) {
        '24h' { $Hours = 24 }
        '7d'  { $Hours = 24 * 7 }
        '30d' { $Hours = 24 * 30 }
        default { $Hours = 24 }
    }
}

# Period-specific output filenames
$suffix = switch ($Window) {
    '24h' { '24h' }
    '7d'  { '7d' }
    '30d' { '30d' }
    default { '24h' }
}
$outMd = Join-Path $outDir ("autopoietic_loop_report_" + $suffix + ".md")
$outJson = Join-Path $outDir ("autopoietic_loop_report_" + $suffix + ".json")

# Ensure outputs dir exists
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
& $python $scriptPy --hours $Hours --out-md $outMd --out-json $outJson
$code = $LASTEXITCODE
if ($code -ne 0) { Write-Error "Analysis failed with exit code $code"; exit $code }

# Optionally update latest aliases
if ($WriteLatest) {
    try {
        Copy-Item -Force -Path $outMd -Destination $outMdLatest
        Copy-Item -Force -Path $outJson -Destination $outJsonLatest
        Write-Host "Updated latest aliases: $outMdLatest, $outJsonLatest" -ForegroundColor DarkCyan
    } catch {
        Write-Warning "Could not update latest aliases: $($_.Exception.Message)"
    }
}

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
