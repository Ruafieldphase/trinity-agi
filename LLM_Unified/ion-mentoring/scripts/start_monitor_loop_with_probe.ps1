param(
    [int]$IntervalSeconds = 1800,
    [int]$DurationMinutes = 1440,
    [switch]$KillExisting
)

$ErrorActionPreference = 'Stop'

$base = Join-Path $PSScriptRoot 'start_monitor_loop.ps1'
if (-not (Test-Path $base)) { Write-Error "start_monitor_loop.ps1 not found: $base"; exit 1 }

$argsList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $base,
    '-IntervalSeconds', "$IntervalSeconds",
    '-DurationMinutes', "$DurationMinutes",
    '-IncludeRateLimitProbe')
if ($KillExisting) { $argsList += '-KillExisting' }

Start-Process -FilePath 'powershell.exe' -ArgumentList $argsList -WindowStyle Hidden | Out-Null
Write-Host "[monitor-loop-probe] Started monitor loop with rate-limit probe (detached)." -ForegroundColor Green
exit 0
