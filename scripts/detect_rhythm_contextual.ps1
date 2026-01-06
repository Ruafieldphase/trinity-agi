#Requires -Version 5.1
<#
.SYNOPSIS
    Contextual Rhythm Detector - 맥락 기반 리듬 감지
.DESCRIPTION
    절대적 시간이 아닌, 시스템 맥락을 고려한 진짜 리듬 감지
    
    핵심 철학: "리듬=에너지=시간=관계는 맥락에 따라 달라진다"
    
    맥락 요소:
    1. 마지막 휴식 이후 경과 시간
    2. 최근 작업 강도 (누적 부하)
    3. 시스템 건강 상태
    4. 큐 압력 (외부 요구)
    5. 최근 이벤트 이력
#>

param(
    [switch]$Json,
    [switch]$Verbose
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$workspaceRoot = "$WorkspaceRoot"

# ========================================
# 1. 맥락 데이터 수집
# ========================================

function Get-SystemContext {
    $context = @{
        Timestamp = (Get-Date)
        ClockTime = (Get-Date).Hour
    }
    
    # 1.1 최근 활동 이력 (Resonance Ledger)
    $ledgerPath = "$workspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl"
    $recentActivity = @{
        LastActivity   = $null
        ActivityCount  = 0
        AvgLatency     = 0
        HighLoadPeriod = $false
    }
    
    if (Test-Path $ledgerPath) {
        try {
            $recent = Get-Content $ledgerPath -Tail 100 -ErrorAction SilentlyContinue | 
            ForEach-Object { $_ | ConvertFrom-Json } |
            Where-Object { $_.timestamp -ne $null }
            
            if ($recent) {
                $recentActivity.ActivityCount = $recent.Count
                $recentActivity.LastActivity = ($recent | Select-Object -Last 1).timestamp
                
                # 평균 레이턴시 계산
                $latencies = $recent | Where-Object { $_.latency -ne $null } | Select-Object -ExpandProperty latency
                if ($latencies) {
                    $recentActivity.AvgLatency = ($latencies | Measure-Object -Average).Average
                }
                
                # 고부하 기간 판단 (최근 100개 중 70개 이상이 높은 레이턴시)
                $highLatencyCount = ($recent | Where-Object { $_.latency -gt 5 }).Count
                $recentActivity.HighLoadPeriod = $highLatencyCount -gt 70
            }
        }
        catch {
            if ($Verbose) { Write-Warning "Ledger read failed: $_" }
        }
    }
    
    # 1.2 시스템 리소스 현황
    $resources = @{
        CPU    = 0
        Memory = 0
        DiskIO = 0
    }
    
    try {
        $resources.CPU = [math]::Round((Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue).CounterSamples[0].CookedValue, 1)
        $os = Get-WmiObject Win32_OperatingSystem
        $resources.Memory = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize * 100, 2)
    }
    catch {
        if ($Verbose) { Write-Warning "Resource check failed: $_" }
    }
    
    # 1.3 큐 상태 (외부 압력)
    $queuePressure = @{
        Size    = 0
        Status  = "OFFLINE"
        Pending = 0
        Failed  = 0
    }
    
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/queue/status" -TimeoutSec 2 -ErrorAction SilentlyContinue
        $queuePressure.Size = $response.queue_size
        $queuePressure.Status = "ONLINE"
        $queuePressure.Pending = $response.pending_count
        $queuePressure.Failed = $response.failed_count
    }
    catch {
        if ($Verbose) { Write-Warning "Queue check failed: $_" }
    }
    
    # 1.4 최근 휴식 시간 추정
    $lastRestTime = $null
    $hoursSinceRest = 24  # 기본값: 알 수 없으면 24시간으로 가정
    
    # Monitoring 이벤트에서 마지막 "quiet period" 찾기
    $monitoringCsv = "$workspaceRoot\outputs\monitoring_events_latest.csv"
    if (Test-Path $monitoringCsv) {
        try {
            $events = Import-Csv $monitoringCsv -ErrorAction SilentlyContinue |
            Where-Object { $_.Timestamp -ne $null } |
            ForEach-Object { 
                $_ | Add-Member -MemberType NoteProperty -Name ParsedTime -Value ([datetime]::Parse($_.Timestamp)) -PassThru -Force
            }
            
            # 마지막 활동 찾기 (Activity 이벤트)
            $lastEvent = $events | Where-Object { $_.Category -eq "Activity" } | Sort-Object ParsedTime -Descending | Select-Object -First 1
            if ($lastEvent) {
                $hoursSinceRest = ((Get-Date) - $lastEvent.ParsedTime).TotalHours
                $lastRestTime = $lastEvent.ParsedTime
            }
        }
        catch {
            if ($Verbose) { Write-Warning "Rest time estimation failed: $_" }
        }
    }
    
    $context.RecentActivity = $recentActivity
    $context.Resources = $resources
    $context.QueuePressure = $queuePressure
    $context.HoursSinceRest = [math]::Round($hoursSinceRest, 1)
    $context.LastRestTime = $lastRestTime
    
    return $context
}

# ========================================
# 2. 맥락 기반 에너지 계산
# ========================================

function Get-ContextualEnergy {
    param($context)
    
    $baseEnergy = 100
    
    # 2.1 시계 시간 기반 기본 에너지
    $hourFactor = switch ($context.ClockTime) {
        { $_ -ge 6 -and $_ -lt 10 } { 0.85 }   # 아침
        { $_ -ge 10 -and $_ -lt 14 } { 1.0 }   # 한낮
        { $_ -ge 14 -and $_ -lt 18 } { 0.9 }   # 오후
        { $_ -ge 18 -and $_ -lt 22 } { 0.6 }   # 저녁
        default { 0.3 }                         # 밤
    }
    
    $energy = $baseEnergy * $hourFactor
    
    # 2.2 휴식 이후 경과 시간 (피로도 누적)
    if ($context.HoursSinceRest -lt 2) {
        # 방금 휴식 → 에너지 충전
        $energy += 15
    }
    elseif ($context.HoursSinceRest -gt 8) {
        # 8시간 이상 작업 → 피로 누적
        $fatiguePenalty = [math]::Min(40, ($context.HoursSinceRest - 8) * 5)
        $energy -= $fatiguePenalty
    }
    
    # 2.3 최근 작업 강도 (고부하 기간)
    if ($context.RecentActivity.HighLoadPeriod) {
        $energy -= 25  # 고부하 작업 후 에너지 소모
    }
    
    # 2.4 시스템 리소스 압박
    $cpuPenalty = if ($context.Resources.CPU -gt 80) { 20 } elseif ($context.Resources.CPU -gt 60) { 10 } else { 0 }
    $memPenalty = if ($context.Resources.Memory -gt 85) { 15 } elseif ($context.Resources.Memory -gt 70) { 5 } else { 0 }
    $energy -= ($cpuPenalty + $memPenalty)
    
    # 2.5 큐 압력 (외부 요구)
    if ($context.QueuePressure.Size -gt 100) {
        $energy -= 30  # 긴급 상황
    }
    elseif ($context.QueuePressure.Size -gt 50) {
        $energy -= 15  # 바쁜 상태
    }
    
    # 2.6 범위 제한
    $energy = [math]::Max(10, [math]::Min(100, $energy))
    
    return [math]::Round($energy, 0)
}

# ========================================
# 3. 맥락 기반 리듬 결정
# ========================================

function Get-ContextualRhythm {
    param($context, $energy)
    
    # 긴급 상황 우선
    if ($context.QueuePressure.Size -gt 100 -or $context.QueuePressure.Failed -gt 50) {
        return @{
            Name        = "EMERGENCY"
            Description = "🚨 긴급: 즉각 대응 필요"
            Color       = "Red"
            Reason      = "Queue overload or high failure rate"
        }
    }
    
    # 회복 필요 (에너지 < 40 또는 고부하 직후)
    if ($energy -lt 40 -or ($context.RecentActivity.HighLoadPeriod -and $energy -lt 60)) {
        return @{
            Name        = "RECOVERY"
            Description = "🛌 회복: 휴식 및 모니터링만"
            Color       = "Magenta"
            Reason      = "Low energy ($energy%) or post-high-load recovery"
        }
    }
    
    # 에너지 기반 리듬
    if ($energy -ge 85) {
        return @{
            Name        = "PEAK"
            Description = "⚡ 최고: 집중 작업 & 도전"
            Color       = "Green"
            Reason      = "High energy ($energy%)"
        }
    }
    elseif ($energy -ge 70) {
        return @{
            Name        = "FLOW"
            Description = "🌊 흐름: 안정적 생산"
            Color       = "Cyan"
            Reason      = "Good energy ($energy%)"
        }
    }
    elseif ($energy -ge 50) {
        return @{
            Name        = "STEADY"
            Description = "📊 안정: 유지 및 모니터링"
            Color       = "Yellow"
            Reason      = "Moderate energy ($energy%)"
        }
    }
    else {
        return @{
            Name        = "REST"
            Description = "💤 휴식: 자동화 작업만"
            Color       = "Blue"
            Reason      = "Low energy ($energy%)"
        }
    }
}

# ========================================
# 4. 권장 작업 매핑
# ========================================

$rhythmTasks = @{
    EMERGENCY = @(
        "Queue: Health Check",
        "System: Health Check (Quick)",
        "Recover: Auto-Recover (one-shot)",
        "Watchdog: Check Task Watchdog Status"
    )
    
    RECOVERY  = @(
        "Monitoring: Unified Dashboard (AGI + Core)",
        "Queue: Latest Results (Success 5)",
        "System: Health Check (Quick)",
        "Core: Quick Health Probe"
    )
    
    PEAK      = @(
        "Python: Run All Tests (repo venv)",
        "Dev: Local CI Check (Full)",
        "Integration: Run Gitko E2E Test",
        "🔄 Trinity: Autopoietic Cycle (24h, open)"
    )
    
    FLOW      = @(
        "Queue: Quick E2E (Ensure Server+Worker)",
        "Realtime: Summarize + Open",
        "YouTube: Build Index (open)",
        "Monitoring: Generate Report (24h) + Open"
    )
    
    STEADY    = @(
        "Monitoring: Unified Dashboard (AGI + Core)",
        "Queue: Health Check",
        "Autopoietic: Generate Loop Report (24h)",
        "Original Data: Build Index (open)"
    )
    
    REST      = @(
        "BQI: Run Phase 6 (Full Pipeline)",
        "Python: Coverage HTML (generate)",
        "🕒 Trinity: Register Auto-Run (03:30)",
        "Monitoring: Register Collector (5m)"
    )
}

# ========================================
# 5. 메인 로직
# ========================================

Write-Host ""
Write-Host "=== 🧬 Contextual Rhythm Detector ===" -ForegroundColor Cyan
Write-Host "    리듬=에너지=시간=관계 (맥락 기반)" -ForegroundColor Gray
Write-Host ""

# 맥락 수집
if ($Verbose) { Write-Host "Collecting context..." -ForegroundColor Gray }
$context = Get-SystemContext

# 에너지 계산
$energy = Get-ContextualEnergy -context $context

# 리듬 결정
$rhythm = Get-ContextualRhythm -context $context -energy $energy

# JSON 출력
if ($Json) {
    @{
        Timestamp        = $context.Timestamp.ToString("yyyy-MM-dd HH:mm:ss")
        Context          = $context
        Energy           = $energy
        Rhythm           = $rhythm
        RecommendedTasks = $rhythmTasks[$rhythm.Name]
    } | ConvertTo-Json -Depth 10
    exit 0
}

# 콘솔 출력
Write-Host "Current Rhythm: " -NoNewline
Write-Host $rhythm.Name -ForegroundColor $rhythm.Color

Write-Host "Description:    " -NoNewline
Write-Host $rhythm.Description -ForegroundColor $rhythm.Color

Write-Host ""
Write-Host "=== 📊 Context Analysis ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "⏰ Clock Time:        $($context.ClockTime):00" -ForegroundColor Gray
Write-Host "⚡ Energy Level:      $energy%" -ForegroundColor $(if ($energy -ge 70) { "Green" } elseif ($energy -ge 40) { "Yellow" } else { "Red" })
Write-Host "💤 Hours Since Rest:  $($context.HoursSinceRest)h" -ForegroundColor Gray
Write-Host "🖥️  CPU:               $($context.Resources.CPU)%" -ForegroundColor Gray
Write-Host "💾 Memory:            $($context.Resources.Memory)%" -ForegroundColor Gray
Write-Host "📋 Queue:             $($context.QueuePressure.Size) ($($context.QueuePressure.Status))" -ForegroundColor Gray

if ($context.RecentActivity.HighLoadPeriod) {
    Write-Host "⚠️  Recent High Load:  YES" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Reason: $($rhythm.Reason)" -ForegroundColor DarkGray

Write-Host ""
Write-Host "=== 📋 Recommended Tasks ===" -ForegroundColor Cyan
Write-Host ""

foreach ($task in $rhythmTasks[$rhythm.Name]) {
    Write-Host "  • $task" -ForegroundColor White
}

Write-Host ""
Write-Host "=== 💡 Key Insight ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "리듬은 절대적 시간이 아닌 '맥락'으로 결정됩니다." -ForegroundColor Yellow
Write-Host "같은 오후 1시여도 밤샘 후면 RECOVERY, 휴식 후면 PEAK입니다." -ForegroundColor Yellow
Write-Host ""

# 메타데이터 저장
$outputPath = "$workspaceRoot\outputs\contextual_rhythm.json"
@{
    Timestamp        = $context.Timestamp.ToString("yyyy-MM-dd HH:mm:ss")
    Context          = $context
    Energy           = $energy
    Rhythm           = $rhythm
    RecommendedTasks = $rhythmTasks[$rhythm.Name]
} | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputPath -Encoding UTF8 -Force

Write-Host "💾 Context saved to: $outputPath" -ForegroundColor Gray
Write-Host ""