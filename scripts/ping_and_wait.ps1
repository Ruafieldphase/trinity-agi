param(
    [string]$ApiBase = 'http://127.0.0.1:8091/api',
    [int]$TimeoutSeconds = 20,
    [int]$PollIntervalMs = 500
)

Write-Host "[ping_and_wait] API: $ApiBase" -ForegroundColor Cyan

# 1) Create ping task
try {
    $create = & "$PSScriptRoot/create_ping_task.ps1" -ApiBase $ApiBase
    if ($null -eq $create -or -not $create.task_id) { throw "Task not created" }
    $taskId = $create.task_id
    Write-Host "[ping_and_wait] Created task: $taskId" -ForegroundColor Yellow
}
catch {
    Write-Host "[ping_and_wait] ❌ Create failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2) Poll for result
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
    try {
        $res = Invoke-RestMethod -Method Get -Uri ("$ApiBase/results/$taskId") -ErrorAction Stop
        if ($res) {
            Write-Host "[ping_and_wait] ✅ Result found:" -ForegroundColor Green
            $res | ConvertTo-Json -Depth 10
            exit 0
        }
    }
    catch {
        # Expect 404 until available; ignore and retry
        Start-Sleep -Milliseconds $PollIntervalMs
    }
}

Write-Host "[ping_and_wait] ❌ Timed out waiting for result (task_id: $taskId)" -ForegroundColor Red
exit 2
