$ErrorActionPreference = 'Stop'
try {
    $jobs = Get-Job -Name 'RPA_Worker_Monitor' -ErrorAction SilentlyContinue
    if (-not $jobs) { Write-Host 'No worker monitor job found.' -ForegroundColor Yellow; exit 0 }
    $jobs | ForEach-Object { try { Stop-Job -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {}; try { Remove-Job -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {} }
    Write-Host 'Worker monitor stopped.' -ForegroundColor Green
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}