#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Start Auto-healing Monitor

.DESCRIPTION
    Launches auto_healer.py in background to monitor and heal anomalies.

.PARAMETER IntervalSeconds
    Check interval in seconds (default: 60)

.PARAMETER DryRun
    Run in dry-run mode (no actual actions)

.PARAMETER Once
    Run once and exit

.PARAMETER KillExisting
    Kill existing auto-healer processes before starting

.EXAMPLE
    .\start_auto_healer.ps1 -IntervalSeconds 60
    .\start_auto_healer.ps1 -Once -DryRun
#>

param(
    [int]$IntervalSeconds = 60,
    [switch]$DryRun,
    [switch]$Once,
    [switch]$KillExisting
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$Script = Join-Path $WorkspaceRoot "scripts\auto_healer.py"
$StrategiesFile = Join-Path $WorkspaceRoot "configs\healing_strategies.json"

# ============================================================================
# Find Python
# ============================================================================

$Python = $null
$venvPaths = @(
    (Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"),
    (Join-Path $WorkspaceRoot "LLM_Unified\.venv\Scripts\python.exe"),
    (Join-Path $WorkspaceRoot ".venv\Scripts\python.exe")
)

foreach ($path in $venvPaths) {
    if (Test-Path -LiteralPath $path) {
        $Python = $path
        break
    }
}

if (-not $Python) {
    $Python = "python"
}

Write-Host "🩹 Auto-healing System Launcher" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Kill existing processes
# ============================================================================

if ($KillExisting) {
    Write-Host "🔪 Killing existing auto-healer processes..." -ForegroundColor Yellow
    Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*auto_healer.py*"
    } | ForEach-Object {
        Write-Host "   Killing PID $($_.Id)" -ForegroundColor Red
        Stop-Process -Id $_.Id -Force
    }
    Write-Host ""
}

# ============================================================================
# Check prerequisites
# ============================================================================

if (-not (Test-Path -LiteralPath $Script)) {
    Write-Host "❌ auto_healer.py not found: $Script" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $StrategiesFile)) {
    Write-Host "❌ healing_strategies.json not found: $StrategiesFile" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Build command
# ============================================================================

$cmdArgs = @(
    $Script,
    "--strategies", $StrategiesFile
)

if ($Once) {
    $cmdArgs += "--once"
}
else {
    $cmdArgs += "--interval", $IntervalSeconds
}

if ($DryRun) {
    $cmdArgs += "--dry-run"
}

# ============================================================================
# Launch
# ============================================================================

Write-Host "Starting auto-healer..." -ForegroundColor Green
Write-Host "   Python: $Python" -ForegroundColor Gray
Write-Host "   Script: $Script" -ForegroundColor Gray
Write-Host "   Strategies: $StrategiesFile" -ForegroundColor Gray
Write-Host "   Mode: $(if ($Once) { 'Once' } else { "Continuous ($IntervalSeconds`s)" })" -ForegroundColor Gray
if ($DryRun) {
    Write-Host "   [DRY-RUN MODE]" -ForegroundColor Yellow
}
Write-Host ""

& $Python @cmdArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Auto-healer exited with code: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "✅ Auto-healer completed" -ForegroundColor Green
