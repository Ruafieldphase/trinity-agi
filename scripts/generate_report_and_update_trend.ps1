param(
    [int]$Hours = 24,
    [switch]$OpenJson
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Err($msg) { Write-Host $msg -ForegroundColor Red }

try {
    $ws = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
    $gen = Join-Path $ws 'scripts/generate_monitoring_report.ps1'
    $trend = Join-Path $ws 'scripts/update_replan_trend.ps1'
    $metrics = Join-Path $ws 'outputs/monitoring_metrics_latest.json'

    if (-not (Test-Path -LiteralPath $gen)) { Write-Err "Missing: $gen"; exit 1 }
    if (-not (Test-Path -LiteralPath $trend)) { Write-Err "Missing: $trend"; exit 1 }

    Write-Info "[1/2] Generating monitoring report ($Hours h)"
    & $gen -Hours $Hours
    if ($LASTEXITCODE -ne 0) { Write-Err "generate_monitoring_report.ps1 failed ($LASTEXITCODE)"; exit $LASTEXITCODE }

    Write-Info "[2/2] Updating ReplanRate trend"
    & $trend
    if ($LASTEXITCODE -ne 0) { Write-Err "update_replan_trend.ps1 failed ($LASTEXITCODE)"; exit $LASTEXITCODE }

    if ($OpenJson -and (Test-Path -LiteralPath $metrics)) {
        Write-Info "Opening latest metrics JSON"
        code $metrics
    }
}
catch {
    Write-Err $_.Exception.Message
    exit 1
}