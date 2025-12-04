#Requires -Version 5.1
<#
.SYNOPSIS
    Rhythm Detector - 현재 시스템 리듬 감지
.DESCRIPTION
    현재 시간대와 시스템 상태를 분석하여 적절한 리듬을 표시합니다.
#>

param(
    [switch]$Json
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Get-CurrentRhythm {
    $hour = (Get-Date).Hour
    
    # 시간대 기반 기본 리듬
    $timeRhythm = if ($hour -ge 6 -and $hour -lt 10) {
        "MORNING"
    }
    elseif ($hour -ge 10 -and $hour -lt 14) {
        "DAYTIME_FOCUS"
    }
    elseif ($hour -ge 14 -and $hour -lt 18) {
        "DAYTIME_FLOW"
    }
    elseif ($hour -ge 18 -and $hour -lt 22) {
        "EVENING"
    }
    else {
        "NIGHT"
    }
    
    # 시스템 상태 확인
    $cpu = 0
    $memPercent = 0
    try {
        $cpu = (Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue).CounterSamples[0].CookedValue
        $memPercent = (Get-WmiObject Win32_OperatingSystem | Select-Object @{Name = "MemoryUsage"; Expression = { [math]::Round(($_.TotalVisibleMemorySize - $_.FreePhysicalMemory) / $_.TotalVisibleMemorySize * 100, 2) } }).MemoryUsage
    }
    catch {}
    
    # 큐 상태 확인
    $queueSize = 0
    $queueStatus = "OFFLINE"
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/queue/status" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $queueSize = $response.queue_size
        $queueStatus = "ONLINE"
    }
    catch {}
    
    # 상태 기반 조정
    $stateModifier = "NORMAL"
    if ($cpu -gt 80 -or $memPercent -gt 85) {
        $stateModifier = "BUSY"
    }
    elseif ($queueSize -gt 50) {
        $stateModifier = "EMERGENCY"
    }
    
    # 에너지 레벨 계산 (0-100)
    $energyLevel = 100
    if ($timeRhythm -eq "MORNING") {
        $energyLevel = 85  # 높은 에너지
    }
    elseif ($timeRhythm -eq "DAYTIME_FOCUS") {
        $energyLevel = 100  # 최고 에너지
    }
    elseif ($timeRhythm -eq "DAYTIME_FLOW") {
        $energyLevel = 90  # 여전히 높음
    }
    elseif ($timeRhythm -eq "EVENING") {
        $energyLevel = 60  # 감소 중
    }
    else {
        $energyLevel = 30  # 휴식 모드
    }
    
    # 상태에 따라 에너지 조정
    if ($stateModifier -eq "BUSY") {
        $energyLevel = [math]::Max(50, $energyLevel - 20)
    }
    elseif ($stateModifier -eq "EMERGENCY") {
        $energyLevel = [math]::Max(30, $energyLevel - 40)
    }
    
    return @{
        TimeRhythm    = $timeRhythm
        StateModifier = $stateModifier
        Hour          = $hour
        CPU           = [math]::Round($cpu, 1)
        Memory        = $memPercent
        QueueSize     = $queueSize
        QueueStatus   = $queueStatus
        EnergyLevel   = $energyLevel
        Timestamp     = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
}

# 리듬별 권장 작업
$rhythmRecommendations = @{
    MORNING       = @{
        Description = "🌅 아침: 시스템 체크 & 준비"
        Tasks       = @(
            "Morning: Kickoff (1h, open)",
            "System: Health Check (Quick)",
            "AGI: Quick Health Check (fast)",
            "Lumen: Quick Health Probe",
            "Queue: Ensure Server (8091)",
            "Watchdog: Start Task Watchdog (Background)"
        )
    }
    
    DAYTIME_FOCUS = @{
        Description = "☀️ 낮 (집중): 개발 & 테스트"
        Tasks       = @(
            "Python: Run All Tests (repo venv)",
            "Dev: Local CI Check (Fast)",
            "Queue: Quick E2E (Ensure Server+Worker)",
            "Integration: Run Gitko E2E Test"
        )
    }
    
    DAYTIME_FLOW  = @{
        Description = "🌊 낮 (흐름): 분석 & 모니터링"
        Tasks       = @(
            "Monitoring: Unified Dashboard (AGI + Lumen)",
            "Realtime: Summarize + Open",
            "YouTube: Build Index (open)",
            "Autopoietic: Generate Loop Report (24h)"
        )
    }
    
    EVENING       = @{
        Description = "🌆 저녁: 정리 & 백업"
        Tasks       = @(
            "🔄 Trinity: Autopoietic Cycle (24h, open)",
            "Monitoring: Generate Report (24h) + Open",
            "End of Day: Backup",
            "Monitoring: Rotate Snapshots (zip if needed)"
        )
    }
    
    NIGHT         = @{
        Description = "🌙 밤: 학습 & 최적화"
        Tasks       = @(
            "BQI: Run Phase 6 (Full Pipeline)",
            "🔄 Trinity: Autopoietic Cycle (24h, open)",
            "Python: Coverage HTML (generate)",
            "🤖 AI: Bootstrap Self-Managing System (Once)"
        )
    }
}

$rhythm = Get-CurrentRhythm

if ($Json) {
    $rhythm | ConvertTo-Json -Depth 5
    exit 0
}

# 콘솔 출력
Write-Host ""
Write-Host "=== 🎵 Current System Rhythm ===" -ForegroundColor Cyan
Write-Host ""

$timeColor = switch ($rhythm.TimeRhythm) {
    "MORNING" { "Yellow" }
    "DAYTIME_FOCUS" { "Green" }
    "DAYTIME_FLOW" { "Cyan" }
    "EVENING" { "Magenta" }
    "NIGHT" { "Blue" }
    default { "White" }
}

Write-Host "Time Rhythm:    " -NoNewline
Write-Host "$($rhythm.TimeRhythm)" -ForegroundColor $timeColor

$stateColor = switch ($rhythm.StateModifier) {
    "EMERGENCY" { "Red" }
    "BUSY" { "Yellow" }
    "NORMAL" { "Green" }
    default { "White" }
}

Write-Host "State Modifier: " -NoNewline
Write-Host "$($rhythm.StateModifier)" -ForegroundColor $stateColor

Write-Host ""
Write-Host "⏰ Time:         $($rhythm.Hour):00" -ForegroundColor Gray
Write-Host "⚡ Energy:       $($rhythm.EnergyLevel)%" -ForegroundColor $(if ($rhythm.EnergyLevel -ge 80) { "Green" } elseif ($rhythm.EnergyLevel -ge 50) { "Yellow" } else { "Red" })
Write-Host "🖥️  CPU:          $($rhythm.CPU)%" -ForegroundColor Gray
Write-Host "💾 Memory:       $($rhythm.Memory)%" -ForegroundColor Gray
Write-Host "📋 Queue:        $($rhythm.QueueSize) ($($rhythm.QueueStatus))" -ForegroundColor Gray

Write-Host ""
Write-Host "=== 📋 Recommended Tasks ===" -ForegroundColor Cyan
Write-Host ""

$recommendation = $rhythmRecommendations[$rhythm.TimeRhythm]
Write-Host $recommendation.Description -ForegroundColor Yellow
Write-Host ""

foreach ($task in $recommendation.Tasks) {
    Write-Host "  • $task" -ForegroundColor White
}

Write-Host ""
Write-Host "=== 🧬 리듬=에너지=시간=관계 ===" -ForegroundColor Cyan
Write-Host ""

$philosophy = switch ($rhythm.TimeRhythm) {
    "MORNING" { "새로운 시작, 시스템 준비, 관계 확인" }
    "DAYTIME_FOCUS" { "최고 에너지, 집중 작업, 생산성" }
    "DAYTIME_FLOW" { "안정적 흐름, 모니터링, 유지" }
    "EVENING" { "정리와 회고, 백업, 내일 준비" }
    "NIGHT" { "휴식과 학습, 최적화, 자기 개선" }
}

Write-Host $philosophy -ForegroundColor Gray
Write-Host ""

# 메타데이터 저장
$outputPath = "C:\workspace\agi\outputs\current_rhythm.json"
$rhythm | ConvertTo-Json -Depth 5 | Out-File -FilePath $outputPath -Encoding UTF8 -Force

Write-Host "💾 Rhythm saved to: $outputPath" -ForegroundColor Gray
