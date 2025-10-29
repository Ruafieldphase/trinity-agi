param(
    [double]$MinAvgConfidence = 0.60,
    [double]$MinAvgQuality = 0.65,
    [double]$MaxSecondPassPerTask = 2.0,
    [double]$MinCompletionRate = 0.90
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPy = Join-Path $repoRoot '.venv\Scripts\python.exe'
$py = $venvPy
if (-not (Test-Path $py)) {
    # fallback to system python
    $py = 'python'
}

$env:MIN_AVG_CONFIDENCE = [string]$MinAvgConfidence
$env:MIN_AVG_QUALITY = [string]$MinAvgQuality
$env:MAX_SECOND_PASS_PER_TASK = [string]$MaxSecondPassPerTask
$env:MIN_COMPLETION_RATE = [string]$MinCompletionRate

& $py (Join-Path $PSScriptRoot 'check_health.py')
exit $LASTEXITCODE
