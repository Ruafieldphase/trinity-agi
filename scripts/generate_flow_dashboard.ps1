#!/usr/bin/env pwsh
# generate_flow_dashboard.ps1 - Flow Theory 시각화 대시보드 생성
param(
    [int]$Hours = 24,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$pythonExe = "C:\workspace\agi\LLM_Unified\.venv\Scripts\python.exe"
$scriptPath = "C:\workspace\agi\fdo_agi_repo\monitoring\flow.py"

Write-Host "`n🌊 Flow Theory Dashboard 생성 중..." -ForegroundColor Cyan
Write-Host "   범위: 최근 $Hours 시간" -ForegroundColor Gray

# Flow 메트릭 수집
$result = & $pythonExe $scriptPath --window-hours $Hours --format json

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Flow 메트릭 수집 실패" -ForegroundColor Red
    exit 1
}

$metrics = $result | ConvertFrom-Json

# HTML 대시보드 생성
$htmlPath = "C:\workspace\agi\outputs\flow_dashboard_latest.html"
$html = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Flow Theory Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric-card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 20px; }
        .metric-value { font-size: 2.5em; font-weight: bold; color: #58a6ff; margin: 10px 0; }
        .metric-label { color: #8b949e; font-size: 0.9em; text-transform: uppercase; }
        .flow-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .flow-high { background: #3fb950; }
        .flow-medium { background: #d29922; }
        .flow-low { background: #f85149; }
        .timestamp { color: #8b949e; font-size: 0.85em; text-align: center; margin-top: 30px; }
        .info-section { background: #161b22; border-left: 4px solid #58a6ff; padding: 15px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌊 Flow Theory Dashboard</h1>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Total Flow (bits)</div>
                <div class="metric-value">$($metrics.total_flow.ToString("F2"))</div>
                <span class="flow-indicator $($metrics.total_flow -gt 10 ? 'flow-high' : ($metrics.total_flow -gt 5 ? 'flow-medium' : 'flow-low'))"></span>
                Information Flow
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Mutual Information</div>
                <div class="metric-value">$($metrics.mutual_information.ToString("F2"))</div>
                <span class="flow-indicator $($metrics.mutual_information -gt 5 ? 'flow-high' : ($metrics.mutual_information -gt 2 ? 'flow-medium' : 'flow-low'))"></span>
                Agent Coherence
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Transfer Entropy</div>
                <div class="metric-value">$($metrics.transfer_entropy.ToString("F2"))</div>
                <span class="flow-indicator $($metrics.transfer_entropy -gt 3 ? 'flow-high' : ($metrics.transfer_entropy -gt 1 ? 'flow-medium' : 'flow-low'))"></span>
                Causal Influence
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Flow State</div>
                <div class="metric-value">$($metrics.flow_state)</div>
                <span class="flow-indicator flow-$($metrics.flow_state.ToLower())"></span>
                Overall Status
            </div>
        </div>
        
        <div class="info-section">
            <h3>📊 분석 요약</h3>
            <p><strong>Total Flow:</strong> 시스템 전체의 정보 흐름량 (높을수록 활발)</p>
            <p><strong>Mutual Information:</strong> 에이전트 간 정보 공유도 (높을수록 일관성)</p>
            <p><strong>Transfer Entropy:</strong> 인과적 영향력 전파 (높을수록 효율적)</p>
            <p><strong>Flow State:</strong> HIGH(>10bits) / MEDIUM(5-10) / LOW(<5)</p>
        </div>
        
        <div class="timestamp">
            Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | Window: $Hours hours
        </div>
    </div>
</body>
</html>
"@

$html | Out-File -FilePath $htmlPath -Encoding UTF8
Write-Host "✅ Dashboard 생성: $htmlPath" -ForegroundColor Green

if (-not $NoBrowser) {
    Start-Process $htmlPath
    Write-Host "🌐 브라우저 열기..." -ForegroundColor Cyan
}

Write-Host "`n✨ Flow Dashboard 완료!" -ForegroundColor Green
