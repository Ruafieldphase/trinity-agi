param(
    [int]$Hours = 24
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host $msg -ForegroundColor Red }

try {
    $workspace = Split-Path -Parent $PSScriptRoot
    $html = Join-Path $workspace 'outputs/monitoring_dashboard_latest.html'
    if (Test-Path $html) {
        Write-Info "Opening existing dashboard: $html"
        try { Start-Process $html | Out-Null } catch { Write-Warn "Failed to open dashboard: $_" }
        exit 0
    }

    Write-Info "Dashboard not found. Generating $Hours h report and dashboard..."
    $gen = Join-Path $workspace 'scripts/generate_monitoring_report.ps1'
    if (-not (Test-Path $gen)) {
        Write-Err "Generator script not found: $gen"
        exit 0  # do not fail the task; keep flow
    }

    & powershell -NoProfile -ExecutionPolicy Bypass -File $gen -Hours $Hours
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Warn "Report generation returned code=$code"
    }

    if (Test-Path $html) {
        try { Start-Process $html | Out-Null } catch { Write-Warn "Failed to open dashboard after generation: $_" }
        Write-Ok "Dashboard ready: $html"
        exit 0
    }
    else {
        Write-Warn "Dashboard HTML still not found: $html"
        exit 0
    }
}
catch {
    Write-Warn "Open-or-generate dashboard encountered an issue: $_"
    exit 0
}
