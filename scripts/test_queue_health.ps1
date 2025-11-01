param()
$ErrorActionPreference = 'Stop'
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8091/api/health' -TimeoutSec 3 -UseBasicParsing
    Write-Host "StatusCode: $($r.StatusCode)" -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
