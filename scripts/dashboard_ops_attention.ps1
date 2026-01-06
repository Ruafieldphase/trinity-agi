# Quick Performance Dashboard - Attention Only
# Shows systems requiring attention (Needs + NoData bands)

param(
    [switch]$Open
)

$ErrorActionPreference = "Stop"

$cmd = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
    "$PSScriptRoot\generate_performance_dashboard.ps1",
    '-Profile', 'ops-attention',
    '-WriteLatest', '-ExportJson', '-ExportCsv'
)
if ($Open) { $cmd += '-OpenDashboard' }

& powershell @cmd