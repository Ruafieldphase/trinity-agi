# Quick Performance Dashboard - Full Export
# Generates complete dashboard with all systems, exports JSON/CSV

param(
    [switch]$Open
)

$ErrorActionPreference = "Stop"

$cmd = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
    "$PSScriptRoot\generate_performance_dashboard.ps1",
    '-WriteLatest', '-ExportJson', '-ExportCsv', '-AllowEmpty'
)
if ($Open) { $cmd += '-OpenDashboard' }

& powershell @cmd
