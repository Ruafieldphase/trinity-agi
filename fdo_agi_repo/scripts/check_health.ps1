param(
    [double]$MinAvgConfidence = 0.60,
    [double]$MinAvgQuality = 0.65,
    [double]$MaxSecondPassPerTask = 2.0,
    [double]$MinCompletionRate = 0.90,
    [switch]$JsonOnly,
    [switch]$Fast,
    [double]$MaxDuration = 15.0,
    [double]$HardTimeoutSec = 0.0
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

# Build passthrough args for python script
$argsList = @()
if ($JsonOnly.IsPresent) { $argsList += '--json-only' }
if ($Fast.IsPresent) { $argsList += '--fast' }
if ($MaxDuration -gt 0) { $argsList += @('--max-duration', ([string]::Format('{0:0.##}', $MaxDuration))) }
if ($HardTimeoutSec -gt 0) { $argsList += @('--hard-timeout', ([string]::Format('{0:0}', [math]::Round($HardTimeoutSec)))) }

& $py (Join-Path $PSScriptRoot 'check_health.py') @argsList
exit $LASTEXITCODE
