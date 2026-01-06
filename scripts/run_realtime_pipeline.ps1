param(
    [switch]$OpenMd,
    [int]$Hours = 24
)

$ErrorActionPreference = 'Stop'

Write-Host "=== Autopoietic: Real-time Pipeline ===" -ForegroundColor Cyan

$workspace = Split-Path -Parent $PSCommandPath | Split-Path -Parent
$metricsJson = Join-Path $workspace 'outputs/monitoring_metrics_latest.json'
$pipelinePy = Join-Path $workspace 'scripts/realtime_resonance_pipeline.py'
$outJson = Join-Path $workspace 'outputs/realtime_pipeline_status.json'
$outMd = Join-Path $workspace 'outputs/realtime_pipeline_status.md'

if (!(Test-Path $metricsJson)) {
    Write-Host "[Info] metrics JSON not found, generating 24h report..." -ForegroundColor Yellow
    & (Join-Path $workspace 'scripts/generate_monitoring_report.ps1') -Hours 24
    if ($LASTEXITCODE -ne 0) { throw "Failed to generate monitoring report" }
}

function Get-PythonCmd {
    $venvLLM = Join-Path $workspace 'LLM_Unified/.venv/Scripts/python.exe'
    $venvRepo = Join-Path $workspace 'fdo_agi_repo/.venv/Scripts/python.exe'
    if (Test-Path $venvLLM) { return $venvLLM }
    if (Test-Path $venvRepo) { return $venvRepo }
    if (Get-Command py -ErrorAction SilentlyContinue) { return 'py -3' }
    if (Get-Command python -ErrorAction SilentlyContinue) { return 'python' }
    return 'python'
}

$py = Get-PythonCmd
Write-Host "[Info] Python: $py" -ForegroundColor DarkGray

$argsList = @(
    $pipelinePy,
    '--metrics', $metricsJson,
    '--hours', "$Hours",
    '--output-json', $outJson,
    '--output-md', $outMd
)

if ($py -eq 'py -3') {
    # 'py -3' needs separate invocation
    & py -3 @argsList
}
else {
    & $py @argsList
}

if ($LASTEXITCODE -ne 0) { throw "Realtime pipeline failed" }

Write-Host "[OK] Outputs:" -ForegroundColor Green
Write-Host "  - $outJson"
Write-Host "  - $outMd"

if ($OpenMd) {
    try {
        code $outMd | Out-Null
    }
    catch {
        Start-Process $outMd | Out-Null
    }
}