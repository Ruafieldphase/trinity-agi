param(
    [int]$Port = 8095
)

$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent $PSScriptRoot
$server = Join-Path $PSScriptRoot 'observer_dashboard_server.py'

if (!(Test-Path -LiteralPath $server)) {
    Write-Error "observer_dashboard_server.py not found: $server"
}

# Prefer repo venvs if available
$py = Join-Path $ws 'LLM_Unified/.venv/Scripts/python.exe'
if (!(Test-Path -LiteralPath $py)) { $py = Join-Path $ws 'fdo_agi_repo/.venv/Scripts/python.exe' }
if (!(Test-Path -LiteralPath $py)) { $py = 'python' }

Write-Host "Starting Observer Dashboard Server on port $Port..." -ForegroundColor Cyan
$cmd = @($server, "$Port")
& $py $cmd