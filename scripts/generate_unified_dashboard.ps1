# Add Performance Metrics to Unified Dashboard
# Reads performance benchmark log and integrates into status dashboard

param(
    [string]$BenchmarkLog = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\performance_benchmark_log.jsonl",
    [string]$OutJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\unified_dashboard_latest.json"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Stop"

Write-Host "📊 Building Unified Dashboard with Performance Metrics..." -ForegroundColor Cyan

# Initialize dashboard data
$dashboard = @{
    generated_at    = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    system_status   = @{}
    performance     = @{}
    recent_activity = @{}
}

# 1. Read latest performance benchmark
if (Test-Path $BenchmarkLog) {
    try {
        $latestBench = Get-Content $BenchmarkLog -Tail 1 | ConvertFrom-Json
        $dashboard.performance = @{
            timestamp      = $latestBench.timestamp
            Core          = @{
                available      = $latestBench.Core.available
                avg_latency_ms = $latestBench.Core.avg_ms
                success_rate   = $latestBench.Core.success_rate
            }
            lm_studio      = @{
                available      = $latestBench.lm_studio.available
                avg_latency_ms = $latestBench.lm_studio.avg_ms
                tokens_per_sec = $latestBench.lm_studio.tokens_per_sec
                success_rate   = $latestBench.lm_studio.success_rate
            }
            recommendation = if ($latestBench.Core.available -and $latestBench.lm_studio.available) {
                if ($latestBench.Core.avg_ms -lt $latestBench.lm_studio.avg_ms) {
                    "Use Core (faster by $([math]::Round($latestBench.lm_studio.avg_ms - $latestBench.Core.avg_ms, 2))ms)"
                }
                else {
                    "Use LM Studio (faster by $([math]::Round($latestBench.Core.avg_ms - $latestBench.lm_studio.avg_ms, 2))ms)"
                }
            }
            elseif ($latestBench.Core.available) {
                "Core only"
            }
            elseif ($latestBench.lm_studio.available) {
                "LM Studio only"
            }
            else {
                "No backend available"
            }
        }
        Write-Host "  ✓ Performance data loaded" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ Could not load performance data: $_" -ForegroundColor Yellow
    }
}

# 1b. Load routing policy if present
$policyPath = "$WorkspaceRoot\outputs\routing_policy.json"
if (Test-Path $policyPath) {
    try {
        $policy = Get-Content $policyPath | ConvertFrom-Json
        $dashboard.system_status.routing_policy = @{
            primary_backend      = $policy.primary_backend
            fallback_backend     = $policy.fallback_backend
            latency_threshold_ms = $policy.latency_threshold_ms
            auto_adjust          = $policy.auto_adjust
            last_updated         = $policy.last_updated
        }
        Write-Host "  ✓ Routing policy loaded" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ Could not load routing policy: $_" -ForegroundColor Yellow
    }
}

# 2. Check queue server status
try {
    $queueStats = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/stats" -TimeoutSec 3
    $dashboard.system_status.queue = @{
        online          = $true
        workers         = $queueStats.workers
        pending_tasks   = $queueStats.pending
        inflight_tasks  = $queueStats.inflight
        completed_tasks = $queueStats.completed
        success_rate    = $queueStats.success_rate
    }
    Write-Host "  ✓ Queue status loaded" -ForegroundColor Green
}
catch {
    $dashboard.system_status.queue = @{ online = $false; error = $_.Exception.Message }
    Write-Host "  ✗ Queue offline" -ForegroundColor Yellow
}

# 3. Check scheduled tasks
try {
    $tasks = Get-ScheduledTask -TaskName "*AGI*", "*Monitoring*" -ErrorAction SilentlyContinue
    $dashboard.system_status.scheduled_tasks = @{
        total    = $tasks.Count
        ready    = ($tasks | Where-Object { $_.State -eq 'Ready' }).Count
        running  = ($tasks | Where-Object { $_.State -eq 'Running' }).Count
        disabled = ($tasks | Where-Object { $_.State -eq 'Disabled' }).Count
    }
    Write-Host "  ✓ Scheduled tasks loaded" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Could not load scheduled tasks" -ForegroundColor Yellow
}

# 4. Check recent ledger activity (AGI)
$ledgerPath = "$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl"
if (Test-Path $ledgerPath) {
    try {
        $recentEntries = Get-Content $ledgerPath -Tail 100 | Where-Object { $_ -ne '' }
        $dashboard.recent_activity.ledger_entries_24h = $recentEntries.Count
        
        if ($recentEntries.Count -gt 0) {
            $lastEntry = $recentEntries[-1] | ConvertFrom-Json
            $dashboard.recent_activity.last_ledger_update = $lastEntry.timestamp
        }
        Write-Host "  ✓ Ledger activity loaded" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ Could not load ledger data" -ForegroundColor Yellow
    }
}

# 5. Check autopoietic loop health
$autoReportPath = "$WorkspaceRoot\outputs\autopoietic_loop_report_24h.md"
if (Test-Path $autoReportPath) {
    $dashboard.recent_activity.autopoietic_report_age_hours = [math]::Round(((Get-Date) - (Get-Item $autoReportPath).LastWriteTime).TotalHours, 1)
    Write-Host "  ✓ Autopoietic report checked" -ForegroundColor Green
}

# 6. System health summary
$healthScore = 0
$maxScore = 5

if ($dashboard.performance.Core.available -or $dashboard.performance.lm_studio.available) { $healthScore++ }
if ($dashboard.system_status.queue.online) { $healthScore++ }
if ($dashboard.system_status.scheduled_tasks.ready -gt 0) { $healthScore++ }
if ($dashboard.recent_activity.ledger_entries_24h -gt 0) { $healthScore++ }
if ($dashboard.recent_activity.autopoietic_report_age_hours -lt 25) { $healthScore++ }

$dashboard.system_status.health_score = [math]::Round(($healthScore / $maxScore) * 100, 0)
$dashboard.system_status.health_status = if ($dashboard.system_status.health_score -ge 80) { "Healthy" } 
elseif ($dashboard.system_status.health_score -ge 60) { "Degraded" } 
else { "Critical" }

# Save dashboard
$outDir = Split-Path -Parent $OutJson
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$dashboard | ConvertTo-Json -Depth 10 | Set-Content -Path $OutJson -Encoding UTF8

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "System Health: $($dashboard.system_status.health_status) ($($dashboard.system_status.health_score)%)" -ForegroundColor $(
    if ($dashboard.system_status.health_score -ge 80) { 'Green' } 
    elseif ($dashboard.system_status.health_score -ge 60) { 'Yellow' } 
    else { 'Red' }
)
Write-Host "=" * 60 -ForegroundColor Cyan

if ($dashboard.performance.recommendation) {
    Write-Host "Performance: $($dashboard.performance.recommendation)" -ForegroundColor Cyan
}

if ($dashboard.system_status.queue.online) {
    Write-Host "Queue: $($dashboard.system_status.queue.workers) workers, $($dashboard.system_status.queue.pending_tasks) pending" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "✓ Dashboard saved to $OutJson" -ForegroundColor Green
Write-Host ""