#Requires -Version 5.1
<#!
.SYNOPSIS
    Metrics collector daemon status checker

.DESCRIPTION
    Reports whether the background metrics collector daemon is running
    and whether the metrics file is being updated recently.

.PARAMETER MinutesStale
    Threshold in minutes to consider the collector stale based on the
    last write time of outputs/system_metrics.jsonl (default: 10).
#>

param(
    [int]$MinutesStale = 10
)

$ErrorActionPreference = 'SilentlyContinue'

function Write-Status {
    param(
        [string]$Label,
        [string]$Value,
        [ConsoleColor]$Color = [ConsoleColor]::White
    )
    $current = [Console]::ForegroundColor
    [Console]::ForegroundColor = $Color
    Write-Host ("{0,-24} {1}" -f $Label, $Value)
    [Console]::ForegroundColor = $current
}

try {
    $root = Split-Path -Parent $PSScriptRoot
    $metricsPath = Join-Path $root 'outputs/system_metrics.jsonl'

    # Find daemon processes by command line
    $procs = Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -match 'metrics_collector_daemon\.ps1' -or
        $_.CommandLine -match 'collect_system_metrics.*daemon'
    }

    $running = $false
    $pids = @()
    if ($procs) {
        $running = $true
        $pids = $procs | Select-Object -ExpandProperty ProcessId
    }

    Write-Host "== Metrics Collector Status ==" -ForegroundColor Cyan
    $runningLabel = 'NO'
    $runningColor = 'Yellow'
    if ($running) { $runningLabel = 'YES'; $runningColor = 'Green' }
    Write-Status 'Daemon Running:' $runningLabel $runningColor
    if ($pids.Count -gt 0) {
        Write-Status 'PIDs:' ( ($pids -join ', ') ) 'White'
    }

    if (Test-Path $metricsPath) {
        $fi = Get-Item $metricsPath
        $ageMin = [math]::Round(((Get-Date) - $fi.LastWriteTime).TotalMinutes, 2)
        $stale = $ageMin -ge $MinutesStale

        # Count and inspect last entry
        $lineCount = (Get-Content $metricsPath | Measure-Object -Line).Lines
        $lastLine = Get-Content $metricsPath -Tail 1
        $lastTs = $null
        try {
            $lastObj = $lastLine | ConvertFrom-Json
            $lastTs = [DateTime]::Parse($lastObj.timestamp)
        }
        catch {}

        Write-Status 'Metrics File:' $metricsPath 'White'
        $ageColor = if ($stale) { 'Yellow' } else { 'Green' }
        Write-Status 'Last Write:' ("{0} ({1} min ago)" -f $fi.LastWriteTime, $ageMin) $ageColor
        Write-Status 'Samples:' $lineCount 'White'
        if ($lastTs) { Write-Status 'Last Timestamp:' ($lastTs.ToString('yyyy-MM-dd HH:mm:ss')) 'White' }

        if ($stale) {
            Write-Host "Warning: metrics file looks stale. Consider restarting the daemon:" -ForegroundColor Yellow
            Write-Host "  .\\scripts\\start_metrics_collector_daemon.ps1 -KillExisting" -ForegroundColor White
        }
    }
    else {
        Write-Status 'Metrics File:' 'NOT FOUND' 'Yellow'
        Write-Host "Hint: run collector once:" -ForegroundColor Yellow
        Write-Host "  .\\scripts\\collect_system_metrics.ps1" -ForegroundColor White
    }

    exit 0
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
