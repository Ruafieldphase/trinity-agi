param(
    [int]$Port = 8090
)

$ErrorActionPreference = 'Stop'

try {
    $portMatches = netstat -ano | Select-String -Pattern (":$Port")
    if ($portMatches) {
        Write-Host "PORT CHECK: :$Port seems active" -ForegroundColor Green
        $portMatches | ForEach-Object { $_.Line } | Select-Object -First 10 | Write-Output
        exit 0
    }
    else {
        Write-Host "PORT CHECK: :$Port not listening" -ForegroundColor Yellow
        exit 2
    }
}
catch {
    Write-Host "PORT CHECK: ERROR" -ForegroundColor Red
    Write-Error $_
    exit 1
}