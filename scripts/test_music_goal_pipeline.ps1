# Music → Rhythm → Goal 파이프라인 E2E 테스트
# 전체 플로우를 시뮬레이션하고 검증합니다

param(
    [switch]$Verbose,
    [switch]$OpenDashboard
)

$ErrorActionPreference = 'Stop'
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

Write-Host "🎵 Music-Goal Pipeline E2E Test" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# 1. Music Daemon 상태 확인
Write-Host "1️⃣ Checking Music Daemon status..." -ForegroundColor Yellow
$musicProc = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like '*music_daemon.py*' 
}

if ($musicProc) {
    Write-Host "✅ Music Daemon is running (PID: $($musicProc.Id))" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Music Daemon not running. Starting..." -ForegroundColor Yellow
    $py = 'c:\workspace\agi\fdo_agi_repo\.venv\Scripts\python.exe'
    if (!(Test-Path -LiteralPath $py)) { $py = 'python' }
    
    Start-Process -FilePath $py -ArgumentList 'c:\workspace\agi\scripts\music_daemon.py', '--auto-goal', '--interval', '60', '--threshold', '0.3' -WindowStyle Hidden -PassThru | Out-Null
    Start-Sleep 3
    Write-Host "✅ Music Daemon started with auto-goal mode" -ForegroundColor Green
}

# 2. 리듬 상태 파일 확인
Write-Host "`n2️⃣ Checking rhythm state..." -ForegroundColor Yellow
$rhythmFiles = Get-ChildItem 'c:\workspace\agi\outputs' -Filter 'RHYTHM_*.md' -ErrorAction SilentlyContinue | 
Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($rhythmFiles) {
    Write-Host "✅ Latest rhythm: $($rhythmFiles.Name)" -ForegroundColor Green
    Write-Host "   Updated: $($rhythmFiles.LastWriteTime)" -ForegroundColor Cyan
}
else {
    Write-Host "⚠️ No rhythm files found" -ForegroundColor Yellow
}

# 3. Goal Tracker 상태 확인
Write-Host "`n3️⃣ Checking Goal Tracker..." -ForegroundColor Yellow
$trackerPath = 'c:\workspace\agi\fdo_agi_repo\memory\goal_tracker.json'
if (Test-Path $trackerPath) {
    $tracker = Get-Content $trackerPath -Raw -Encoding utf8 | ConvertFrom-Json
    
    # Music-triggered goals 찾기
    $musicGoals = $tracker.goals | Where-Object { 
        $_.tags -and ($_.tags -contains 'source:music_daemon' -or $_.tags -contains 'trigger:rhythm')
    }
    
    Write-Host "✅ Goal Tracker found" -ForegroundColor Green
    Write-Host "   Total goals: $($tracker.goals.Count)" -ForegroundColor Cyan
    Write-Host "   Music-triggered goals: $($musicGoals.Count)" -ForegroundColor Cyan
    
    if ($musicGoals.Count -gt 0) {
        Write-Host "`n   Latest music-triggered goal:" -ForegroundColor Magenta
        $latest = $musicGoals | Sort-Object created_at -Descending | Select-Object -First 1
        Write-Host "   - Title: $($latest.title)" -ForegroundColor White
        Write-Host "   - Status: $($latest.status)" -ForegroundColor White
        Write-Host "   - Created: $($latest.created_at)" -ForegroundColor White
        Write-Host "   - Tags: $($latest.tags -join ', ')" -ForegroundColor White
    }
}
else {
    Write-Host "⚠️ Goal Tracker not found" -ForegroundColor Yellow
}

# 4. Music-Goal Events 로그 확인
Write-Host "`n4️⃣ Checking Music-Goal event log..." -ForegroundColor Yellow
$eventLog = 'c:\workspace\agi\outputs\music_goal_events.jsonl'
if (Test-Path $eventLog) {
    $events = Get-Content $eventLog -Encoding utf8 | ForEach-Object { 
        if ($_.Trim()) { $_ | ConvertFrom-Json } 
    }
    
    Write-Host "✅ Event log found" -ForegroundColor Green
    Write-Host "   Total events: $($events.Count)" -ForegroundColor Cyan
    
    if ($events.Count -gt 0) {
        $latest = $events | Select-Object -Last 1
        Write-Host "`n   Latest event:" -ForegroundColor Magenta
        Write-Host "   - Timestamp: $($latest.timestamp)" -ForegroundColor White
        Write-Host "   - Goal: $($latest.goal_title)" -ForegroundColor White
        Write-Host "   - Trigger: $($latest.trigger_type)" -ForegroundColor White
        
        if ($latest.rhythm_metrics) {
            Write-Host "   - Rhythm: $($latest.rhythm_metrics.phase) ($([math]::Round($latest.rhythm_metrics.health_score * 100, 1))%)" -ForegroundColor White
        }
    }
}
else {
    Write-Host "⚠️ Event log not found" -ForegroundColor Yellow
}

# 5. 최근 24시간 음악 분석
Write-Host "`n5️⃣ Analyzing recent music activity..." -ForegroundColor Yellow
$py = 'c:\workspace\agi\fdo_agi_repo\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $py)) { $py = 'python' }

$analysisScript = 'c:\workspace\agi\scripts\generate_groove_profile.py'
if (Test-Path $analysisScript) {
    & $py $analysisScript --hours 24 2>&1 | Out-Null
    
    $grooveProfile = 'c:\workspace\agi\outputs\groove_profile_latest.json'
    if (Test-Path $grooveProfile) {
        $profile = Get-Content $grooveProfile -Raw -Encoding utf8 | ConvertFrom-Json
        Write-Host "✅ Groove profile generated" -ForegroundColor Green
        Write-Host "   Tracks analyzed: $($profile.total_tracks)" -ForegroundColor Cyan
        Write-Host "   Dominant mood: $($profile.dominant_mood)" -ForegroundColor Cyan
        Write-Host "   Avg energy: $([math]::Round($profile.avg_energy * 100, 1))%" -ForegroundColor Cyan
    }
}
else {
    Write-Host "⚠️ Groove profile script not found" -ForegroundColor Yellow
}

# 6. 파이프라인 상태 요약
Write-Host "`n" -NoNewline
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "📊 Pipeline Status Summary" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray

$components = @(
    @{ Name = "Music Daemon"; Status = ($null -ne $musicProc) }
    @{ Name = "Rhythm System"; Status = ($null -ne $rhythmFiles) }
    @{ Name = "Goal Tracker"; Status = (Test-Path $trackerPath) }
    @{ Name = "Event Log"; Status = (Test-Path $eventLog) }
)

foreach ($comp in $components) {
    $icon = if ($comp.Status) { "✅" } else { "❌" }
    $color = if ($comp.Status) { "Green" } else { "Red" }
    Write-Host "$icon $($comp.Name)" -ForegroundColor $color
}

Write-Host "`n🎯 Pipeline health: " -NoNewline -ForegroundColor Cyan
$healthPct = ($components | Where-Object { $_.Status }).Count / $components.Count * 100
if ($healthPct -eq 100) {
    Write-Host "EXCELLENT ($healthPct%)" -ForegroundColor Green
}
elseif ($healthPct -ge 75) {
    Write-Host "GOOD ($healthPct%)" -ForegroundColor Yellow
}
else {
    Write-Host "DEGRADED ($healthPct%)" -ForegroundColor Red
}

# 7. Dashboard 열기 (옵션)
if ($OpenDashboard) {
    Write-Host "`n📊 Opening dashboard..." -ForegroundColor Yellow
    & 'c:\workspace\agi\scripts\generate_autonomous_goal_dashboard.ps1' -OpenBrowser
}

Write-Host "`n✨ Test complete!" -ForegroundColor Green
