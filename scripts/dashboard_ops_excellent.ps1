# Quick Performance Dashboard - Excellence Showcase
# Shows only Excellent systems for celebrating wins

param(
    [switch]$Open
)

$ErrorActionPreference = "Stop"

$cmd = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
    "$PSScriptRoot\generate_performance_dashboard.ps1",
    '-Profile', 'ops-excellent',
    '-WriteLatest', '-ExportJson', '-ExportCsv'
)
if ($Open) { $cmd += '-OpenDashboard' }

& powershell @cmd