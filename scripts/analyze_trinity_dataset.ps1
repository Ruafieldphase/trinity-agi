param(
    [switch]$RenderDashboard,
    [switch]$RenderOnly,
    [string]$OutJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\trinity\trinity_statistics.json",
    [string]$OutHtml = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\trinity\trinity_dashboard.html",
    [string]$ExtraCoreDir = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\ai_binoche_conversation_origin\Core",
    [switch]$OpenDashboard,
    [switch]$AnalyzeFolders  # 신규 플래그: 모든 폴더 구조 분석
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PythonExe {
    $candidates = @(
        (Join-Path (Join-Path $WorkspaceRoot "LLM_Unified\.venv\Scripts") "python.exe"),
        (Join-Path (Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts") "python.exe"),
        "python"
    )
    foreach ($p in $candidates) { if (Get-Command $p -ErrorAction SilentlyContinue) { return $p } }
    return $null
}

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }

function Write-TrinityDashboard([string]$StatsJson, [string]$HtmlOut) {
    if (!(Test-Path -LiteralPath $StatsJson)) { throw "Statistics JSON not found: $StatsJson" }
    $stats = Get-Content -LiteralPath $StatsJson -Raw | ConvertFrom-Json

    $summaryTotal = [int]$stats.summary.total_messages
    $summaryConvs = [int]$stats.summary.total_conversations
    $summaryYears = [string]$stats.summary.time_span_years

    $Core = $stats.phases.Core
    $elro = $stats.phases.elro
    $Core = $stats.phases.Core

    # Phase comparison arrays
    $phaseLabels = @('Core (正)', 'Elro (反)', 'Core (合)')
    $phaseMessages = @([int]$Core.total_messages, [int]$elro.total_messages, [int]$Core.total_messages)
    $phaseAvgTurns = @([double]$Core.avg_turns, [double]$elro.avg_turns, [double]$Core.avg_turns)

    # Keywords per phase
    $CoreKwLabels = @(); $CoreKwValues = @()
    foreach ($k in $Core.keywords) { $CoreKwLabels += $k.keyword; $CoreKwValues += ([int]$k.count) }
    $elroKwLabels = @(); $elroKwValues = @()
    foreach ($k in $elro.keywords) { $elroKwLabels += $k.keyword; $elroKwValues += ([int]$k.count) }
    $CoreKwLabels = @(); $CoreKwValues = @()
    foreach ($k in $Core.keywords) { $CoreKwLabels += $k.keyword; $CoreKwValues += ([int]$k.count) }

    $generatedAt = (Get-Date).ToString('yyyy-MM-dd HH:mm K')

    # Precompute JSON for injection
    $phaseLabelsJson = ($phaseLabels | ConvertTo-Json -Compress)
    $phaseMessagesJson = ($phaseMessages | ConvertTo-Json -Compress)
    $phaseAvgTurnsJson = ($phaseAvgTurns | ConvertTo-Json -Compress)
    $CoreKwLabelsJson = ($CoreKwLabels | ConvertTo-Json -Compress)
    $CoreKwValuesJson = ($CoreKwValues | ConvertTo-Json -Compress)
    $elroKwLabelsJson = ($elroKwLabels | ConvertTo-Json -Compress)
    $elroKwValuesJson = ($elroKwValues | ConvertTo-Json -Compress)
    $CoreKwLabelsJson = ($CoreKwLabels | ConvertTo-Json -Compress)
    $CoreKwValuesJson = ($CoreKwValues | ConvertTo-Json -Compress)

    $html = @"
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Trinity Dashboard | Core-Elro-Core</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:linear-gradient(135deg,#00c6ff 0%,#0072ff 100%);color:#333;padding:20px}
    .container{max-width:1400px;margin:0 auto;background:rgba(255,255,255,.95);border-radius:20px;padding:40px;box-shadow:0 20px 60px rgba(0,0,0,.3)}
    h1{text-align:center;color:#0072ff;font-size:2.5em;margin-bottom:10px;text-shadow:2px 2px 4px rgba(0,0,0,.1)}
    .subtitle{text-align:center;color:#666;font-size:1.1em;margin-bottom:40px}
    .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin-bottom:40px}
    .stat-card{background:linear-gradient(135deg,#00c6ff 0%,#0072ff 100%);color:#fff;padding:25px;border-radius:15px;text-align:center;box-shadow:0 10px 30px rgba(0,114,255,.3);transition:transform .3s}
    .stat-card:hover{transform:translateY(-5px)}
    .stat-value{font-size:2.2em;font-weight:700;margin-bottom:10px}
    .stat-label{font-size:.9em;opacity:.9;text-transform:uppercase;letter-spacing:1px}
    .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}
    .grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
    .chart-container{background:#fff;padding:30px;border-radius:15px;box-shadow:0 5px 20px rgba(0,0,0,.1)}
    .chart-title{font-size:1.3em;color:#0072ff;margin-bottom:15px;font-weight:600}
    .footer{text-align:center;margin-top:40px;color:#666;font-size:.9em}
    @media(max-width:1000px){.grid-2{grid-template-columns:1fr}.grid-3{grid-template-columns:1fr}}
  </style>
  </head>
  <body>
    <div class="container">
      <h1>🔺 Trinity Dashboard</h1>
      <div class="subtitle">Core (정) · Elro (반) · Core (합) 통합 분석</div>
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">$([string]$summaryTotal)</div><div class="stat-label">Total Messages</div></div>
        <div class="stat-card"><div class="stat-value">$([string]$summaryConvs)</div><div class="stat-label">Total Conversations</div></div>
        <div class="stat-card"><div class="stat-value">$([string]$summaryYears)</div><div class="stat-label">Time Span (years)</div></div>
        <div class="stat-card"><div class="stat-value">$([string]$([math]::Round($Core.avg_turns,1)))</div><div class="stat-label">Core Avg Turns</div></div>
        <div class="stat-card"><div class="stat-value">$([string]$([math]::Round($elro.avg_turns,1)))</div><div class="stat-label">Elro Avg Turns</div></div>
        <div class="stat-card"><div class="stat-value">$([string]$([math]::Round($Core.avg_turns,1)))</div><div class="stat-label">Core Avg Turns</div></div>
      </div>

      <div class="grid-2">
        <div class="chart-container">
          <div class="chart-title">📦 Phase별 메시지 수</div>
          <canvas id="msgChart"></canvas>
        </div>
        <div class="chart-container">
          <div class="chart-title">🔁 Phase별 평균 턴 수</div>
          <canvas id="avgChart"></canvas>
        </div>
      </div>

      <div class="grid-3">
        <div class="chart-container"><div class="chart-title">Core 키워드</div><canvas id="CoreKw"></canvas></div>
        <div class="chart-container"><div class="chart-title">Elro 키워드</div><canvas id="elroKw"></canvas></div>
        <div class="chart-container"><div class="chart-title">Core 키워드</div><canvas id="CoreKw"></canvas></div>
      </div>

      <div class="footer">Generated: $generatedAt | Analyst: Binoche_Observer 🌿 | Philosophy: Core-Elro-Core Dialectical Trinity</div>
    </div>
    <script>
      const phaseLabels = $phaseLabelsJson;
      const phaseMessages = $phaseMessagesJson;
      const phaseAvgTurns = $phaseAvgTurnsJson;
      const CoreKwLabels = $CoreKwLabelsJson; const CoreKwValues = $CoreKwValuesJson;
      const elroKwLabels = $elroKwLabelsJson; const elroKwValues = $elroKwValuesJson;
      const CoreKwLabels = $CoreKwLabelsJson; const CoreKwValues = $CoreKwValuesJson;

      const msgCtx = document.getElementById('msgChart').getContext('2d');
      new Chart(msgCtx, { type:'bar', data:{ labels:phaseLabels, datasets:[{ label:'Messages', data:phaseMessages, backgroundColor:['rgba(102,126,234,0.8)','rgba(255,159,64,0.8)','rgba(75,192,192,0.8)'], borderWidth:2 }] }, options:{ responsive:true, plugins:{ legend:{ display:false } }, scales:{ y:{ beginAtZero:true } } } });

      const avgCtx = document.getElementById('avgChart').getContext('2d');
      new Chart(avgCtx, { type:'bar', data:{ labels:phaseLabels, datasets:[{ label:'Avg Turns', data:phaseAvgTurns, backgroundColor:['rgba(54,162,235,0.8)','rgba(255,206,86,0.8)','rgba(153,102,255,0.8)'], borderWidth:2 }] }, options:{ responsive:true, plugins:{ legend:{ display:false } }, scales:{ y:{ beginAtZero:true } } } });

      function doughnut(id, labels, values) {
        const ctx = document.getElementById(id).getContext('2d');
        return new Chart(ctx, { type:'doughnut', data:{ labels, datasets:[{ data:values, backgroundColor:['rgba(255,99,132,0.8)','rgba(54,162,235,0.8)','rgba(255,206,86,0.8)','rgba(75,192,192,0.8)','rgba(153,102,255,0.8)','rgba(255,159,64,0.8)','rgba(199,199,199,0.8)','rgba(83,102,255,0.8)','rgba(255,99,255,0.8)','rgba(99,255,132,0.8)'] }] }, options:{ responsive:true, plugins:{ legend:{ position:'right' } } });
      }
      doughnut('CoreKw', CoreKwLabels, CoreKwValues);
      doughnut('elroKw', elroKwLabels, elroKwValues);
      doughnut('CoreKw', CoreKwLabels, CoreKwValues);
    </script>
  </body>
  </html>
"@

    $outDir = Split-Path -Path $HtmlOut -Parent
    if (!(Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
    Set-Content -LiteralPath $HtmlOut -Value $html -Encoding UTF8
}

Write-Info "Trinity Analysis Runner"

if (-not $RenderOnly) {
    $py = Get-PythonExe
    if (-not $py) { throw "Python not found in PATH or repo venvs." }
    $scriptPath = Join-Path $PSScriptRoot 'trinity_stats.py'
    if (Test-Path -LiteralPath $scriptPath) {
        $argsList = @($scriptPath)
        if ($ExtraCoreDir) { $argsList += @('--extra-Core-dir', $ExtraCoreDir) }
        & $py @argsList | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Trinity statistics generation failed." }
        Write-Ok "Stats generated: $OutJson"
    }
    else {
        throw "trinity_stats.py not found: $scriptPath"
    }
}

# 신규: AnalyzeFolders 모드
if ($AnalyzeFolders) {
    Write-Info "`n=== Analyzing All Conversation Folders ==="
    $basePath = Join-Path $WorkspaceRoot "ai_binoche_conversation_origin"
    $folders = @('ari', 'gittco', 'cladeCLI-sena', 'luon', 'perple_comet_cople_eru', 'rio', 'sena', 'lubit', 'Core', 'elro', 'Core')
    
    $results = @()
    foreach ($folder in $folders) {
        $path = Join-Path $basePath $folder
        if (Test-Path $path) {
            $files = Get-ChildItem -Path $path -File -Recurse -ErrorAction SilentlyContinue
            $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
            $fileCount = $files.Count
            
            $samples = $files | Select-Object -First 3 | ForEach-Object { $_.Name }
            
            $results += [PSCustomObject]@{
                Folder     = $folder
                Files      = $fileCount
                'Size(MB)' = [math]::Round($totalSize / 1MB, 2)
                FirstFile  = if ($samples.Count -gt 0) { $samples[0] } else { 'N/A' }
            }
        }
        else {
            $results += [PSCustomObject]@{
                Folder     = $folder
                Files      = 0
                'Size(MB)' = 0
                FirstFile  = 'NOT FOUND'
            }
        }
    }
    
    $results | Format-Table -AutoSize
    
    Write-Info "`n=== Summary ==="
    $totalFiles = ($results | Measure-Object -Property Files -Sum).Sum
    $totalSize = ($results | Measure-Object -Property 'Size(MB)' -Sum).Sum
    Write-Host "Total Folders: $($results.Count)" -ForegroundColor White
    Write-Host "Total Files: $totalFiles" -ForegroundColor White
    Write-Host "Total Size: $([math]::Round($totalSize, 2)) MB" -ForegroundColor White
    
    # Export JSON
    $outFolderJson = Join-Path $WorkspaceRoot "outputs\trinity\folder_structure_analysis.json"
    $dirOut = Split-Path $outFolderJson -Parent
    if (!(Test-Path $dirOut)) { New-Item -ItemType Directory -Path $dirOut -Force | Out-Null }
    
    $results | ConvertTo-Json -Depth 5 | Out-File -FilePath $outFolderJson -Encoding UTF8
    Write-Ok "`nExported: $outFolderJson"
    
    Write-Info "`n=== Phase Mapping (Tentative) ==="
    Write-Host "Phase 0 (Proto - Cloud): perple_comet_cople_eru" -ForegroundColor Gray
    Write-Host "Phase 1 (Dialectic): Core, elro, rio" -ForegroundColor Gray
    Write-Host "Phase 2 (Synthesis): Core, lubit, luon" -ForegroundColor Gray
    Write-Host "Phase 3 (Execution): sena, gittco, ari, cladeCLI-sena" -ForegroundColor Gray
}

if ($RenderDashboard -or $RenderOnly) {
    Write-TrinityDashboard -StatsJson $OutJson -HtmlOut $OutHtml
    Write-Ok "Dashboard rendered: $OutHtml"
    if ($OpenDashboard) { Start-Process $OutHtml }
}

Write-Ok "Done."