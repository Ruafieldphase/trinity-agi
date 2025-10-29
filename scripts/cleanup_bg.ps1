param(
    [switch]$StopProxy
)

$ErrorActionPreference = 'SilentlyContinue'

Write-Host '=== Cleanup: stopping workspace-related watchers ==='
$patterns = @(
    '*C:\workspace\agi\scripts\lumen_dashboard.ps1*',
    '*extension_api.py*watch-status*',
    '*ion-mentoring*start_monitor_loop*.ps1*',
    '*scripts\start_luon_watch.ps1*'
)

$killed = @()
foreach ($pat in $patterns) {
    $ps = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -like $pat) }
    foreach ($p in $ps) {
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
            $killed += $p
            Write-Host ("Killed PID {0} ({1}) : {2}" -f $p.ProcessId, $p.Name, $pat)
        }
        catch {}
    }
}

if ($StopProxy) {
    Write-Host '=== Cleanup: stopping local LLM proxy ==='
    $ps1 = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ( $_.CommandLine -like '*local_llm_proxy.py*' -or $_.CommandLine -like '*D:\\nas_backup\\scripts\\start_local_llm_proxy.ps1*' ) }
    foreach ($p in $ps1) {
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
            $killed += $p
            Write-Host ("Killed PID {0} ({1}) : local_llm_proxy" -f $p.ProcessId, $p.Name)
        }
        catch {}
    }
}

$ids = $killed | Select-Object -ExpandProperty ProcessId -Unique | Sort-Object
if ($ids) {
    Write-Host ("Summary: Killed PIDs = " + ($ids -join ', '))
}
else {
    Write-Host 'Summary: Nothing to kill.'
}
