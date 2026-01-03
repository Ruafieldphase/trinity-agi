# Quick Performance Dashboard - Needs Attention Only
# Shows only systems requiring attention with band-filtered top attention list

param(
    [switch]$Open
)

$ErrorActionPreference = "Stop"

$cmd = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
    "$PSScriptRoot\generate_performance_dashboard.ps1",
    '-OnlyBands', 'Needs',
    '-AttentionRespectsBands',
    '-WriteLatest', '-ExportJson', '-ExportCsv'
)
if ($Open) { $cmd += '-OpenDashboard' }

& powershell @cmd