# Enhanced System Dashboard with GPU Metrics
# Generates comprehensive HTML dashboard including GPU monitoring
# Part of Phase 3+ Real-Time Monitoring Enhancement

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
