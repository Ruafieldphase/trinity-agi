param(
    [switch]$Open
)

$ErrorActionPreference = "Stop"

$cmd = @(
    '-NoProfile','-ExecutionPolicy','Bypass','-File',
    "$PSScriptRoot\generate_performance_dashboard.ps1",
    '-Profile','ops-focus',
    '-WriteLatest','-ExportJson','-ExportCsv','-AllowEmpty'
)
if ($Open) { $cmd += '-OpenDashboard' }

& powershell @cmd
