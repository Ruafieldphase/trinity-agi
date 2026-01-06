# Generate Realtime Dashboard (Original Data Phase 4 Complete)
# 목적: Ledger + Resonance + 통합 상태 대시보드 생성

param(
    [int]$WindowHours = 24,
    [switch]$OpenDashboard,
    [switch]$Help
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


if ($Help) {
    Write-Host @"
Generate Realtime Dashboard - Original Data Phase 4

Usage:
  scripts\generate_realtime_dashboard.ps1 [options]

Options:
  -WindowHours <int>   Time window (default: 24)
  -OpenDashboard       Open HTML dashboard after generation
  -Help                Show this help

Examples:
  # 기본 실행
  scripts\generate_realtime_dashboard.ps1

  # 대시보드 자동 열기
  scripts\generate_realtime_dashboard.ps1 -OpenDashboard

  # 12시간 윈도우
  scripts\generate_realtime_dashboard.ps1 -WindowHours 12 -OpenDashboard

Exit Code:
  0 = Success
  1 = Failure
"@
    exit 0
}

$ErrorActionPreference = "Stop"

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$OutputsDir = Join-Path $WorkspaceRoot "outputs"
$DashboardPath = Join-Path $OutputsDir "realtime_dashboard_latest.html"

Write-Host "=== Realtime Dashboard Generator ===" -ForegroundColor Cyan
Write-Host "Window: $WindowHours hours" -ForegroundColor Gray
Write-Host ""

# 1. Resonance Bridge 실행
Write-Host "[1/3] Running Resonance Bridge..." -ForegroundColor Yellow
& "$PSScriptRoot\run_realtime_resonance.ps1" -WindowHours $WindowHours
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Resonance Bridge failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Resonance metrics collected" -ForegroundColor Green
Write-Host ""

# 2. Resonance JSON 읽기
Write-Host "[2/3] Loading resonance data..." -ForegroundColor Yellow
$ResonanceJson = Join-Path $OutputsDir "realtime_resonance_latest.json"
if (-not (Test-Path $ResonanceJson)) {
    Write-Host "✗ Resonance JSON not found: $ResonanceJson" -ForegroundColor Red
    exit 1
}

$Data = Get-Content -Path $ResonanceJson -Raw | ConvertFrom-Json
Write-Host "✓ Loaded $($Data.events_count) events" -ForegroundColor Green
Write-Host ""

# 3. HTML 대시보드 생성
Write-Host "[3/3] Generating HTML dashboard..." -ForegroundColor Yellow

$Html = @"
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Realtime Dashboard - Original Data Phase 4</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2.5rem;
            color: #667eea;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #666;
        }
        .status {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }
        .status.success {
            background: #10b981;
            color: white;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h2 {
            font-size: 1.5rem;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-label {
            font-weight: 600;
            color: #555;
        }
        .metric-value {
            font-size: 1.3rem;
            font-weight: bold;
            color: #667eea;
        }
        .metric-value.excellent {
            color: #10b981;
        }
        .metric-value.warning {
            color: #f59e0b;
        }
        .recommendation {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 15px;
            font-size: 1.1rem;
            font-weight: 500;
        }
        .timestamp {
            text-align: center;
            color: #white;
            margin-top: 20px;
            font-size: 0.9rem;
            background: rgba(255,255,255,0.9);
            padding: 15px;
            border-radius: 10px;
        }
        .phase-indicator {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 15px;
            background: #764ba2;
            color: white;
            font-weight: bold;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌟 Realtime Dashboard</h1>
            <div class="subtitle">Original Data Phase 4 - Ledger + Resonance Integration</div>
            <span class="status success">$($Data.status.ToUpper())</span>
            <span class="phase-indicator">$($Data.prediction.current_phase.day) - $($Data.prediction.current_phase.emotion)</span>
        </header>

        <div class="grid">
            <!-- Ledger Metrics -->
            <div class="card">
                <h2>📊 Ledger Metrics</h2>
                <div class="metric">
                    <span class="metric-label">Events Collected</span>
                    <span class="metric-value excellent">$($Data.events_count)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Confidence</span>
                    <span class="metric-value excellent">$("{0:P1}" -f $Data.metrics.avg_confidence)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Quality</span>
                    <span class="metric-value excellent">$("{0:P1}" -f $Data.metrics.avg_quality)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Success Rate</span>
                    <span class="metric-value excellent">$("{0:P1}" -f $Data.metrics.success_rate)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Avg Duration</span>
                    <span class="metric-value">$("{0:N2}" -f $Data.metrics.avg_duration)s</span>
                </div>
            </div>

            <!-- Resonance State -->
            <div class="card">
                <h2>🔮 Resonance State</h2>
                <div class="metric">
                    <span class="metric-label">Current Resonance</span>
                    <span class="metric-value excellent">$("{0:P1}" -f $Data.resonance_state.resonance)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Info Density</span>
                    <span class="metric-value">$("{0:N3}" -f $Data.resonance_state.info_density)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Entropy</span>
                    <span class="metric-value">$("{0:N3}" -f $Data.resonance_state.entropy)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Logical Coherence</span>
                    <span class="metric-value excellent">$("{0:P1}" -f $Data.resonance_state.logical_coherence)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Ethical Alignment</span>
                    <span class="metric-value">$("{0:P1}" -f $Data.resonance_state.ethical_alignment)</span>
                </div>
            </div>

            <!-- Prediction -->
            <div class="card">
                <h2>🎯 Prediction</h2>
                <div class="metric">
                    <span class="metric-label">Predicted Resonance</span>
                    <span class="metric-value excellent">$("{0:P1}" -f $Data.prediction.predicted_resonance)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Predicted Entropy</span>
                    <span class="metric-value">$("{0:N3}" -f $Data.prediction.predicted_entropy)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Horizon Warning</span>
                    <span class="metric-value">$($Data.prediction.horizon_warning)</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Horizon Crossings</span>
                    <span class="metric-value">$($Data.resonance_state.horizon_crossings)</span>
                </div>
                <div class="recommendation">
                    💡 $($Data.prediction.recommended_action)
                </div>
            </div>
        </div>

        <div class="timestamp">
            Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")<br>
            Window: $WindowHours hours | Steps: $($Data.resonance_state.current_step)
        </div>
    </div>
</body>
</html>
"@

$Html | Out-File -FilePath $DashboardPath -Encoding UTF8
Write-Host "✓ Dashboard saved: $DashboardPath" -ForegroundColor Green
Write-Host ""

# 4. 대시보드 열기
if ($OpenDashboard) {
    Write-Host "Opening dashboard..." -ForegroundColor Gray
    Start-Process $DashboardPath
}

Write-Host "=== Dashboard Generation Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "  Events: $($Data.events_count)" -ForegroundColor Gray
Write-Host "  Resonance: $("{0:P1}" -f $Data.resonance_state.resonance)" -ForegroundColor Gray
Write-Host "  Phase: $($Data.prediction.current_phase.day)" -ForegroundColor Gray
Write-Host "  Action: $($Data.prediction.recommended_action)" -ForegroundColor Gray
Write-Host ""

exit 0