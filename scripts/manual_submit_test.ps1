param(
    [string]$ApiBase = 'http://127.0.0.1:8091/api'
)

Write-Host "[manual_submit_test] API: $ApiBase" -ForegroundColor Cyan

function Show-Json($obj) {
    if ($null -eq $obj) { return }
    $obj | ConvertTo-Json -Depth 10
}

try {
    $health = Invoke-RestMethod -Method Get -Uri ("$ApiBase/health") -ErrorAction Stop
    Write-Host "[manual_submit_test] Health:" -ForegroundColor Yellow
    Show-Json $health
}
catch {
    Write-Host "[manual_submit_test] [ERROR] Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $task = Invoke-RestMethod -Method Get -Uri ("$ApiBase/tasks/next") -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        Write-Host "[manual_submit_test] ℹ️ No task available to dequeue." -ForegroundColor Yellow
        exit 0
    }
    Write-Host "[manual_submit_test] 📥 Dequeued task:" -ForegroundColor Yellow
    Show-Json $task

    $payload = @{ success = $true; data = @{ message = 'manual submit'; handled_by = 'manual_submit_test.ps1' } } | ConvertTo-Json -Compress
    $submit = Invoke-RestMethod -Method Post -Uri ("$ApiBase/tasks/$($task.task_id)/result") -ContentType 'application/json' -Body $payload -ErrorAction Stop
    Write-Host "[manual_submit_test] 📤 Submit result response:" -ForegroundColor Yellow
    Show-Json $submit

    $result = Invoke-RestMethod -Method Get -Uri ("$ApiBase/results/$($task.task_id)") -ErrorAction Stop
    Write-Host "[manual_submit_test] [OK] Retrieved stored result:" -ForegroundColor Green
    Show-Json $result
}
catch {
    Write-Host "[manual_submit_test] [ERROR] Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}