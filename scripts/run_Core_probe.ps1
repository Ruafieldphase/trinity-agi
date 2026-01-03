[CmdletBinding()]
param(
    [int]$TimeoutSec = 8,
    [int]$Attempts = 3,
    [int]$BackoffMs = 300,
    [string]$Tag = '',
    [switch]$OpenLatest
)

$ErrorActionPreference = 'Stop'

# Resolve paths
$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$workspace = Split-Path -Parent $scriptDir
$collector = Join-Path $workspace 'scripts/core_probe_collector.ps1'

if (-not (Test-Path $collector)) {
    Write-Error "Collector script not found: $collector"
    exit 1
}

& $collector -TimeoutSec $TimeoutSec -Attempts $Attempts -BackoffMs $BackoffMs -Tag $Tag -WriteLatest
$code = $LASTEXITCODE

if ($OpenLatest) {
    try {
        $latest = Join-Path $workspace 'outputs/core_probe_latest.md'
        if (Test-Path $latest) { Start-Process code $latest }
    } catch { Write-Warning "Could not open latest digest: $($_.Exception.Message)" }
}

exit $code
