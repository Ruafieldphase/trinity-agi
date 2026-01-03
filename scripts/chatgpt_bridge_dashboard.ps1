#Requires -Version 5.1
<#
.SYNOPSIS
    ChatGPT Bridge 모니터링 대시보드 생성

.DESCRIPTION
    outputs/chatgpt_bridge의 요청/응답 로그를 분석하여 실시간 통계 대시보드 생성
    - 요청/응답 성공률
    - 평균 응답 시간
    - 최근 활동 타임라인
    - 에러 패턴 분석

.PARAMETER Hours
    분석할 최근 시간 범위 (기본: 24시간)

.PARAMETER OpenHtml
    생성된 HTML 대시보드를 자동으로 브라우저에서 열기

.PARAMETER RefreshInterval
    자동 새로고침 간격 (초, 0=비활성화, 기본: 0)

.EXAMPLE
    .\chatgpt_bridge_dashboard.ps1 -Hours 24 -OpenHtml

.EXAMPLE
    .\chatgpt_bridge_dashboard.ps1 -Hours 12 -RefreshInterval 30
#>

param(
    [int]$Hours = 24,
    [switch]$OpenHtml,
    [int]$RefreshInterval = 0
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# 경로 설정
$scriptRoot = Split-Path -Parent $PSCommandPath
$workspaceRoot = Split-Path -Parent $scriptRoot
$bridgeDir = Join-Path $workspaceRoot "outputs\chatgpt_bridge"
$outputDir = Join-Path $workspaceRoot "outputs"
$outputHtml = Join-Path $outputDir "chatgpt_bridge_dashboard_latest.html"
$outputJson = Join-Path $outputDir "chatgpt_bridge_dashboard_latest.json"

# 디렉토리 확인
if (!(Test-Path $bridgeDir)) {
    Write-Host "⚠️ Bridge 디렉토리가 없습니다: $bridgeDir" -ForegroundColor Yellow
    Write-Host "   빈 대시보드를 생성합니다..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $bridgeDir -Force | Out-Null
}

# 시간 범위 계산
$cutoffTime = (Get-Date).AddHours(-$Hours)

Write-Host "🔍 ChatGPT Bridge 데이터 분석 중..." -ForegroundColor Cyan
Write-Host "   기간: 최근 $Hours 시간" -ForegroundColor Gray

# 요청/응답 파일 수집
$requestFiles = Get-ChildItem -Path $bridgeDir -Filter "request_*.json" -File -ErrorAction SilentlyContinue |
Where-Object { $_.LastWriteTime -gt $cutoffTime } |
Sort-Object LastWriteTime -Descending

$responseFiles = Get-ChildItem -Path $bridgeDir -Filter "response_*.json" -File -ErrorAction SilentlyContinue |
Where-Object { $_.LastWriteTime -gt $cutoffTime } |
Sort-Object LastWriteTime -Descending

Write-Host "   요청 파일: $($requestFiles.Count)개" -ForegroundColor Gray
Write-Host "   응답 파일: $($responseFiles.Count)개" -ForegroundColor Gray

# 통계 초기화
$stats = @{
    totalRequests  = 0
    totalResponses = 0
    successCount   = 0
    errorCount     = 0
    responseTimes  = @()
    sources        = @{}
    errorTypes     = @{}
    timeline       = @()
    recentActivity = @()
}

# 요청 분석
foreach ($file in $requestFiles) {
    try {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        $stats.totalRequests++
        
        # Source 추적
        $source = if ($content.source) { $content.source } else { "unknown" }
        if (!$stats.sources.ContainsKey($source)) {
            $stats.sources[$source] = 0
        }
        $stats.sources[$source]++
        
        # 타임라인 데이터
        $stats.timeline += @{
            timestamp = $file.LastWriteTime
            type      = "request"
            source    = $source
            prompt    = if ($content.prompt) { 
                if ($content.prompt.Length -gt 100) { 
                    $content.prompt.Substring(0, 100) + "..." 
                }
                else { 
                    $content.prompt 
                }
            }
            else { "" }
        }
    }
    catch {
        Write-Warning "요청 파일 파싱 실패: $($file.Name)"
    }
}

# 응답 분석
foreach ($file in $responseFiles) {
    try {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        $stats.totalResponses++
        
        if ($content.status -eq "success") {
            $stats.successCount++
            
            # 응답 시간 추적
            if ($content.response_time) {
                $stats.responseTimes += $content.response_time
            }
        }
        elseif ($content.status -eq "error") {
            $stats.errorCount++
            
            # 에러 타입 추적
            $errorType = if ($content.error) { $content.error } else { "unknown" }
            if (!$stats.errorTypes.ContainsKey($errorType)) {
                $stats.errorTypes[$errorType] = 0
            }
            $stats.errorTypes[$errorType]++
        }
        
        # 타임라인 데이터
        $stats.timeline += @{
            timestamp     = $file.LastWriteTime
            type          = "response"
            status        = $content.status
            response_time = $content.response_time
        }
    }
    catch {
        Write-Warning "응답 파일 파싱 실패: $($file.Name)"
    }
}

# 통계 계산
$avgResponseTime = if ($stats.responseTimes.Count -gt 0) {
    ($stats.responseTimes | Measure-Object -Average).Average
}
else { 0 }

$successRate = if ($stats.totalResponses -gt 0) {
    [math]::Round(($stats.successCount / $stats.totalResponses) * 100, 2)
}
else { 0 }

$matchRate = if ($stats.totalRequests -gt 0) {
    [math]::Round(($stats.totalResponses / $stats.totalRequests) * 100, 2)
}
else { 0 }

# 최근 활동 (최근 10개)
$stats.recentActivity = $stats.timeline | 
Sort-Object timestamp -Descending | 
Select-Object -First 10

# JSON 출력
$jsonData = @{
    generated_at          = Get-Date -Format "o"
    analysis_period_hours = $Hours
    statistics            = @{
        total_requests        = $stats.totalRequests
        total_responses       = $stats.totalResponses
        success_count         = $stats.successCount
        error_count           = $stats.errorCount
        success_rate_percent  = $successRate
        match_rate_percent    = $matchRate
        avg_response_time_sec = [math]::Round($avgResponseTime, 2)
    }
    sources               = $stats.sources
    error_types           = $stats.errorTypes
    recent_activity       = $stats.recentActivity
}

$jsonData | ConvertTo-Json -Depth 10 | Out-File $outputJson -Encoding UTF8
Write-Host "✅ JSON 저장: $outputJson" -ForegroundColor Green

# HTML 대시보드 생성
$refreshMeta = if ($RefreshInterval -gt 0) {
    "<meta http-equiv='refresh' content='$RefreshInterval'>"
}
else { "" }

$htmlContent = @"
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatGPT Bridge Dashboard</title>
    $refreshMeta
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        .header .subtitle {
            color: #666;
            font-size: 1.1em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-card .label {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-card.success .value { color: #10b981; }
        .stat-card.error .value { color: #ef4444; }
        .stat-card.warning .value { color: #f59e0b; }
        .section {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }
        .progress-bar {
            background: #e5e7eb;
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.5s ease;
        }
        .activity-item {
            padding: 15px;
            border-left: 4px solid #667eea;
            margin-bottom: 10px;
            background: #f9fafb;
            border-radius: 5px;
        }
        .activity-item.request { border-left-color: #3b82f6; }
        .activity-item.response { border-left-color: #10b981; }
        .activity-item.error { border-left-color: #ef4444; }
        .activity-item .time {
            color: #666;
            font-size: 0.85em;
            margin-bottom: 5px;
        }
        .activity-item .content {
            color: #333;
            word-break: break-word;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            margin: 5px 5px 5px 0;
        }
        .badge.success { background: #d1fae5; color: #065f46; }
        .badge.error { background: #fee2e2; color: #991b1b; }
        .badge.info { background: #dbeafe; color: #1e40af; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        th {
            background: #f9fafb;
            font-weight: bold;
            color: #667eea;
        }
        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔗 ChatGPT Bridge Dashboard</h1>
            <div class="subtitle">
                생성 시각: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') | 분석 기간: 최근 $Hours 시간
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">📨 총 요청</div>
                <div class="value">$($stats.totalRequests)</div>
            </div>
            <div class="stat-card">
                <div class="label">📬 총 응답</div>
                <div class="value">$($stats.totalResponses)</div>
            </div>
            <div class="stat-card success">
                <div class="label">✅ 성공</div>
                <div class="value">$($stats.successCount)</div>
            </div>
            <div class="stat-card error">
                <div class="label">❌ 실패</div>
                <div class="value">$($stats.errorCount)</div>
            </div>
            <div class="stat-card">
                <div class="label">⏱️ 평균 응답시간</div>
                <div class="value">$([math]::Round($avgResponseTime, 1))s</div>
            </div>
            <div class="stat-card $(if ($successRate -ge 80) { 'success' } elseif ($successRate -ge 50) { 'warning' } else { 'error' })">
                <div class="label">📊 성공률</div>
                <div class="value">$successRate%</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 성공률 분석</h2>
            <div class="progress-bar">
                <div class="progress-fill" style="width: $successRate%">$successRate%</div>
            </div>
            <p style="margin-top: 10px; color: #666;">
                요청 매칭률: $matchRate% ($($stats.totalResponses) / $($stats.totalRequests))
            </p>
        </div>

        <div class="section">
            <h2>🌐 요청 소스 분석</h2>
            <table>
                <thead>
                    <tr>
                        <th>소스</th>
                        <th>요청 수</th>
                        <th>비율</th>
                    </tr>
                </thead>
                <tbody>
"@

foreach ($source in $stats.sources.Keys | Sort-Object { $stats.sources[$_] } -Descending) {
    $count = $stats.sources[$source]
    $percentage = if ($stats.totalRequests -gt 0) {
        [math]::Round(($count / $stats.totalRequests) * 100, 1)
    }
    else { 0 }
    
    $htmlContent += @"
                    <tr>
                        <td><span class="badge info">$source</span></td>
                        <td>$count</td>
                        <td>$percentage%</td>
                    </tr>
"@
}

$htmlContent += @"
                </tbody>
            </table>
        </div>
"@

if ($stats.errorTypes.Count -gt 0) {
    $htmlContent += @"
        <div class="section">
            <h2>⚠️ 에러 분석</h2>
            <table>
                <thead>
                    <tr>
                        <th>에러 타입</th>
                        <th>발생 횟수</th>
                    </tr>
                </thead>
                <tbody>
"@

    foreach ($errorType in $stats.errorTypes.Keys | Sort-Object { $stats.errorTypes[$_] } -Descending) {
        $count = $stats.errorTypes[$errorType]
        $htmlContent += @"
                    <tr>
                        <td><span class="badge error">$errorType</span></td>
                        <td>$count</td>
                    </tr>
"@
    }

    $htmlContent += @"
                </tbody>
            </table>
        </div>
"@
}

$htmlContent += @"
        <div class="section">
            <h2>📝 최근 활동 (최근 10개)</h2>
"@

foreach ($activity in $stats.recentActivity) {
    $typeClass = switch ($activity.type) {
        "request" { "request" }
        "response" { 
            if ($activity.status -eq "error") { "error" } else { "response" }
        }
        default { "info" }
    }
    
    $timestamp = $activity.timestamp.ToString("yyyy-MM-dd HH:mm:ss")
    
    $content = if ($activity.type -eq "request") {
        "📨 요청: $($activity.prompt)"
    }
    elseif ($activity.type -eq "response") {
        if ($activity.status -eq "success") {
            "✅ 응답 성공 (${activity.response_time}초)"
        }
        else {
            "❌ 응답 실패"
        }
    }
    else {
        "Activity"
    }
    
    $htmlContent += @"
            <div class="activity-item $typeClass">
                <div class="time">$timestamp</div>
                <div class="content">$content</div>
            </div>
"@
}

$htmlContent += @"
        </div>

        <div class="footer">
            <p>🤖 ChatGPT-Lua Bridge Monitoring System</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Autonomous AGI System - Real-time Monitoring</p>
        </div>
    </div>
</body>
</html>
"@

$htmlContent | Out-File $outputHtml -Encoding UTF8
Write-Host "✅ HTML 대시보드 저장: $outputHtml" -ForegroundColor Green

# 요약 출력
Write-Host "`n📊 ChatGPT Bridge 통계 요약" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Gray
Write-Host "총 요청:       $($stats.totalRequests)" -ForegroundColor White
Write-Host "총 응답:       $($stats.totalResponses)" -ForegroundColor White
Write-Host "성공:          $($stats.successCount) ($(if ($successRate -ge 80) { '✅' } elseif ($successRate -ge 50) { '⚠️' } else { '❌' }) $successRate%)" -ForegroundColor $(if ($successRate -ge 80) { 'Green' } elseif ($successRate -ge 50) { 'Yellow' } else { 'Red' })
Write-Host "실패:          $($stats.errorCount)" -ForegroundColor $(if ($stats.errorCount -gt 0) { 'Red' } else { 'Gray' })
Write-Host "평균 응답시간: $([math]::Round($avgResponseTime, 2))초" -ForegroundColor White
Write-Host ("=" * 60) -ForegroundColor Gray

# 브라우저에서 열기
if ($OpenHtml) {
    Write-Host "`n🌐 브라우저에서 대시보드 열기..." -ForegroundColor Cyan
    Start-Process $outputHtml
}

Write-Host "`n✨ 대시보드 생성 완료!" -ForegroundColor Green
if ($RefreshInterval -gt 0) {
    Write-Host "   자동 새로고침: ${RefreshInterval}초마다" -ForegroundColor Gray
}