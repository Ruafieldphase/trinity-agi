#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Check status of Cache Validation Monitor (ASCII-only output)
.DESCRIPTION
    Prints whether the daemon is running, shows PID if present, and tails the last 20 lines of the log.
    Uses UTF-8 console bootstrap and avoids any emoji/unicode in output.
#>

# UTF-8 console bootstrap

. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
}
catch {}

$ErrorActionPreference = 'Continue'
$RepoRoot = "$WorkspaceRoot"
$LogFile = Join-Path $RepoRoot 'outputs/cache_validation_monitor.log'

Write-Host '>> Checking cache validator monitor status...' -ForegroundColor Cyan

$monitor = @()
try {
    $monitor = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -in @('powershell.exe', 'pwsh.exe') -and
        $_.CommandLine -match 'cache_validation_monitor_daemon\.ps1'
    })
}
catch {}

if ($monitor.Count -gt 0) {
    $pids = ($monitor | Select-Object -ExpandProperty ProcessId) -join ', '
    Write-Host ("** Monitor running (PID: {0})" -f $pids) -ForegroundColor Green
}
else {
    Write-Host '-- Monitor not running' -ForegroundColor Yellow
}

if (Test-Path $LogFile) {
    Write-Host ("\n>> Last 20 log lines from: {0}" -f $LogFile) -ForegroundColor Gray
    try {
        Get-Content -Path $LogFile -Tail 20
    }
    catch {
        Write-Host ("-- Failed to read log: {0}" -f $_) -ForegroundColor Red
    }
}
else {
    Write-Host ('-- Log file not found: ' + $LogFile) -ForegroundColor Yellow
}