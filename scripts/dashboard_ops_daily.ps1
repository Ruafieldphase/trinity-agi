param(
    [switch]$Open
)

$ErrorActionPreference = "Stop"

$cmd = @(
    '-NoProfile','-ExecutionPolicy','Bypass','-File',
    "$PSScriptRoot\generate_performance_dashboard.ps1",
    '-Profile','ops-daily',
    '-WriteLatest','-ExportJson','-ExportCsv','-AllowEmpty'
)
if ($Open) { $cmd += '-OpenDashboard' }

& powershell @cmd
