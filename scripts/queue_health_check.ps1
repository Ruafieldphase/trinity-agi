param(
    [string]$Server = 'http://127.0.0.1:8091'
)

$ErrorActionPreference = 'Stop'
try {
    $health = Invoke-RestMethod -UseBasicParsing -Uri "$Server/api/health" -TimeoutSec 5
    if (-not $health -or $health.status -ne 'ok') {
        Write-Error "Health check failed or not ok."
        exit 2
    }

    $queueSize = [int]($health.queue_size)
    $resultsCount = [int]($health.results_count)
    $inflightCount = $null
    $queuePreview = $null

    try {
        $inflight = Invoke-RestMethod -UseBasicParsing -Uri "$Server/api/inflight" -TimeoutSec 5
        if ($inflight -and $inflight.count -ne $null) { $inflightCount = [int]$inflight.count }
    }
    catch { $inflightCount = $null }

    try {
        $queue = Invoke-RestMethod -UseBasicParsing -Uri "$Server/api/tasks" -TimeoutSec 5
        if ($queue -and $queue.queue -and $queue.queue.Count -gt 0) {
            $queuePreview = ($queue.queue | Select-Object -First 3 | ForEach-Object { $_.type + ':' + $_.task_id }) -join ', '
        }
    }
    catch { $queuePreview = $null }

    Write-Host "Task Queue Server: OK" -ForegroundColor Green
    $inflightOut = if ($inflightCount -ne $null) { $inflightCount } else { 'n/a' }
    Write-Host ("- queue_size={0} inflight={1} results={2}" -f $queueSize, $inflightOut, $resultsCount)
    if ($queuePreview) { Write-Host ("- queue_preview: {0}" -f $queuePreview) }
    exit 0
}
catch {
    Write-Host "Task Queue Server: ERROR" -ForegroundColor Red
    Write-Error $_.Exception.Message
    exit 1
}