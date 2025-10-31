param(
    [string]$LogFile = (Join-Path (Join-Path $PSScriptRoot '..') 'outputs\worker_monitor.log')
)
$ErrorActionPreference = 'Stop'
try {
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*worker_monitor_daemon.ps1*' }
    if ($procs) {
        $pids = $procs | Select-Object -ExpandProperty ProcessId
        Write-Host ("Daemon process PID(s): {0}" -f ($pids -join ',')) -ForegroundColor Green
    }
    else {
        Write-Host 'Daemon process not running.' -ForegroundColor Yellow
    }
    if (Test-Path -LiteralPath $LogFile) {
        Write-Host ("Log tail: {0}" -f $LogFile) -ForegroundColor Cyan
        Get-Content -LiteralPath $LogFile -Tail 12
    }
    else { Write-Host "No log file yet: $LogFile" -ForegroundColor DarkYellow }
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
