# Enhanced System Dashboard with GPU Metrics
# Generates comprehensive HTML dashboard including GPU monitoring
# Part of Phase 3+ Real-Time Monitoring Enhancement
#
# QUICK USAGE:
#   generate_enhanced_dashboard.ps1 -OpenBrowser   # generate & open
#   generate_enhanced_dashboard.ps1                # generate only
#
# SECTIONS INDEX:
#   - Parameters (line 1-10)
#   - GPU Metrics Collection (line 20-200)
#   - Queue Status (line 200-400)
#   - LLM Analytics (line 400-600)
#   - Dashboard HTML (line 600+)

param(
    [int]$LookbackHours = 24,
    [string]$OutHtml = "$PSScriptRoot\..\outputs\system_dashboard_enhanced.html",
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"

# Collect current metrics
Write-Host "📊 Collecting system metrics..." -ForegroundColor Cyan

# 1. GPU Metrics
& "$PSScriptRoot\collect_gpu_metrics.ps1" -Quiet
$gpuData = Get-Content "$PSScriptRoot\..\outputs\gpu_usage_latest.json" | ConvertFrom-Json

# 2. Performance Metrics (if exists)
$perfFile = "$PSScriptRoot\..\outputs\performance_metrics_latest.json"
if (Test-Path $perfFile) {
    $perfData = Get-Content $perfFile | ConvertFrom-Json
}
else {
    $perfData = @{ lumen = @{ available = $false }; lmstudio = @{ available = $false } }
}

# 3. Queue Status
try {
    $queueHealth = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/health" -TimeoutSec 2
}
catch {
    $queueHealth = @{ status = "offline" }
}

# 4. Anomaly Detection Data
$anomalyBaseline = @{}
$baselinePath = "$PSScriptRoot\..\outputs\anomaly_baseline.json"
if (Test-Path $baselinePath) {
    try {
        $anomalyBaseline = Get-Content $baselinePath -Raw | ConvertFrom-Json -AsHashtable
    }
    catch {
        Write-Host "⚠️  Could not load anomaly baseline" -ForegroundColor Yellow
    }
}

$recentAnomalies = @()
$anomalyLogPath = "$PSScriptRoot\..\outputs\anomaly_log.jsonl"
if (Test-Path $anomalyLogPath) {
    $cutoff = (Get-Date).AddHours(-$LookbackHours)
    try {
        $recentAnomalies = Get-Content $anomalyLogPath | ForEach-Object {
            $entry = $_ | ConvertFrom-Json
            $ts = [DateTime]::Parse($entry.timestamp)
            if ($ts -ge $cutoff) { $entry }
        } | Select-Object -Last 20
    }
    catch {
        Write-Host "⚠️  Could not load anomaly log" -ForegroundColor Yellow
    }
}

# 5. Healing History Data
$recentHealings = @()
$healingLogPath = "$PSScriptRoot\..\outputs\healing_log.jsonl"
if (Test-Path $healingLogPath) {
    $cutoff = (Get-Date).AddHours(-$LookbackHours)
    try {
        $recentHealings = Get-Content $healingLogPath -TotalCount 200 | ForEach-Object {
            $entry = $_ | ConvertFrom-Json
            $ts = [DateTime]::Parse($entry.timestamp)
            if ($ts -ge $cutoff) { $entry }
        } | Select-Object -Last 20
    }
    catch {
        Write-Host "⚠️  Could not load healing log" -ForegroundColor Yellow
    }
}

$policySnapshot = @()
$policySnapshotPath = "$PSScriptRoot\..\outputs\policy_ab_snapshot_latest.md"
if (Test-Path $policySnapshotPath) {
    try {
        $policySnapshot = Get-Content $policySnapshotPath -TotalCount 40
    } catch {
        $policySnapshot = @("Failed to load policy snapshot: $($_.Exception.Message)")
    }
}
$policyPreviewText = ""
if ($policySnapshot.Count -gt 0) {
    $policyPreviewText = $policySnapshot -join "`n"
    if ($policySnapshot.Count -ge 40) {
        $policyPreviewText += "`n... (see outputs\policy_ab_snapshot_latest.md for full report)"
    }
}

$resourceSummaryPath = "$PSScriptRoot\..\outputs\resource_optimizer_summary.md"
$resourceSummaryText = ""
if (Test-Path $resourceSummaryPath) {
    try {
        $resourceSummaryText = (Get-Content $resourceSummaryPath -TotalCount 20) -join "`n"
    }
    catch {
        $resourceSummaryText = "Failed to load resource optimizer summary: $($_.Exception.Message)"
    }
}

$rpaStatusPath = "$PSScriptRoot\..\outputs\rpa_worker_status.txt"
$rpaStatusLine = ""
if (Test-Path $rpaStatusPath) {
    try {
        $rpaStatusLine = (Get-Content $rpaStatusPath -TotalCount 1) -join "`n"
    }
    catch {
        $rpaStatusLine = "Failed to load RPA worker status: $($_.Exception.Message)"
    }
}

$rpaAlertPath = "$PSScriptRoot\..\outputs\alerts\rpa_worker_alert.json"
$rpaAlertSummary = ""
if (Test-Path $rpaAlertPath) {
    try {
        $alertRaw = Get-Content $rpaAlertPath -Raw
        if (-not [string]::IsNullOrWhiteSpace($alertRaw)) {
            $alertObj = $alertRaw | ConvertFrom-Json -ErrorAction Stop
            $alertMessage = if ($alertObj.message) { $alertObj.message } else { "Restart limit reached." }
            $alertTs = $null
            if ($alertObj.timestamp) { $alertTs = $alertObj.timestamp }
            else {
                try { $alertTs = (Get-Item $rpaAlertPath).LastWriteTime.ToString("o") } catch {}
            }
            $details = @()
            if ($alertTs) { $details += "timestamp=$alertTs" }
            if ($alertObj.recent_restarts -ne $null -and $alertObj.max_restarts -ne $null) {
                $details += "recent_restarts=$($alertObj.recent_restarts)/$($alertObj.max_restarts)"
            }
            if ($alertObj.window_seconds -ne $null) { $details += "window_seconds=$($alertObj.window_seconds)" }
            $detailText = if ($details.Count) { " (" + ($details -join ", ") + ")" } else { "" }
            $rpaAlertSummary = "$alertMessage$detailText"
        }
    }
    catch {
        $rpaAlertSummary = "Failed to read RPA worker alert: $($_.Exception.Message)"
    }
}

$monitoringMetricsPath = "$PSScriptRoot\..\outputs\monitoring_metrics_latest.json"
$policyOptimization = $null
$gatewayOptimizerMetrics = $null
try {
    if (Test-Path $monitoringMetricsPath) {
        $monitoringMetrics = Get-Content $monitoringMetricsPath -Raw | ConvertFrom-Json
        if ($monitoringMetrics -and $monitoringMetrics.AGI -and $monitoringMetrics.AGI.Policy -and $monitoringMetrics.AGI.Policy.optimization) {
            $policyOptimization = $monitoringMetrics.AGI.Policy.optimization
        }
        if ($monitoringMetrics -and $monitoringMetrics.GatewayOptimizer) {
            $gatewayOptimizerMetrics = $monitoringMetrics.GatewayOptimizer
        }
    }
}
catch {
    Write-Host "⚠️  Could not load monitoring metrics: $($_.Exception.Message)" -ForegroundColor Yellow
}

$optTotal = "--"
$optPeak = "--"
$optOffpeak = "--"
$optThrottle = "--"
$optPreferGateway = "--"
$optPrimaryText = "--"
$optLastTime = "--"
$optLastPhase = "--"
$optLastChannels = "--"
$optLastOffpeakMode = "--"
$optLastCompression = "--"
$optLastLearning = "--"
$optLastThrottle = "--"

if ($policyOptimization) {
    if ($policyOptimization.total -ne $null) { $optTotal = $policyOptimization.total }
    if ($policyOptimization.peak -ne $null) { $optPeak = $policyOptimization.peak }
    if ($policyOptimization.offpeak -ne $null) { $optOffpeak = $policyOptimization.offpeak }
    if ($policyOptimization.throttle -ne $null) { $optThrottle = $policyOptimization.throttle }
    if ($policyOptimization.prefer_gateway -ne $null) { $optPreferGateway = $policyOptimization.prefer_gateway }
    if ($policyOptimization.preferred_primary) {
        try {
            $primaryEntries = $policyOptimization.preferred_primary.PSObject.Properties | ForEach-Object { "{0}:{1}" -f $_.Name, $_.Value }
            if ($primaryEntries -and $primaryEntries.Count -gt 0) { $optPrimaryText = $primaryEntries -join ', ' }
        }
        catch {}
    }
    $optLast = $policyOptimization.last
    if ($optLast) {
        if ($optLast.timestamp) { $optLastTime = $optLast.timestamp }
        if ($optLast.is_peak_now -eq $true) { $optLastPhase = "PEAK" }
        elseif ($optLast.is_peak_now -eq $false) { $optLastPhase = "OFF-PEAK" }
        $channels = $optLast.preferred_channels
        if ($channels) {
            if ($channels -is [System.Collections.IEnumerable] -and -not ($channels -is [string])) {
                $optLastChannels = ($channels | ForEach-Object { $_ }) -join ', '
            }
            else {
                $optLastChannels = $channels
            }
        }
        if ($optLast.offpeak_mode) { $optLastOffpeakMode = $optLast.offpeak_mode }
        if ($optLast.batch_compression) { $optLastCompression = $optLast.batch_compression }
        if ($optLast.learning_bias) { $optLastLearning = $optLast.learning_bias }
        if ($optLast.should_throttle -eq $true) { $optLastThrottle = "YES" }
        elseif ($optLast.should_throttle -eq $false) { $optLastThrottle = "NO" }
    }
}

$goptModeText = "--"
$goptTotalEntries = "--"
$goptPeakEntries = "--"
$goptOffpeakEntries = "--"
$goptWarmups = "--"
$goptTarget = "--"
$goptWarning = "--"
$goptCritical = "--"
$goptSigma = "--"
$goptLastTime = "--"
$goptLastPhase = "--"
$goptLastTimeout = "--"
$goptLastConcurrency = "--"
$goptLastWarmup = "--"
$goptLastNext = "--"

if ($gatewayOptimizerMetrics) {
    if ($gatewayOptimizerMetrics.dry_run -eq $true) { $goptModeText = "DRY-RUN" }
    elseif ($gatewayOptimizerMetrics.dry_run -eq $false) { $goptModeText = "ACTIVE" }
    if ($gatewayOptimizerMetrics.total_entries -ne $null) { $goptTotalEntries = $gatewayOptimizerMetrics.total_entries }
    if ($gatewayOptimizerMetrics.peak_entries -ne $null) { $goptPeakEntries = $gatewayOptimizerMetrics.peak_entries }
    if ($gatewayOptimizerMetrics.offpeak_entries -ne $null) { $goptOffpeakEntries = $gatewayOptimizerMetrics.offpeak_entries }
    if ($gatewayOptimizerMetrics.warmup_triggers -ne $null) { $goptWarmups = $gatewayOptimizerMetrics.warmup_triggers }
    if ($gatewayOptimizerMetrics.thresholds) {
        if ($gatewayOptimizerMetrics.thresholds.latency_target_ms -ne $null) { $goptTarget = $gatewayOptimizerMetrics.thresholds.latency_target_ms }
        if ($gatewayOptimizerMetrics.thresholds.latency_warning_ms -ne $null) { $goptWarning = $gatewayOptimizerMetrics.thresholds.latency_warning_ms }
        if ($gatewayOptimizerMetrics.thresholds.latency_critical_ms -ne $null) { $goptCritical = $gatewayOptimizerMetrics.thresholds.latency_critical_ms }
        if ($gatewayOptimizerMetrics.thresholds.stability_target_sigma -ne $null) { $goptSigma = $gatewayOptimizerMetrics.thresholds.stability_target_sigma }
    }
    $goptLast = $gatewayOptimizerMetrics.last
    if ($goptLast) {
        if ($goptLast.timestamp) { $goptLastTime = $goptLast.timestamp }
        if ($goptLast.phase) { $goptLastPhase = ($goptLast.phase).ToUpper() }
        elseif ($goptLast.is_peak_now -eq $true) { $goptLastPhase = "PEAK" }
        elseif ($goptLast.is_peak_now -eq $false) { $goptLastPhase = "OFF-PEAK" }
        if ($goptLast.timeout_ms -ne $null) { $goptLastTimeout = "$($goptLast.timeout_ms) ms" }
        if ($goptLast.concurrency -ne $null) { $goptLastConcurrency = $goptLast.concurrency }
        if ($goptLast.warmup_active -eq $true) { $goptLastWarmup = "ACTIVE" }
        elseif ($goptLast.warmup_active -eq $false) { $goptLastWarmup = "IDLE" }
        if ($goptLast.next_warmup) { $goptLastNext = $goptLast.next_warmup }
        elseif ($goptLast.schedule) { $goptLastNext = $goptLast.schedule }
    }
}

# Generate HTML
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$html = @"
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AGI System Dashboard - Enhanced</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #fff;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            text-align: center;
            padding: 30px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header .timestamp { opacity: 0.8; font-size: 0.9em; }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: rgba(255,255,255,0.15);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .card h2 {
            font-size: 1.5em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card h2 .icon { font-size: 1.2em; }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .metric:last-child { border-bottom: none; }
        .metric-label { opacity: 0.8; font-size: 0.95em; }
        .metric-value {
            font-weight: bold;
            font-size: 1.1em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }
        .status-ok { background: #10b981; color: white; }
        .status-warning { background: #f59e0b; color: white; }
        .status-error { background: #ef4444; color: white; }
        .status-offline { background: #6b7280; color: white; }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 8px;
        }
        .progress-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }
        .progress-green { background: #10b981; }
        .progress-yellow { background: #f59e0b; }
        .progress-red { background: #ef4444; }
        
        .table-container {
            overflow-x: auto;
            margin-top: 15px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th {
            background: rgba(255,255,255,0.1);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }
        tr:hover {
            background: rgba(255,255,255,0.05);
        }
        .anomaly-critical { color: #ef4444; font-weight: bold; }
        .anomaly-warning { color: #f59e0b; font-weight: bold; }
        .anomaly-info { color: #3b82f6; }
        .healing-success { color: #10b981; font-weight: bold; }
        .healing-failed { color: #ef4444; font-weight: bold; }
        
        .footer {
            text-align: center;
            padding: 20px;
            opacity: 0.7;
            font-size: 0.9em;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .live-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
    </style>
    <script>
        // Auto-refresh every 60 seconds
        setTimeout(function(){ location.reload(); }, 60000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AGI System Dashboard</h1>
            <div class="timestamp">
                <span class="live-indicator"></span>
                Last Updated: $timestamp
            </div>
        </div>
        
        <div class="grid">
            <!-- GPU Card -->
            <div class="card">
                <h2><span class="icon">🎮</span> GPU Status</h2>
"@

if ($gpuData.available) {
    $gpuUtilColor = if ($gpuData.gpu_utilization_percent -lt 50) { "green" } elseif ($gpuData.gpu_utilization_percent -lt 80) { "yellow" } else { "red" }
    $memUtilColor = if ($gpuData.memory_utilization_percent -lt 70) { "green" } elseif ($gpuData.memory_utilization_percent -lt 90) { "yellow" } else { "red" }
    $tempColor = if ($gpuData.temperature_celsius -lt 70) { "green" } elseif ($gpuData.temperature_celsius -lt 85) { "yellow" } else { "red" }
    
    $html += @"
                <div class="metric">
                    <span class="metric-label">GPU Model</span>
                    <span class="metric-value">$($gpuData.gpu_name)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Utilization</span>
                    <span class="metric-value">
                        $($gpuData.gpu_utilization_percent)%
                    </span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill progress-$gpuUtilColor" style="width: $($gpuData.gpu_utilization_percent)%"></div>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Memory Usage</span>
                    <span class="metric-value">
                        $($gpuData.memory_used_mb) MB / $($gpuData.memory_total_mb) MB ($($gpuData.memory_utilization_percent)%)
                    </span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill progress-$memUtilColor" style="width: $($gpuData.memory_utilization_percent)%"></div>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Temperature</span>
                    <span class="metric-value">$($gpuData.temperature_celsius)°C</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill progress-$tempColor" style="width: $([math]::Min(100, $gpuData.temperature_celsius))%"></div>
                </div>
                
                <div class="metric">
                    <span class="metric-label">Power Draw</span>
                    <span class="metric-value">
                        $($gpuData.power_draw_watts) W / $($gpuData.power_limit_watts) W ($($gpuData.power_utilization_percent)%)
                    </span>
                </div>
"@
}
else {
    $html += @"
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="metric-value">
                        <span class="status-badge status-offline">Not Available</span>
                    </span>
                </div>
                <div class="metric" style="border-bottom: none;">
                    <span class="metric-label">Reason</span>
                    <span class="metric-value" style="font-size: 0.9em; opacity: 0.8;">$($gpuData.error)</span>
                </div>
"@
}

$html += @"
            </div>
            
            <!-- Task Queue Card -->
            <div class="card">
                <h2><span class="icon">📋</span> Task Queue</h2>
"@

if ($queueHealth.status -eq "ok") {
    $queueStatus = "status-ok"
    $queueLabel = "Online"
}
elseif ($queueHealth.status -eq "offline") {
    $queueStatus = "status-offline"
    $queueLabel = "Offline"
}
else {
    $queueStatus = "status-warning"
    $queueLabel = "Unknown"
}

$html += @"
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="metric-value">
                        <span class="status-badge $queueStatus">$queueLabel</span>
                    </span>
                </div>
"@

if ($queueHealth.status -eq "ok") {
    $totalPending = $queueHealth.queue_urgent + $queueHealth.queue_normal + $queueHealth.queue_low
    $html += @"
                <div class="metric">
                    <span class="metric-label">Urgent Queue</span>
                    <span class="metric-value">$($queueHealth.queue_urgent)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Normal Queue</span>
                    <span class="metric-value">$($queueHealth.queue_normal)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Low Priority Queue</span>
                    <span class="metric-value">$($queueHealth.queue_low)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Pending</span>
                    <span class="metric-value" style="font-size: 1.3em; color: #fbbf24;">$totalPending</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Completed</span>
                    <span class="metric-value">$($queueHealth.completed)</span>
                </div>
"@
}

$html += @"
            </div>
            
            <!-- Resonance Optimization Card -->
            <div class="card">
                <h2><span class="icon">🌀</span> Resonance Optimization</h2>
                <div class="metric">
                    <span class="metric-label">Total / Peak / Off-peak</span>
                    <span class="metric-value">$optTotal / $optPeak / $optOffpeak</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Throttle Activations</span>
                    <span class="metric-value">$optThrottle</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Gateway Preference Count</span>
                    <span class="metric-value">$optPreferGateway</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Primary Channels</span>
                    <span class="metric-value" style="font-size: 0.95em;">$optPrimaryText</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Event Phase</span>
                    <span class="metric-value">$optLastPhase</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Channels</span>
                    <span class="metric-value" style="font-size: 0.9em;">$optLastChannels</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Off-peak Mode / Compression / Learning</span>
                    <span class="metric-value" style="font-size: 0.9em;">$optLastOffpeakMode / $optLastCompression / $optLastLearning</span>
                </div>
                <div class="metric" style="border-bottom: none;">
                    <span class="metric-label">Throttle · Timestamp</span>
                    <span class="metric-value" style="font-size: 0.9em;">$optLastThrottle · $optLastTime</span>
                </div>
            </div>
            
            <!-- Gateway Optimizer Card -->
            <div class="card">
                <h2><span class="icon">🌉</span> Gateway Optimizer</h2>
                <div class="metric">
                    <span class="metric-label">Mode</span>
                    <span class="metric-value">$goptModeText</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Entries (Peak / Off-peak)</span>
                    <span class="metric-value">$goptTotalEntries ($goptPeakEntries / $goptOffpeakEntries)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Warmup Triggers</span>
                    <span class="metric-value">$goptWarmups</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Latency Targets (ms)</span>
                    <span class="metric-value">$goptTarget / $goptWarning / $goptCritical</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Stability σ Target</span>
                    <span class="metric-value">$goptSigma</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Run Phase</span>
                    <span class="metric-value">$goptLastPhase</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Timeout / Concurrency</span>
                    <span class="metric-value">$goptLastTimeout / $goptLastConcurrency</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Warmup State</span>
                    <span class="metric-value">$goptLastWarmup (next: $goptLastNext)</span>
                </div>
                <div class="metric" style="border-bottom: none;">
                    <span class="metric-label">Timestamp</span>
                    <span class="metric-value" style="font-size: 0.9em;">$goptLastTime</span>
                </div>
            </div>
            
            <!-- Performance Card -->
            <div class="card">
                <h2><span class="icon">⚡</span> LLM Performance</h2>
"@

if ($perfData.lumen.available) {
    $lumenLatency = [math]::Round($perfData.lumen.p50_ms, 1)
    $lumenStatus = if ($lumenLatency -lt 100) { "status-ok" } elseif ($lumenLatency -lt 200) { "status-warning" } else { "status-error" }
    $html += @"
                <div class="metric">
                    <span class="metric-label">Lumen (Cloud)</span>
                    <span class="metric-value">
                        <span class="status-badge $lumenStatus">${lumenLatency}ms</span>
                    </span>
                </div>
"@
}
else {
    $html += @"
                <div class="metric">
                    <span class="metric-label">Lumen (Cloud)</span>
                    <span class="metric-value">
                        <span class="status-badge status-offline">Not Available</span>
                    </span>
                </div>
"@
}

if ($perfData.lmstudio.available) {
    $lmLatency = [math]::Round($perfData.lmstudio.p50_ms, 1)
    $lmStatus = if ($lmLatency -lt 200) { "status-ok" } elseif ($lmLatency -lt 500) { "status-warning" } else { "status-error" }
    $html += @"
                <div class="metric">
                    <span class="metric-label">LM Studio (Local)</span>
                    <span class="metric-value">
                        <span class="status-badge $lmStatus">${lmLatency}ms</span>
                    </span>
                </div>
"@
}
else {
    $html += @"
                <div class="metric">
                    <span class="metric-label">LM Studio (Local)</span>
                    <span class="metric-value">
                        <span class="status-badge status-offline">Not Available</span>
                    </span>
                </div>
"@
}

$html += @"
            </div>
        </div>
        
        <!-- Anomaly Detection Section -->
        <div class="card" style="grid-column: 1 / -1;">
            <h2><span class="icon">🔍</span> Anomaly Detection (Last $LookbackHours hours)</h2>
"@

if ($recentAnomalies.Count -gt 0) {
    $html += @"
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Severity</th>
                            <th>Type</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
"@
    foreach ($anomaly in $recentAnomalies | Sort-Object { [DateTime]::Parse($_.timestamp) } -Descending) {
        $ts = ([DateTime]::Parse($anomaly.timestamp)).ToString("MM-dd HH:mm:ss")
        $severityClass = switch ($anomaly.severity) {
            "critical" { "anomaly-critical" }
            "warning" { "anomaly-warning" }
            default { "anomaly-info" }
        }
        $html += @"
                        <tr>
                            <td>$ts</td>
                            <td class="$severityClass">$($anomaly.severity.ToUpper())</td>
                            <td>$($anomaly.anomaly_type)</td>
                            <td style="font-size: 0.9em;">$($anomaly.details)</td>
                        </tr>
"@
    }
    $html += @"
                    </tbody>
                </table>
            </div>
"@
}
else {
    $html += @"
            <div class="metric" style="justify-content: center; border-bottom: none;">
                <span style="opacity: 0.7;">✅ No anomalies detected in the last $LookbackHours hours</span>
            </div>
"@
}

$html += @"
        </div>
        
        <!-- Healing Actions Section -->
        <div class="card" style="grid-column: 1 / -1;">
            <h2><span class="icon">🛠️</span> Auto-Healing Actions (Last $LookbackHours hours)</h2>
"@

if ($recentHealings.Count -gt 0) {
    $html += @"
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Anomaly Type</th>
                            <th>Action</th>
                            <th>Status</th>
                            <th>Details</th>
                        </tr>
                    </thead>
                    <tbody>
"@
    foreach ($healing in $recentHealings | Sort-Object { [DateTime]::Parse($_.timestamp) } -Descending) {
        $ts = ([DateTime]::Parse($healing.timestamp)).ToString("MM-dd HH:mm:ss")
        $statusClass = if ($healing.status -eq "success") { "healing-success" } else { "healing-failed" }
        $html += @"
                        <tr>
                            <td>$ts</td>
                            <td>$($healing.anomaly_type)</td>
                            <td>$($healing.action_type)</td>
                            <td class="$statusClass">$($healing.status.ToUpper())</td>
                            <td style="font-size: 0.9em;">$($healing.details)</td>
                        </tr>
"@
    }
    $html += @"
                    </tbody>
                </table>
            </div>
"@
}
else {
    $html += @"
            <div class="metric" style="justify-content: center; border-bottom: none;">
                <span style="opacity: 0.7;">No healing actions executed in the last $LookbackHours hours</span>
            </div>
"@
}

$html += @"
        </div>
"@

if ($resourceSummaryText) {
    $html += @"
        <div class="card" style="grid-column: 1 / -1;">
            <h2><span class="icon">🤖</span> RPA Worker Monitor</h2>
            <div class="metric" style="flex-direction: column; align-items: flex-start; gap: 6px;">
                <div>
                    <strong>Status:</strong>
                    <span style="margin-left: 6px; font-family: 'Consolas', 'Courier New', monospace;">
$(if ($rpaStatusLine) { $rpaStatusLine } else { "Status not available." })
                    </span>
                </div>
"@
    if ($rpaAlertSummary) {
        $html += @"
                <div style="margin-top: 6px;">
                    <strong>Alert:</strong>
                    <span style="margin-left: 6px; color: #ffcc66; font-family: 'Consolas', 'Courier New', monospace;">$rpaAlertSummary</span>
                </div>
"@
    }
    else {
        $html += @"
                <div style="margin-top: 6px; opacity: 0.7;">
                    No active alerts.
                </div>
"@
    }
    $html += @"
            </div>
        </div>
"@

    $html += @"
        <div class="card" style="grid-column: 1 / -1;">
            <h2><span class="icon">⚖️</span> Resource Budget (Preview)</h2>
            <div class="table-container">
                <pre>
$resourceSummaryText
                </pre>
            </div>
        </div>
"@
}
else {
    $html += @"
        <div class="card" style="grid-column: 1 / -1;">
            <h2><span class="icon">🤖</span> RPA Worker Monitor</h2>
            <div class="metric" style="flex-direction: column; align-items: flex-start; gap: 6px;">
                <div>
                    <strong>Status:</strong>
                    <span style="margin-left: 6px; font-family: 'Consolas', 'Courier New', monospace;">
$(if ($rpaStatusLine) { $rpaStatusLine } else { "Status not available." })
                    </span>
                </div>
                <div style="margin-top: 6px; opacity: 0.7;">
                    $(if ($rpaAlertSummary) { "Alert: $rpaAlertSummary" } else { "No active alerts." })
                </div>
            </div>
        </div>
"@

    $html += @"
        <div class="card" style="grid-column: 1 / -1;">
            <h2><span class="icon">⚖️</span> Resource Budget (Preview)</h2>
            <div class="metric" style="justify-content: center; border-bottom: none;">
                <span style="opacity: 0.7;">Resource optimizer summary not available.</span>
            </div>
        </div>
"@
}

if ($policyPreviewText) {
    $html += @"
        <div class="card" style="grid-column: 1 / -1;">
            <h2><span class="icon">📄</span> Policy Snapshot (Preview)</h2>
            <div class="table-container">
                <pre>
$policyPreviewText
                </pre>
            </div>
        </div>
"@
}
else {
    $html += @"
        <div class="card" style="grid-column: 1 / -1;">
            <h2><span class="icon">📄</span> Policy Snapshot (Preview)</h2>
            <div class="metric" style="justify-content: center; border-bottom: none;">
                <span style="opacity: 0.7;">Policy snapshot not available.</span>
            </div>
        </div>
"@
}
$html += @"
        <div class="footer">
            <p>AGI Real-Time Monitoring System | Phase 3+ Enhanced Dashboard</p>
            <p style="margin-top: 8px; opacity: 0.6;">Auto-refresh: Every 60s (auto)</p>
        </div>
    </div>
</body>
</html>
"@

# Save HTML
$outDir = Split-Path $OutHtml -Parent
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$html | Set-Content $OutHtml -Encoding UTF8

Write-Host "✓ Enhanced dashboard generated: $OutHtml" -ForegroundColor Green

if ($OpenBrowser) {
    Start-Process $OutHtml
    Write-Host "  Browser opened" -ForegroundColor Cyan
}

exit 0


