$ErrorActionPreference = 'Continue'

$jobs = Get-Job -Name 'NerveCenter' -ErrorAction SilentlyContinue
if ($jobs) {
    $jobs | ForEach-Object { Stop-Job -Id $_.Id -Force -ErrorAction SilentlyContinue; Remove-Job -Id $_.Id -Force -ErrorAction SilentlyContinue }
    Write-Host "Stopped Nerve Center job(s)." -ForegroundColor Yellow
}

# Fallback: kill python process by command line match
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*autonomic\\nerve_center.py*' } | ForEach-Object {
    try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop; Write-Host "Killed nerve_center.py (PID=$($_.ProcessId))" -ForegroundColor Yellow } catch {}
}
