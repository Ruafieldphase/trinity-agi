param(
    [int]$TailLines = 40
)

$ErrorActionPreference = 'Stop'

$logsDir = Join-Path $PSScriptRoot '..\logs'
if (-not (Test-Path $logsDir)) {
    Write-Output "No log files found (logs directory missing): $logsDir"
    exit 2
}

$latest = Get-ChildItem -Path $logsDir -Filter 'monitor_loop_*.log' -ErrorAction SilentlyContinue |
Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($null -eq $latest) {
    Write-Output 'No log files found'
    exit 3
}

Write-Output ("LatestLog: {0}" -f $latest.FullName)
Get-Content -Tail $TailLines -Path $latest.FullName
exit 0
