# Music-Goal 통합 검증 스크립트
param(
    [switch]$Detailed,
    [switch]$OpenReport
)

$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent $PSScriptRoot

Write-Host "🔍 Music-Goal Integration Validation" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$report = @{
    timestamp = (Get-Date).ToString('o')
    validation_results = @{}
    issues = @()
    recommendations = @()
}

# 1. Goal Tracker 구조 검증
Write-Host "`n1️⃣ Validating Goal Tracker Schema..." -ForegroundColor Yellow
$trackerPath = "$ws\fdo_agi_repo\memory\goal_tracker.json"

if (!(Test-Path -LiteralPath $trackerPath)) {
    $report.issues += "Goal tracker file not found: $trackerPath"
    $report.validation_results['tracker_exists'] = $false
} else {
    $report.validation_results['tracker_exists'] = $true
    
    try {
        $tracker = Get-Content -LiteralPath $trackerPath -Raw | ConvertFrom-Json
        
        # source 필드 확인
        $hasSourceField = $tracker.goals | Where-Object { $_.PSObject.Properties.Name -contains 'source' }
        $report.validation_results['has_source_field'] = [bool]$hasSourceField
        
        if (!$hasSourceField) {
            $report.recommendations += "Add 'source' field to goal schema"
        }
        
        # tags 필드 확인
        $hasTagsField = $tracker.goals | Where-Object { $_.PSObject.Properties.Name -contains 'tags' }
        $report.validation_results['has_tags_field'] = [bool]$hasTagsField
        
        if (!$hasTagsField) {
            $report.recommendations += "Add 'tags' field to goal schema"
        }
        
        # music_daemon 소스 목표 확인
        $musicGoals = $tracker.goals | Where-Object { $_.source -eq 'music_daemon' }
        $report.validation_results['music_goals_count'] = $musicGoals.Count
        
        Write-Host "   ✅ Tracker schema validated" -ForegroundColor Green
        Write-Host "     - Goals with source field: $($hasSourceField.Count)" -ForegroundColor Cyan
        Write-Host "     - Music-triggered goals: $($musicGoals.Count)" -ForegroundColor Magenta
        
    } catch {
        $report.issues += "Failed to parse goal tracker: $($_.Exception.Message)"
        $report.validation_results['tracker_valid'] = $false
    }
}

# 2. Music-Goal 이벤트 로그 검증
Write-Host "`n2️⃣ Validating Music-Goal Event Log..." -ForegroundColor Yellow
$eventsPath = "$ws\outputs\music_goal_events.jsonl"

if (!(Test-Path -LiteralPath $eventsPath)) {
    $report.validation_results['event_log_exists'] = $false
    $report.recommendations += "Create music_goal_events.jsonl for event tracking"
} else {
    $report.validation_results['event_log_exists'] = $true
    
    try {
        $events = Get-Content -LiteralPath $eventsPath | ForEach-Object { $_ | ConvertFrom-Json }
        $report.validation_results['total_events'] = $events.Count
        
        # 필수 필드 검증
        $requiredFields = @('timestamp', 'event_type', 'goal_id', 'goal_title', 'rhythm_phase', 'rhythm_score')
        $validEvents = $events | Where-Object {
            $ev = $_
            ($requiredFields | ForEach-Object { $ev.PSObject.Properties.Name -contains $_ }) -notcontains $false
        }
        
        $report.validation_results['valid_events'] = $validEvents.Count
        $report.validation_results['invalid_events'] = $events.Count - $validEvents.Count
        
        if ($report.validation_results['invalid_events'] -gt 0) {
            $report.issues += "Found $($report.validation_results['invalid_events']) events with missing fields"
        }
        
        Write-Host "   ✅ Event log validated" -ForegroundColor Green
        Write-Host "     - Total events: $($events.Count)" -ForegroundColor Cyan
        Write-Host "     - Valid events: $($validEvents.Count)" -ForegroundColor Green
        
    } catch {
        $report.issues += "Failed to parse event log: $($_.Exception.Message)"
        $report.validation_results['event_log_valid'] = $false
    }
}

# 3. Music Daemon 통합 검증
Write-Host "`n3️⃣ Validating Music Daemon Integration..." -ForegroundColor Yellow
$daemonPath = "$ws\scripts\music_daemon.py"

if (!(Test-Path -LiteralPath $daemonPath)) {
    $report.issues += "Music daemon script not found: $daemonPath"
    $report.validation_results['daemon_exists'] = $false
} else {
    $report.validation_results['daemon_exists'] = $true
    
    # --auto-goal 플래그 확인
    $daemonContent = Get-Content -LiteralPath $daemonPath -Raw
    $hasAutoGoalFlag = $daemonContent -like '*--auto-goal*'
    $report.validation_results['has_auto_goal_flag'] = $hasAutoGoalFlag
    
    if (!$hasAutoGoalFlag) {
        $report.recommendations += "Add --auto-goal CLI flag to music_daemon.py"
    }
    
    # GoalTracker import 확인
    $hasGoalTrackerImport = $daemonContent -like '*from fdo_agi_repo.memory.goal_tracker import*' -or
                            $daemonContent -like '*import goal_tracker*'
    $report.validation_results['has_goal_tracker_import'] = $hasGoalTrackerImport
    
    if (!$hasGoalTrackerImport) {
        $report.recommendations += "Import GoalTracker in music_daemon.py"
    }
    
    Write-Host "   ✅ Daemon integration checked" -ForegroundColor Green
    Write-Host "     - Auto-goal flag: $hasAutoGoalFlag" -ForegroundColor Cyan
    Write-Host "     - GoalTracker import: $hasGoalTrackerImport" -ForegroundColor Cyan
}

# 4. Dashboard 필터링 검증
Write-Host "`n4️⃣ Validating Dashboard Filtering..." -ForegroundColor Yellow
$dashboardPath = "$ws\scripts\autonomous_goal_dashboard.py"

if (!(Test-Path -LiteralPath $dashboardPath)) {
    $report.issues += "Dashboard script not found: $dashboardPath"
    $report.validation_results['dashboard_exists'] = $false
} else {
    $report.validation_results['dashboard_exists'] = $true
    
    $dashboardContent = Get-Content -LiteralPath $dashboardPath -Raw
    
    # source 필터 확인
    $hasSourceFilter = $dashboardContent -like '*source*filter*' -or
                       $dashboardContent -like '*filter.*source*'
    $report.validation_results['has_source_filter'] = $hasSourceFilter
    
    if (!$hasSourceFilter) {
        $report.recommendations += "Add source-based filtering to autonomous_goal_dashboard.py"
    }
    
    Write-Host "   ✅ Dashboard filtering checked" -ForegroundColor Green
    Write-Host "     - Source filter: $hasSourceFilter" -ForegroundColor Cyan
}

# 최종 리포트 생성
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 Validation Summary" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$passedChecks = ($report.validation_results.Values | Where-Object { $_ -eq $true -or ($_ -is [int] -and $_ -ge 0) }).Count
$totalChecks = $report.validation_results.Count

Write-Host "`nChecks Passed: $passedChecks / $totalChecks" -ForegroundColor $(if ($passedChecks -eq $totalChecks) { 'Green' } else { 'Yellow' })

if ($report.issues.Count -gt 0) {
    Write-Host "`n⚠️ Issues Found:" -ForegroundColor Red
    foreach ($issue in $report.issues) {
        Write-Host "  - $issue" -ForegroundColor Yellow
    }
}

if ($report.recommendations.Count -gt 0) {
    Write-Host "`n💡 Recommendations:" -ForegroundColor Cyan
    foreach ($rec in $report.recommendations) {
        Write-Host "  - $rec" -ForegroundColor White
    }
}

# JSON 리포트 저장
$reportPath = "$ws\outputs\music_goal_validation_report.json"
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host "`n✅ Validation report saved: $reportPath" -ForegroundColor Green

if ($OpenReport) {
    code $reportPath
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

# Exit code
if ($report.issues.Count -gt 0) {
    exit 1
} else {
    exit 0
}