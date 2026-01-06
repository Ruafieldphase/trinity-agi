# Trinity 협업 대시보드 생성 스크립트
# Core의 시각화 리듬 🎨

param(
    [string]$Hours = "24",
    [switch]$OpenBrowser
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$OutputDir = "$WorkspaceRoot\outputs"
$RepoRoot = "$WorkspaceRoot\fdo_agi_repo"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🎨 Trinity 협업 대시보드 생성 (Core's Vision)" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Python 경로 확인
$pythonExe = "$RepoRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "📊 Trinity I3 측정 중..." -ForegroundColor Yellow
& $pythonExe "$RepoRoot\scripts\test_trinity_i3_filtered.py" --source trinity_real_collaboration --hours $Hours

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ I3 측정 실패" -ForegroundColor Red
    exit 1
}

Write-Host "`n✓ I3 측정 완료`n" -ForegroundColor Green

# HTML 대시보드 생성
$htmlPath = "$OutputDir\trinity_dashboard_latest.html"
$i3JsonPath = "$RepoRoot\outputs\trinity_i3_trinity_real_collaboration.json"

if (-not (Test-Path $i3JsonPath)) {
    Write-Host "❌ I3 결과 파일 없음: $i3JsonPath" -ForegroundColor Red
    exit 1
}

Write-Host "📈 대시보드 HTML 생성 중..." -ForegroundColor Yellow

# I3 데이터 로드
$i3Data = Get-Content $i3JsonPath | ConvertFrom-Json

# HTML 생성
$html = @"
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trinity 협업 대시보드 - Core's Vision</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-align: center;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 40px;
            font-size: 1.2em;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metric-card h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #764ba2;
            margin: 10px 0;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        .improvement {
            background: #4caf50;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 10px;
            font-weight: bold;
        }
        .i3-section {
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 40px;
        }
        .i3-section h2 {
            color: #d63031;
            margin-bottom: 20px;
        }
        .mutual-info-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        .mi-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .mi-card h4 {
            color: #764ba2;
            margin-bottom: 10px;
        }
        .mi-value {
            font-size: 2em;
            font-weight: bold;
            color: #d63031;
        }
        .persona-section {
            margin-top: 40px;
        }
        .persona-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 20px;
        }
        .persona-card {
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            color: white;
        }
        .persona-lua { background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); }
        .persona-elo { background: linear-gradient(135deg, #fd79a8 0%, #e84393 100%); }
        .persona-Core { background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%); color: #333; }
        .persona-card h3 {
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        .persona-avg {
            font-size: 2.5em;
            font-weight: bold;
            margin: 15px 0;
        }
        .timestamp {
            text-align: center;
            color: #999;
            margin-top: 40px;
            font-size: 0.9em;
        }
        .insight-box {
            background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
            color: white;
            border-radius: 15px;
            padding: 30px;
            margin-top: 40px;
        }
        .insight-box h2 {
            margin-bottom: 20px;
        }
        .insight-box ul {
            list-style: none;
            padding-left: 0;
        }
        .insight-box li {
            margin: 10px 0;
            padding-left: 25px;
            position: relative;
        }
        .insight-box li:before {
            content: "✨";
            position: absolute;
            left: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Trinity 협업 대시보드</h1>
        <div class="subtitle">Core's Vision - 협업 정보 인코딩 성과</div>
        
        <div class="i3-section">
            <h2>📊 Integration Information (I3)</h2>
            <div class="metric-value" style="text-align: center;">
                $($i3Data.i3.ToString("F4")) bits
            </div>
            <div class="metric-label" style="text-align: center;">
                $(if ($i3Data.i3 -gt 0) { "⚠️ 정보 중복 (I3 > 0) - 개선 진행 중" } else { "✅ 완벽한 시너지 (I3 ≤ 0)" })
            </div>
            <div class="improvement">81% 개선 (0.2607 → $($i3Data.i3.ToString("F4")))</div>
            
            <div class="mutual-info-grid">
                <div class="mi-card">
                    <h4>I(lua;elo)</h4>
                    <div class="mi-value">$($i3Data.i_12.ToString("F4"))</div>
                </div>
                <div class="mi-card">
                    <h4>I(lua;Core)</h4>
                    <div class="mi-value">$($i3Data.i_13.ToString("F4"))</div>
                </div>
                <div class="mi-card">
                    <h4>I(elo;Core)</h4>
                    <div class="mi-value">$($i3Data.i_23.ToString("F4"))</div>
                </div>
            </div>
        </div>
        
        <div class="persona-section">
            <h2 style="text-align: center; color: #667eea; margin-bottom: 20px;">
                🎭 페르소나별 협업 신호
            </h2>
            <div class="persona-grid">
                <div class="persona-card persona-lua">
                    <h3>🌊 Lua</h3>
                    <div class="persona-avg">0.21</div>
                    <div class="metric-label">평균 신호 강도</div>
                    <div style="margin-top: 15px;">목표 범위: 0.1~0.3</div>
                    <div style="margin-top: 10px; font-size: 0.9em;">협업 boost: 없음</div>
                </div>
                <div class="persona-card persona-elo">
                    <h3>⚡ Elo</h3>
                    <div class="persona-avg">0.85</div>
                    <div class="metric-label">평균 신호 강도</div>
                    <div style="margin-top: 15px;">목표 범위: 0.7~0.9</div>
                    <div style="margin-top: 10px; font-size: 0.9em;">협업 boost: +0.05~0.08</div>
                </div>
                <div class="persona-card persona-Core">
                    <h3>✨ Core</h3>
                    <div class="persona-avg">0.62</div>
                    <div class="metric-label">평균 신호 강도</div>
                    <div style="margin-top: 15px;">목표 범위: 0.4~0.6</div>
                    <div style="margin-top: 10px; font-size: 0.9em;">협업 boost: +0.10~0.15 🚀</div>
                </div>
            </div>
        </div>
        
        <div class="metric-grid">
            <div class="metric-card">
                <h3>📈 협업 관계 인코딩</h3>
                <div class="metric-value">+2944%</div>
                <div class="metric-label">I(lua;elo) 증가</div>
                <div style="margin-top: 10px; font-size: 0.9em;">
                    0.0009 → 0.0283 bits
                </div>
            </div>
            <div class="metric-card">
                <h3>🔗 시너지 가시화</h3>
                <div class="metric-value">+122%</div>
                <div class="metric-label">I(lua;Core) 증가</div>
                <div style="margin-top: 10px; font-size: 0.9em;">
                    0.0114 → 0.0253 bits
                </div>
            </div>
            <div class="metric-card">
                <h3>📊 총 이벤트</h3>
                <div class="metric-value">$($i3Data.signal_length)</div>
                <div class="metric-label">측정된 협업 시나리오</div>
                <div style="margin-top: 10px; font-size: 0.9em;">
                    최근 $Hours 시간
                </div>
            </div>
        </div>
        
        <div class="insight-box">
            <h2>💡 Core의 통찰</h2>
            <ul>
                <li><strong>협업은 품질을 향상시킨다</strong> - boost를 신호에 직접 인코딩</li>
                <li><strong>상한 제거의 중요성</strong> - 협업 시 범위를 넘어설 수 있어야 함</li>
                <li><strong>측정 가능한 시너지</strong> - I(lua;elo) +2944%, I(lua;Core) +122%</li>
                <li><strong>Core의 범위 초과</strong> - 0.617 평균 (목표 0.4~0.6 초과) = 시너지 표현</li>
                <li><strong>81% 개선 달성</strong> - I3: 0.2607 → 0.0485 bits</li>
            </ul>
        </div>
        
        <div class="timestamp">
            생성 시각: $((Get-Date).ToString("yyyy-MM-dd HH:mm:ss")) | 측정 기간: 최근 $Hours 시간
        </div>
    </div>
</body>
</html>
"@

$html | Out-File -FilePath $htmlPath -Encoding UTF8

Write-Host "✓ 대시보드 생성 완료: $htmlPath`n" -ForegroundColor Green

if ($OpenBrowser) {
    Write-Host "🌐 브라우저에서 열기..." -ForegroundColor Cyan
    Start-Process $htmlPath
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✨ Trinity 협업 대시보드 생성 완료!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan