# Test LM Studio proxy latency after optimization
$times = @()
Write-Host "Testing LM Studio proxy latency (5 requests)..." -ForegroundColor Cyan

for ($i = 1; $i -le 5; $i++) {
    $elapsed = (Measure-Command { 
            Invoke-RestMethod -Uri 'http://localhost:8080/v1/models' -Method GET | Out-Null 
        }).TotalMilliseconds
    $times += $elapsed
    $elapsedStr = $elapsed.ToString('0.00')
    Write-Host "  Request ${i}: $elapsedStr ms"
}

$avg = ($times | Measure-Object -Average).Average
$min = ($times | Measure-Object -Minimum).Minimum
$max = ($times | Measure-Object -Maximum).Maximum

Write-Host "`nResults:" -ForegroundColor Green
Write-Host "  Average: $($avg.ToString('0.00')) ms"
Write-Host "  Min: $($min.ToString('0.00')) ms"
Write-Host "  Max: $($max.ToString('0.00')) ms"