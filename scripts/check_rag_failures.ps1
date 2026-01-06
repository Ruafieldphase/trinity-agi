$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$ledger = Join-Path $ws 'fdo_agi_repo\memory\resonance_ledger.jsonl'

Write-Host "Checking RAG call failures..." -ForegroundColor Cyan

$lines = Get-Content $ledger -Tail 200
$failures = $lines | ForEach-Object { 
    try { $_ | ConvertFrom-Json } catch { $null }
} | Where-Object { $_.event -eq 'rag_call_failed' }

Write-Host "Found $($failures.Count) RAG failures in last 200 events" -ForegroundColor Yellow

$failures | Select-Object -First 5 | ForEach-Object {
    Write-Host "`nFailure at: $($_.timestamp)" -ForegroundColor Red
    Write-Host "  Task: $($_.task_id)"
    Write-Host "  Error: $($_.error)"
    Write-Host "  Query: $($_.query)"
    if ($_.details) {
        Write-Host "  Details: $($_.details | ConvertTo-Json -Compress)"
    }
}

exit 0