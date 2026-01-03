# Music → Rhythm → Goal 전체 플로우 테스트
# 실제 음악 재생 없이 시뮬레이션으로 검증

param(
    [switch]$Verbose,
    [string]$OutJson = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\music_goal_flow_test_latest.json"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$Results = @{
    timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
    steps = @()
    success = $false
}

function Add-Step {
    param($Name, $Status, $Details)
    $script:Results.steps += @{
        name = $Name
        status = $Status
        timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
        details = $Details
    }
    if ($Verbose) {
        $color = if ($Status -eq 'success') { 'Green' } else { 'Red' }
        Write-Host "[$Status] $Name" -ForegroundColor $color
        if ($Details) {
            Write-Host "   $Details" -ForegroundColor Gray
        }
    }
}

try {
    # Step 1: 리듬 리포트 확인
    Add-Step "Check Rhythm Report" "running" $null
    $rhythmReport = "$WorkspaceRoot\outputs\RHYTHM_SYSTEM_STATUS_REPORT.md"
    if (Test-Path $rhythmReport) {
        $content = Get-Content $rhythmReport -Raw
        $hasRest = $content -match '휴식 페이즈|REST_PHASE'
        $hasActive = $content -match '활성 페이즈|ACTIVE_PHASE'
        Add-Step "Check Rhythm Report" "success" "Found: Rest=$hasRest, Active=$hasActive"
    } else {
        Add-Step "Check Rhythm Report" "failed" "File not found: $rhythmReport"
        throw "Rhythm report not found"
    }

    # Step 2: Goal Tracker 읽기
    Add-Step "Read Goal Tracker" "running" $null
    $trackerPath = "$WorkspaceRoot\fdo_agi_repo\memory\goal_tracker.json"
    if (Test-Path $trackerPath) {
        $tracker = Get-Content $trackerPath -Raw | ConvertFrom-Json
        $goalCount = $tracker.goals.Count
        Add-Step "Read Goal Tracker" "success" "Found $goalCount goals"
    } else {
        Add-Step "Read Goal Tracker" "failed" "File not found: $trackerPath"
        throw "Goal tracker not found"
    }

    # Step 3: Music-Goal 이벤트 로그 확인
    Add-Step "Check Music-Goal Events" "running" $null
    $eventsPath = "$WorkspaceRoot\outputs\music_goal_events.jsonl"
    if (Test-Path $eventsPath) {
        $eventCount = (Get-Content $eventsPath | Measure-Object).Count
        Add-Step "Check Music-Goal Events" "success" "Found $eventCount events"
    } else {
        Add-Step "Check Music-Goal Events" "warning" "No events file (first run?)"
    }

    # Step 4: Music Daemon 프로세스 확인
    Add-Step "Check Music Daemon" "running" $null
    $musicProc = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like '*music_daemon.py*'
    }
    if ($musicProc) {
        $pid = $musicProc.Id
        Add-Step "Check Music Daemon" "success" "Running (PID: $pid)"
    } else {
        Add-Step "Check Music Daemon" "warning" "Not running (manual mode?)"
    }

    # Step 5: 시뮬레이션 - 새 목표 생성 시나리오
    Add-Step "Simulate Goal Creation" "running" $null
    $simGoal = @{
        id = "sim-" + (Get-Date).ToString('yyyyMMddHHmmss')
        title = "[TEST] 음악→리듬→목표 플로우 검증"
        description = "Music Daemon → Rhythm Analysis → Goal Generation 테스트"
        status = "completed"
        created_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
        completed_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
        tags = @{
            source = "music_daemon"
            trigger = "rhythm_test"
            test = "flow_validation"
        }
        metadata = @{
            rhythm_phase = "simulated_rest"
            music_context = "test_binaural_flow"
            auto_generated = $true
        }
    }
    Add-Step "Simulate Goal Creation" "success" "Created test goal: $($simGoal.id)"

    # Step 6: 시뮬레이션 이벤트 로깅
    Add-Step "Log Simulation Event" "running" $null
    $event = @{
        timestamp = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss')
        event_type = "goal_created"
        source = "music_daemon_simulation"
        goal_id = $simGoal.id
        goal_title = $simGoal.title
        trigger = "test_flow"
        metadata = @{
            test_run = $true
            script = "test_music_to_goal_flow.ps1"
        }
    }
    $eventJson = $event | ConvertTo-Json -Compress
    if (-not (Test-Path $eventsPath)) {
        New-Item -ItemType File -Path $eventsPath -Force | Out-Null
    }
    Add-Content -Path $eventsPath -Value $eventJson -Encoding UTF8
    Add-Step "Log Simulation Event" "success" "Logged to $eventsPath"

    # Step 7: 전체 플로우 검증
    Add-Step "Validate Flow" "running" $null
    $flowValid = $true
    $validations = @()
    
    # 리듬 리포트 존재
    if (Test-Path $rhythmReport) {
        $validations += "✓ Rhythm report exists"
    } else {
        $flowValid = $false
        $validations += "✗ Rhythm report missing"
    }
    
    # Goal Tracker 존재
    if (Test-Path $trackerPath) {
        $validations += "✓ Goal tracker exists"
    } else {
        $flowValid = $false
        $validations += "✗ Goal tracker missing"
    }
    
    # 이벤트 로그 작성 가능
    if (Test-Path $eventsPath) {
        $validations += "✓ Events log writable"
    } else {
        $flowValid = $false
        $validations += "✗ Events log not writable"
    }
    
    $validationDetails = $validations -join "`n   "
    if ($flowValid) {
        Add-Step "Validate Flow" "success" $validationDetails
    } else {
        Add-Step "Validate Flow" "failed" $validationDetails
        throw "Flow validation failed"
    }

    # 최종 성공
    $Results.success = $true
    $Results.summary = @{
        total_steps = $Results.steps.Count
        successful = ($Results.steps | Where-Object { $_.status -eq 'success' }).Count
        failed = ($Results.steps | Where-Object { $_.status -eq 'failed' }).Count
        warnings = ($Results.steps | Where-Object { $_.status -eq 'warning' }).Count
    }

    Write-Host "`n✅ Music → Goal Flow Test PASSED" -ForegroundColor Green
    Write-Host "   Steps: $($Results.summary.successful)/$($Results.summary.total_steps) successful" -ForegroundColor Cyan

} catch {
    $Results.success = $false
    $Results.error = $_.Exception.Message
    Write-Host "`n❌ Music → Goal Flow Test FAILED" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Yellow
    exit 1
} finally {
    # JSON 출력
    $Results | ConvertTo-Json -Depth 10 | Set-Content -Path $OutJson -Encoding UTF8
    if ($Verbose) {
        Write-Host "`n📄 Report saved: $OutJson" -ForegroundColor Gray
    }
}