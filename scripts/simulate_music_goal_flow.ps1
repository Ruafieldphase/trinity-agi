# 음악-리듬-목표 전체 플로우 시뮬레이션
param(
    [switch]$DryRun,
    [switch]$Verbose,
    [int]$SimulateDurationSeconds = 90
)

$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent $PSScriptRoot

Write-Host "🎵 Music-Goal Flow Simulation" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

# 1. Music Daemon 상태 확인
Write-Host "`n1️⃣ Checking Music Daemon..." -ForegroundColor Yellow
$musicProc = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object { 
    $_.CommandLine -like '*music_daemon.py*' 
}

if ($musicProc) {
    Write-Host "   ✅ Music Daemon is running (PID: $($musicProc.Id))" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ Music Daemon not running" -ForegroundColor Yellow
    Write-Host "   Starting Music Daemon with --auto-goal..." -ForegroundColor Cyan
    
    $py = "$ws\fdo_agi_repo\.venv\Scripts\python.exe"
    if (!(Test-Path -LiteralPath $py)) { $py = 'python' }
    
    if (!$DryRun) {
        Start-Process -FilePath $py -ArgumentList "$ws\scripts\music_daemon.py","--auto-goal","--interval","60","--threshold","0.3" -WindowStyle Hidden -PassThru | Out-Null
        Start-Sleep -Seconds 2
        Write-Host "   ✅ Music Daemon started" -ForegroundColor Green
    }
}

# 2. Rhythm 상태 파일 확인
Write-Host "`n2️⃣ Checking Rhythm State..." -ForegroundColor Yellow
$rhythmFiles = @(
    "$ws\outputs\RHYTHM_REST_PHASE_*.md",
    "$ws\outputs\RHYTHM_ACTIVE_PHASE_*.md",
    "$ws\outputs\RHYTHM_SYSTEM_STATUS_REPORT.md"
)

$latestRhythm = Get-ChildItem -Path $ws\outputs -Filter 'RHYTHM_*PHASE_*.md' -ErrorAction SilentlyContinue | 
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($latestRhythm) {
    $phase = if ($latestRhythm.Name -like '*REST*') { 'REST' } else { 'ACTIVE' }
    $age = ((Get-Date) - $latestRhythm.LastWriteTime).TotalMinutes
    Write-Host "   ✅ Latest Rhythm: $phase (${age:N1}m ago)" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ No rhythm state found" -ForegroundColor Yellow
}

# 3. Goal Tracker 상태
Write-Host "`n3️⃣ Checking Goal Tracker..." -ForegroundColor Yellow
$trackerPath = "$ws\fdo_agi_repo\memory\goal_tracker.json"

if (Test-Path -LiteralPath $trackerPath) {
    $tracker = Get-Content -LiteralPath $trackerPath -Raw | ConvertFrom-Json
    $musicGoals = $tracker.goals | Where-Object { 
        $_.source -eq 'music_daemon' -or $_.tags -contains 'source:music_daemon'
    }
    
    Write-Host "   ✅ Total goals: $($tracker.goals.Count)" -ForegroundColor Green
    if ($musicGoals) {
        Write-Host "   🎵 Music-triggered goals: $($musicGoals.Count)" -ForegroundColor Magenta
    }
} else {
    Write-Host "   ⚠️ Goal tracker not found" -ForegroundColor Yellow
}

# 4. Music-Goal 이벤트 로그
Write-Host "`n4️⃣ Checking Music-Goal Events..." -ForegroundColor Yellow
$eventsPath = "$ws\outputs\music_goal_events.jsonl"

if (Test-Path -LiteralPath $eventsPath) {
    $eventCount = (Get-Content -LiteralPath $eventsPath).Count
    Write-Host "   ✅ Event log exists: $eventCount events" -ForegroundColor Green
    
    if ($Verbose -and $eventCount -gt 0) {
        Write-Host "`n   Recent events:" -ForegroundColor Cyan
        Get-Content -LiteralPath $eventsPath -Tail 3 | ForEach-Object {
            $ev = $_ | ConvertFrom-Json
            Write-Host "     $($ev.timestamp) | $($ev.event_type) | $($ev.goal_title)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "   ℹ️ No event log yet" -ForegroundColor Cyan
}

# 5. 시뮬레이션 (Music → Rhythm → Goal)
if (!$DryRun) {
    Write-Host "`n5️⃣ Simulating Music-Goal Flow..." -ForegroundColor Yellow
    Write-Host "   ⏱️ Duration: ${SimulateDurationSeconds}s" -ForegroundColor Cyan
    
    $startTime = Get-Date
    $iterations = [math]::Ceiling($SimulateDurationSeconds / 10)
    
    for ($i = 1; $i -le $iterations; $i++) {
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        
        # Progress bar
        $progress = [math]::Min(100, ($elapsed / $SimulateDurationSeconds) * 100)
        Write-Progress -Activity "Simulating Flow" -Status "$($elapsed:N0)s / $SimulateDurationSeconds s" -PercentComplete $progress
        
        # 10초마다 상태 체크
        if ($i % 2 -eq 0) {
            $currentTracker = Get-Content -LiteralPath $trackerPath -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
            $currentMusicGoals = $currentTracker.goals | Where-Object { $_.source -eq 'music_daemon' }
            
            if ($currentMusicGoals -and $currentMusicGoals.Count -gt ($musicGoals.Count)) {
                Write-Host "`n   🎯 New music-triggered goal detected!" -ForegroundColor Green
                $newGoal = $currentMusicGoals | Sort-Object created_at -Descending | Select-Object -First 1
                Write-Host "     Title: $($newGoal.title)" -ForegroundColor Cyan
                Write-Host "     Created: $($newGoal.created_at)" -ForegroundColor Gray
                $musicGoals = $currentMusicGoals
            }
        }
        
        Start-Sleep -Seconds 10
    }
    
    Write-Progress -Activity "Simulating Flow" -Completed
}

# 최종 리포트
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 Flow Simulation Report" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if (Test-Path -LiteralPath $trackerPath) {
    $finalTracker = Get-Content -LiteralPath $trackerPath -Raw | ConvertFrom-Json
    $finalMusicGoals = $finalTracker.goals | Where-Object { $_.source -eq 'music_daemon' }
    
    Write-Host "`nGoal Statistics:" -ForegroundColor Yellow
    Write-Host "  Total goals: $($finalTracker.goals.Count)" -ForegroundColor White
    Write-Host "  Music-triggered: $($finalMusicGoals.Count)" -ForegroundColor Magenta
    
    $statusGroups = $finalMusicGoals | Group-Object status
    foreach ($group in $statusGroups) {
        $color = switch ($group.Name) {
            'completed' { 'Green' }
            'in_progress' { 'Yellow' }
            'failed' { 'Red' }
            default { 'Gray' }
        }
        Write-Host "  $($group.Name): $($group.Count)" -ForegroundColor $color
    }
}

if (Test-Path -LiteralPath $eventsPath) {
    $totalEvents = (Get-Content -LiteralPath $eventsPath).Count
    Write-Host "`nEvent Log:" -ForegroundColor Yellow
    Write-Host "  Total events: $totalEvents" -ForegroundColor White
}

Write-Host "`n✅ Simulation complete" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan
