param()
$ErrorActionPreference = 'SilentlyContinue'
$pattern = 'ensure_autonomous_worker_daemon.ps1'
try {
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match [regex]::Escape($pattern) }
    if ($procs) {
        foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
        Write-Host "Watchdog daemon stopped" -ForegroundColor Green
    }
    else {
        Write-Host "No watchdog daemon found" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Failed to stop watchdog: $($_.Exception.Message)" -ForegroundColor Red
}
try {
    $pidFile = Join-Path (Split-Path -Parent $PSScriptRoot) 'fdo_agi_repo\outputs\autonomous_worker_watchdog.pid'
    if (Test-Path $pidFile) { Remove-Item $pidFile -Force -ErrorAction SilentlyContinue }
}
catch {}
