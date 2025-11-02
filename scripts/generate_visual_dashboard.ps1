# Generate Visual HTML Dashboard
# Creates interactive HTML dashboard with charts and real-time metrics

param(
    [string]$JsonSource = "$PSScriptRoot\..\outputs\unified_dashboard_latest.json",
    [string]$BenchmarkLog = "$PSScriptRoot\..\outputs\performance_benchmark_log.jsonl",
    [string]$OutHtml = "$PSScriptRoot\..\outputs\system_dashboard_latest.html",
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"

Write-Host "🎨 Generating Visual Dashboard..." -ForegroundColor Cyan

# Read data
if (-not (Test-Path $JsonSource)) {
    Write-Host "❌ Dashboard data not found. Run generate_unified_dashboard.ps1 first." -ForegroundColor Red
    exit 1
}

$data = Get-Content $JsonSource | ConvertFrom-Json

# Read benchmark history for sparklines
$benchHistory = @()
if (Test-Path $BenchmarkLog) {
    $benchHistory = Get-Content $BenchmarkLog | ForEach-Object { 
        try { $_ | ConvertFrom-Json } catch { $null }
    } | Where-Object { $_ -ne $null }
}

# Generate sparkline data
$lumenSparkline = ($benchHistory | ForEach-Object { $_.lumen.avg_ms }) -join ","
$lmStudioSparkline = ($benchHistory | ForEach-Object { $_.lm_studio.avg_ms }) -join ","
$timestamps = ($benchHistory | ForEach-Object { 
        try { [DateTime]::Parse($_.timestamp).ToString("HH:mm") } catch { "" }
    }) -join ","

# Health status color
$healthColor = switch ($data.system_status.health_status) {
    "Healthy" { "#4ade80" }
    "Degraded" { "#facc15" }
    "Critical" { "#ef4444" }
    default { "#9ca3af" }
}

# HTML Template
$html = @"
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AGI System Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 3em;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .auto-refresh-badge {
            display: inline-block;
            margin-top: 10px;
            padding: 6px 12px;
            background: rgba(255,255,255,0.2);
            border-radius: 6px;
            font-size: 0.85em;
            color: white;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .card:hover {
            transform: translateY(-4px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        .card-title {
            font-size: 1.4em;
            font-weight: 600;
            margin-bottom: 16px;
            color: #1f2937;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card-title .icon {
            font-size: 1.5em;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #e5e7eb;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-label {
            color: #6b7280;
            font-size: 0.95em;
        }
        .metric-value {
            font-weight: 600;
            color: #1f2937;
            font-size: 1.1em;
        }
        .health-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 1.3em;
            color: white;
            background: $healthColor;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .recommendation {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
            border-radius: 8px;
            margin-top: 12px;
            font-weight: 500;
        }
        .sparkline {
            width: 100%;
            height: 60px;
            margin-top: 12px;
        }
        .status-online {
            color: #10b981;
            font-weight: 600;
        }
        .status-offline {
            color: #ef4444;
            font-weight: 600;
        }
        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            opacity: 0.8;
        }
        .timestamp {
            font-size: 0.9em;
            color: #9ca3af;
            margin-top: 8px;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AGI System Dashboard</h1>
            <div class="subtitle">Autonomous Operations Monitor</div>
            <div class="auto-refresh-badge">
                🔄 Auto-refresh: <span id="countdown">300</span>s
            </div>
        </div>

        <div class="grid">
            <!-- System Health Card -->
            <div class="card">
                <div class="card-title">
                    <span class="icon">💚</span>
                    System Health
                </div>
                <div style="text-align: center; margin: 20px 0;">
                    <span class="health-badge">$($data.system_status.health_status) ($($data.system_status.health_score)%)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Scheduled Tasks</span>
                    <span class="metric-value">$($data.system_status.scheduled_tasks.ready)/$($data.system_status.scheduled_tasks.total) Ready</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Queue Server</span>
                    <span class="metric-value $(if($data.system_status.queue.online){'status-online'}else{'status-offline'})">
                        $(if($data.system_status.queue.online){'Online'}else{'Offline'})
                    </span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Workers</span>
                    <span class="metric-value">$($data.system_status.queue.workers)</span>
                </div>
            </div>

            <!-- Routing Policy Card -->
            <div class="card">
                <div class="card-title">
                    <span class="icon">🧭</span>
                    Routing Policy
                </div>
                <div class="metric">
                    <span class="metric-label">Primary Backend</span>
                    <span class="metric-value">$($data.system_status.routing_policy.primary_backend)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Fallback Backend</span>
                    <span class="metric-value">$($data.system_status.routing_policy.fallback_backend)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Latency Threshold</span>
                    <span class="metric-value">$($data.system_status.routing_policy.latency_threshold_ms) ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Auto Adjust</span>
                    <span class="metric-value">$($data.system_status.routing_policy.auto_adjust)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Updated</span>
                    <span class="metric-value">$($data.system_status.routing_policy.last_updated)</span>
                </div>
                <div class="recommendation" style="margin-top:16px;">
                    임계값 로직: LM Studio > 임계값이면 Lumen으로 라우팅, 그 외는 Primary 우선(옵션에 따라 Local 선호).
                </div>
                <div style="margin-top:10px; display:flex; gap:10px; flex-wrap:wrap;">
                    <a href="./performance_trend_analysis.json" style="text-decoration:none; background:#111827; color:#fff; padding:8px 12px; border-radius:6px;">View Trend JSON</a>
                    <a href="./performance_trend_analysis.md" style="text-decoration:none; background:#374151; color:#fff; padding:8px 12px; border-radius:6px;">View Trend MD</a>
                </div>
            </div>

            <!-- Performance Card -->
            <div class="card">
                <div class="card-title">
                    <span class="icon">⚡</span>
                    Performance Metrics
                </div>
                <div class="metric">
                    <span class="metric-label">Lumen Gateway</span>
                    <span class="metric-value" style="color: #10b981;">$([math]::Round($data.performance.lumen.avg_latency_ms, 0))ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">LM Studio Local</span>
                    <span class="metric-value" style="color: #f59e0b;">$([math]::Round($data.performance.lm_studio.avg_latency_ms, 0))ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Throughput (LM)</span>
                    <span class="metric-value">$($data.performance.lm_studio.tokens_per_sec) tok/s</span>
                </div>
                <div class="recommendation">
                    🎯 $($data.performance.recommendation)
                </div>
            </div>

            <!-- Activity Card -->
            <div class="card">
                <div class="card-title">
                    <span class="icon">📊</span>
                    Recent Activity
                </div>
                <div class="metric">
                    <span class="metric-label">Ledger Entries (24h)</span>
                    <span class="metric-value">$($data.recent_activity.ledger_entries_24h)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Completed Tasks</span>
                    <span class="metric-value">$($data.system_status.queue.completed_tasks)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Success Rate</span>
                    <span class="metric-value">$([math]::Round($data.system_status.queue.success_rate * 100, 1))%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Report Age</span>
                    <span class="metric-value">$([math]::Round($data.recent_activity.autopoietic_report_age_hours, 1))h</span>
                </div>
            </div>
        </div>

        <!-- Trend Chart -->
        <div class="card" style="margin-bottom: 20px;">
            <div class="card-title">
                <span class="icon">📈</span>
                Latency Trend (Recent Benchmarks)
            </div>
            <canvas id="trendChart" style="max-height: 300px;"></canvas>
        </div>

        <div class="footer">
            <div>Generated: $($data.generated_at)</div>
            <div class="timestamp">Auto-refresh recommended every 5 minutes</div>
        </div>
    </div>

    <script>
        // Trend Chart
        const ctx = document.getElementById('trendChart').getContext('2d');
    const lumenData = [$lumenSparkline];
    const lmStudioData = [$lmStudioSparkline];
    const labels = '$timestamps'.split(',');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Lumen Gateway',
                        data: lumenData,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'LM Studio Local',
                        data: lmStudioData,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Latency (ms)'
                        }
                    }
                }
            }
        });

        // Auto-refresh functionality
        let countdown = 300; // 5 minutes
        const countdownEl = document.getElementById('countdown');
        
        setInterval(() => {
            countdown--;
            countdownEl.textContent = countdown;
            
            if (countdown <= 0) {
                location.reload();
            }
        }, 1000);
    </script>
</body>
</html>
"@

# Save HTML
$outDir = Split-Path -Parent $OutHtml
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$html | Set-Content -Path $OutHtml -Encoding UTF8

Write-Host "✓ Dashboard generated: $OutHtml" -ForegroundColor Green

if ($OpenBrowser) {
    Start-Process $OutHtml
    Write-Host "✓ Opened in browser" -ForegroundColor Green
}

Write-Host ""
