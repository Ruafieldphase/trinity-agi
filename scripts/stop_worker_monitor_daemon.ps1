$ErrorActionPreference = 'Stop'
try {
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*worker_monitor_daemon.ps1*' }
    if (-not $procs) { Write-Host 'No daemon process found.' -ForegroundColor Yellow; exit 0 }
    $pids = $procs | Select-Object -ExpandProperty ProcessId
    $pids | ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } catch {} }
    Write-Host ("Daemon stopped: {0}" -f ($pids -join ',')) -ForegroundColor Green
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
