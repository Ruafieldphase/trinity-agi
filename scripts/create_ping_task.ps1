param(
    [string]$ApiBase = 'http://127.0.0.1:8091/api'
)

Write-Host "[create_ping_task] API: $ApiBase" -ForegroundColor Cyan

try {
    $body = @{ type = 'ping'; data = @{ } } | ConvertTo-Json -Compress
    $resp = Invoke-RestMethod -Method Post -Uri ("$ApiBase/tasks/create") -ContentType 'application/json' -Body $body -ErrorAction Stop
    if ($null -eq $resp) { throw "Empty response from create" }
    if ($resp.task_id) {
        Write-Host "[create_ping_task] [OK] Created task_id: $($resp.task_id)" -ForegroundColor Green
    }
    else {
        Write-Host "[create_ping_task] Response:"; $resp | ConvertTo-Json -Depth 10
    }
    return $resp
}
catch {
    Write-Host "[create_ping_task] [ERROR] Failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}