#Requires -Version 5.1
<#
.SYNOPSIS
    Daily health snapshot wrapper - saves timestamped + latest health check results.
.DESCRIPTION
    Runs system_health_check.ps1 and saves JSON/MD to:
    - outputs/system_health_latest.(json|md) for easy reference
    - outputs/health_snapshots/<date>_system_health.(json|md) for history
.EXAMPLE
    .\daily_health_snapshot.ps1
    .\daily_health_snapshot.ps1 -Detailed
#>

param(
    [switch]$Detailed,
    [switch]$OpenMarkdown
)

$ErrorActionPreference = "Continue"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

$root = Split-Path -Parent $PSScriptRoot
$dateStamp = Get-Date -Format "yyyy-MM-dd"

Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "|   Daily Health Snapshot                      |" -ForegroundColor Cyan
Write-Host "===============================================`n" -ForegroundColor Cyan

# Ensure snapshot directory exists
$snapshotDir = Join-Path $root "outputs\health_snapshots"
if (-not (Test-Path $snapshotDir)) {
    New-Item -ItemType Directory -Path $snapshotDir -Force | Out-Null
    Write-Host "Created snapshot directory: $snapshotDir" -ForegroundColor Gray
}

# Define paths
$latestJson = Join-Path $root "outputs\system_health_latest.json"
$latestMd = Join-Path $root "outputs\system_health_latest.md"
$timestampedJson = Join-Path $snapshotDir "${dateStamp}_system_health.json"
$timestampedMd = Join-Path $snapshotDir "${dateStamp}_system_health.md"

# Run health check
$healthScript = Join-Path $PSScriptRoot "system_health_check.ps1"
if (-not (Test-Path $healthScript)) {
    Write-Host "ERROR: system_health_check.ps1 not found." -ForegroundColor Red
    exit 1
}

Write-Host "Running health check..." -ForegroundColor Yellow
$healthArgs = @()
if ($Detailed) { $healthArgs += "-Detailed" }
$healthArgs += "-OutputJson", $latestJson
$healthArgs += "-OutputMarkdown", $latestMd

try {
    & $healthScript @healthArgs
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        Write-Host "`nWarning: Health check exited with code $exitCode" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "`nERROR: Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}

# Copy to timestamped versions
Write-Host "`nSaving timestamped snapshots..." -ForegroundColor Yellow

$saved = 0
if (Test-Path $latestJson) {
    Copy-Item -Path $latestJson -Destination $timestampedJson -Force
    Write-Host "  JSON: $timestampedJson" -ForegroundColor Green
    $saved++
}

if (Test-Path $latestMd) {
    Copy-Item -Path $latestMd -Destination $timestampedMd -Force
    Write-Host "  MD:   $timestampedMd" -ForegroundColor Green
    $saved++
}

if ($saved -eq 0) {
    Write-Host "  Warning: No snapshot files found to save." -ForegroundColor Yellow
}
else {
    Write-Host "`nSnapshot complete. Files saved:" -ForegroundColor Cyan
    Write-Host "  Latest:      outputs\system_health_latest.(json|md)" -ForegroundColor Gray
    Write-Host "  Timestamped: outputs\health_snapshots\${dateStamp}_system_health.(json|md)" -ForegroundColor Gray
}

# Optional: open markdown
if ($OpenMarkdown -and (Test-Path $latestMd)) {
    try {
        code $latestMd
        Write-Host "`nOpened: $latestMd" -ForegroundColor Gray
    }
    catch {
        Write-Host "Warning: Could not open markdown file." -ForegroundColor Yellow
    }
}

Write-Host ""
exit 0
