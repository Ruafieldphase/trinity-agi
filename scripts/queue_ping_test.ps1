param(
    [string]$BaseUrl = 'http://127.0.0.1:8091/api',
    [int]$WaitSeconds = 2
)
$ErrorActionPreference = 'Stop'
Write-Host "Creating ping task..." -ForegroundColor Cyan
$body = @{ type = 'ping'; data = @{} } | ConvertTo-Json -Compress
$resp = Invoke-RestMethod -Method Post -Uri ("$BaseUrl/tasks/create") -ContentType 'application/json' -Body $body
$taskId = $resp.task_id
if (-not $taskId) { throw 'No task_id returned' }
Write-Host ("TaskId: $taskId") -ForegroundColor Yellow
Start-Sleep -Seconds $WaitSeconds
try {
    $result = Invoke-RestMethod -Method Get -Uri ("$BaseUrl/results/$taskId")
}
catch {
    Write-Host 'Result not ready yet, waiting...' -ForegroundColor DarkYellow
    Start-Sleep -Seconds $WaitSeconds
    $result = Invoke-RestMethod -Method Get -Uri ("$BaseUrl/results/$taskId")
}
Write-Host "Result:" -ForegroundColor Green
$result | ConvertTo-Json -Depth 5
