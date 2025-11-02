# Quick benchmark log check
$log = "C:\workspace\agi\outputs\performance_benchmark_log.jsonl"

if (Test-Path $log) {
    $count = (Get-Content $log).Count
    Write-Host "Total benchmark records: $count" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Last 3 records:" -ForegroundColor Yellow
    Get-Content $log -Tail 3 | ForEach-Object {
        $entry = $_ | ConvertFrom-Json
        Write-Host "  [$($entry.timestamp)] Lumen: $($entry.lumen.avg_ms)ms, LM Studio: $($entry.lm_studio.avg_ms)ms"
    }
}
else {
    Write-Host "No benchmark log found" -ForegroundColor Yellow
}
