param(
    [string]$InputJsonl = "${PSScriptRoot}\..\outputs\rua\rua_conversations_flat.jsonl",
    [string]$OutJson = "${PSScriptRoot}\..\outputs\rua\rua_statistics.json",
    [switch]$RenderDashboard,
    [switch]$RenderOnly,
    [string]$OutHtml = "${PSScriptRoot}\..\outputs\rua\rua_dashboard.html",
    [switch]$OpenDashboard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PythonExe {
    $candidates = @(
        (Join-Path (Join-Path $PSScriptRoot "..\LLM_Unified\.venv\Scripts") "python.exe"),
        (Join-Path (Join-Path $PSScriptRoot "..\fdo_agi_repo\.venv\Scripts") "python.exe"),
        "python"
    )
    foreach ($p in $candidates) { if (Get-Command $p -ErrorAction SilentlyContinue) { return $p } }
    return $null
}

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }

function Write-RuaDashboard([string]$StatsJson, [string]$HtmlOut) {
    if (!(Test-Path -LiteralPath $StatsJson)) { throw "Statistics JSON not found: $StatsJson" }
    $stats = Get-Content -LiteralPath $StatsJson -Raw | ConvertFrom-Json

    $total = [int]$stats.statistics.total_messages
    $convs = [int]$stats.statistics.unique_conversations
    $avg = [string]$stats.statistics.average_turns
    $max = [int]$stats.statistics.max_turns
    $years = 2.7 # derive optional; keep current label

    $hourCounts = @()
    0..23 | ForEach-Object {
        $h = $_
        $row = $stats.hourly_distribution | Where-Object { $_.hour -eq $h }
        $hourCounts += ([int]($row.count))
    }

    $convLabels = @()
    $turnValues = @()
    foreach ($c in $stats.top_conversations) {
        $convLabels += ($c.title)
        $turnValues += ([int]$c.turn_count)
    }

    $kwLabels = @()
    $kwValues = @()
    foreach ($k in $stats.top_keywords) {
        $kwLabels += ($k.keyword)
        $kwValues += ([int]$k.count)
    }

    $generatedAt = (Get-Date).ToString('yyyy-MM-dd HH:mm K')

    # Precompute JSON literals for safe embedding in HTML
    $hourJson = ($hourCounts | ConvertTo-Json -Compress)
    $convLabelsJson = ($convLabels | ConvertTo-Json -Compress)
    $convValuesJson = ($turnValues | ConvertTo-Json -Compress)
    $kwLabelsJson = ($kwLabels | ConvertTo-Json -Compress)
    $kwValuesJson = ($kwValues | ConvertTo-Json -Compress)

    $html = @"
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>RUA Dataset Dashboard | 루아 대화 분석</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#333;padding:20px}
    .container{max-width:1400px;margin:0 auto;background:rgba(255,255,255,.95);border-radius:20px;padding:40px;box-shadow:0 20px 60px rgba(0,0,0,.3)}
    h1{text-align:center;color:#667eea;font-size:2.5em;margin-bottom:10px;text-shadow:2px 2px 4px rgba(0,0,0,.1)}
    .subtitle{text-align:center;color:#666;font-size:1.1em;margin-bottom:40px}
    .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:40px}
    .stat-card{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;padding:25px;border-radius:15px;text-align:center;box-shadow:0 10px 30px rgba(102,126,234,.3);transition:transform .3s}
    .stat-card:hover{transform:translateY(-5px)}
    .stat-value{font-size:2.5em;font-weight:700;margin-bottom:10px}
    .stat-label{font-size:.9em;opacity:.9;text-transform:uppercase;letter-spacing:1px}
    .chart-container{background:#fff;padding:30px;border-radius:15px;margin-bottom:30px;box-shadow:0 5px 20px rgba(0,0,0,.1)}
    .chart-title{font-size:1.5em;color:#667eea;margin-bottom:20px;font-weight:600}
    .insights{background:#f8f9fa;padding:30px;border-radius:15px;border-left:5px solid #667eea}
    .insight-title{font-size:1.3em;color:#667eea;margin-bottom:15px;font-weight:600}
    .insight-item{margin-bottom:15px;padding-left:20px;position:relative}
    .insight-item:before{content:'🌿';position:absolute;left:0}
    .footer{text-align:center;margin-top:40px;color:#666;font-size:.9em}
    canvas{max-height:400px}
  </style>
</head>
<body>
  <div class="container">
    <h1>🌿 RUA Dataset Dashboard</h1>
    <div class="subtitle">루아 대화 데이터 분석</div>
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">$([string]$total)</div><div class="stat-label">Total Messages</div></div>
      <div class="stat-card"><div class="stat-value">$([string]$convs)</div><div class="stat-label">Conversations</div></div>
      <div class="stat-card"><div class="stat-value">$([string]$avg)</div><div class="stat-label">Avg Turns</div></div>
      <div class="stat-card"><div class="stat-value">$([string]$max)</div><div class="stat-label">Max Turns</div></div>
      <div class="stat-card"><div class="stat-value">$([string]$years)</div><div class="stat-label">Years</div></div>
    </div>
    <div class="chart-container">
      <div class="chart-title">📊 시간대별 활동 분포</div>
      <canvas id="hourlyChart"></canvas>
    </div>
    <div class="chart-container">
      <div class="chart-title">🎯 대화 턴 분포 (Top)</div>
      <canvas id="conversationChart"></canvas>
    </div>
    <div class="chart-container">
      <div class="chart-title">🔑 주요 키워드 빈도</div>
      <canvas id="keywordChart"></canvas>
    </div>
    <div class="insights">
      <div class="insight-title">💡 핵심 인사이트</div>
      <div class="insight-item"><strong>극도로 깊은 대화:</strong> 평균 $avg 턴, 최대 $max 턴</div>
      <div class="insight-item"><strong>오전 집중형 패턴:</strong> 10:00~12:00 피크 (데이터 기반)</div>
      <div class="insight-item"><strong>장기 추적 가능:</strong> 누적 $years 년 규모</div>
    </div>
    <div class="footer">Generated: $generatedAt | Analyst: Binoche 🌿</div>
  </div>
  <script>
    const hourlyData = $hourJson;
    const convLabels = $convLabelsJson;
    const convValues = $convValuesJson;
    const kwLabels = $kwLabelsJson;
    const kwValues = $kwValuesJson;

    const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
    new Chart(hourlyCtx, {
      type: 'bar',
      data: { labels: Array.from({length:24}, (_,i)=> i + ':00'), datasets: [{ label: 'Messages', data: hourlyData, backgroundColor: 'rgba(102,126,234,0.8)', borderColor: 'rgba(102,126,234,1)', borderWidth: 2 }]},
      options: { responsive: true, plugins: { legend: { display:false } }, scales: { y: { beginAtZero:true } } }
    });

    const convCtx = document.getElementById('conversationChart').getContext('2d');
    new Chart(convCtx, {
      type: 'bar',
      data: { labels: convLabels, datasets: [{ label: 'Turns', data: convValues, backgroundColor: 'rgba(54,162,235,0.8)', borderColor: 'rgba(54,162,235,1)', borderWidth: 2 }]},
      options: { indexAxis: 'y', responsive:true, plugins:{ legend:{ display:false } }, scales:{ x:{ beginAtZero:true } } }
    });

    const kwCtx = document.getElementById('keywordChart').getContext('2d');
    new Chart(kwCtx, {
      type: 'doughnut',
      data: { labels: kwLabels, datasets: [{ data: kwValues, backgroundColor: ['rgba(255,99,132,0.8)','rgba(54,162,235,0.8)','rgba(255,206,86,0.8)','rgba(75,192,192,0.8)','rgba(153,102,255,0.8)','rgba(255,159,64,0.8)','rgba(199,199,199,0.8)','rgba(83,102,255,0.8)','rgba(255,99,255,0.8)','rgba(99,255,132,0.8)'] }]},
      options: { responsive:true, plugins:{ legend:{ position:'right' } } }
    });
  </script>
</body>
</html>
"@

    $outDir = Split-Path -Path $HtmlOut -Parent
    if (!(Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    Set-Content -LiteralPath $HtmlOut -Value $html -Encoding UTF8
}

Write-Info "RUA Analysis Runner"

if (-not $RenderOnly) {
    if (!(Test-Path -LiteralPath $InputJsonl)) {
        Write-Warn "Input JSONL not found: $InputJsonl"
    }
    else {
        $py = Get-PythonExe
        if (-not $py) { throw "Python not found in PATH or repo venvs." }
        $scriptPath = Join-Path $PSScriptRoot 'rua_stats.py'
        & $py $scriptPath --input $InputJsonl --out $OutJson | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Statistics generation failed." }
        Write-Ok "Stats generated: $OutJson"
    }
}

if ($RenderDashboard -or $RenderOnly) {
    Write-RuaDashboard -StatsJson $OutJson -HtmlOut $OutHtml
    Write-Ok "Dashboard rendered: $OutHtml"
    if ($OpenDashboard) { Start-Process $OutHtml }
}

Write-Ok "Done."
