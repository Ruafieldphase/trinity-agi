
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
$ErrorActionPreference = 'SilentlyContinue'
$patterns = @(
    '*$WorkspaceRoot\scripts\core_dashboard.ps1*',
    '*extension_api.py*watch-status*',
    '*ion-mentoring*start_monitor_loop*.ps1*',
    '*scripts\start_luon_watch.ps1*',
    '*local_llm_proxy.py*',
    '*$WorkspaceRoot\scripts\start_local_llm_proxy.ps1*'
)

$all = @()
foreach ($pat in $patterns) {
    $ps = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -like $pat) }
    $all += $ps
}

if ($all) {
    $all | Select-Object ProcessId, Name, CommandLine | Sort-Object ProcessId | Format-Table -AutoSize
}
else {
    Write-Host 'No matching workspace-related background processes found.'
}