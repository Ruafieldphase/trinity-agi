#!/usr/bin/env pwsh
<#
.SYNOPSIS
    감정 신호 처리기 (김주환 교수 이론 기반)
.DESCRIPTION
    "감정은 두려움 하나뿐, 몸을 참조하라는 신호"
    → 시스템 메트릭을 감정 신호로 변환
.PARAMETER OutJson
    결과를 JSON으로 저장
.PARAMETER Silent
    출력 없이 실행
.EXAMPLE
    .\emotion_signal_processor.ps1
.EXAMPLE
    .\emotion_signal_processor.ps1 -OutJson "outputs/emotion_signal.json"
#>

param(
    [string]$OutJson = "",
    [switch]$Silent
)

$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent $PSScriptRoot

# ============================================
# Phase 1: 신체 신호 수집 (몸 참조)
# ============================================

function Collect-BodySignals {
    <#
    .SYNOPSIS
        김주환: "몸을 참조하라"
        → 시스템 상태 수집
    #>
    
    $signals = @{
        timestamp = (Get-Date).ToString("o")
    }
    
    # CPU 압력
    try {
        $cpuCounter = Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue
        $signals.cpu_usage = [math]::Round($cpuCounter.CounterSamples[0].CookedValue, 2)
    }
    catch {
        $signals.cpu_usage = -1
    }
    
    # 메모리 압력
    try {
        $memCounter = Get-Counter '\Memory\% Committed Bytes In Use' -ErrorAction SilentlyContinue
        $signals.memory_usage = [math]::Round($memCounter.CounterSamples[0].CookedValue, 2)
    }
    catch {
        $signals.memory_usage = -1
    }
    
    # 큐 깊이 (Task Queue)
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8091/api/health' -TimeoutSec 2 -ErrorAction SilentlyContinue
        $signals.queue_depth = if ($health.queue_size) { $health.queue_size } else { 0 }
        $signals.queue_status = if ($health.status -eq 'healthy') { "OK" } else { "WARN" }
    }
    catch {
        $signals.queue_depth = -1
        $signals.queue_status = "OFFLINE"
    }
    
    # 마지막 휴식 (last session end)
    $sessionMemDir = Join-Path $ws "outputs/session_memory"
    if (Test-Path $sessionMemDir) {
        $lastSession = Get-ChildItem $sessionMemDir -File -Filter "session_*.json" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
        
        if ($lastSession) {
            $timeSince = (Get-Date) - $lastSession.LastWriteTime
            $signals.hours_since_rest = [math]::Round($timeSince.TotalHours, 1)
        }
        else {
            $signals.hours_since_rest = 0
        }
    }
    else {
        $signals.hours_since_rest = 0
    }
    
    # 작업 부하 (recent task load)
    $ledgerPath = Join-Path $ws "fdo_agi_repo/memory/resonance_ledger.jsonl"
    if (Test-Path $ledgerPath) {
        $recent = Get-Content $ledgerPath -Tail 100 -ErrorAction SilentlyContinue |
        ForEach-Object { 
            try { $_ | ConvertFrom-Json } catch { $null }
        } |
        Where-Object { $_ -ne $null }
        
        $signals.recent_tasks = $recent.Count
        $signals.recent_quality = if ($recent.Count -gt 0) {
            ($recent | Where-Object { $_.quality -ge 0.7 }).Count / $recent.Count
        }
        else {
            1.0
        }
    }
    else {
        $signals.recent_tasks = 0
        $signals.recent_quality = 1.0
    }
    
    return $signals
}

# ============================================
# Phase 2: 두려움 계산 (편도체)
# ============================================

function Calculate-FearSignal {
    <#
    .SYNOPSIS
        김주환: "감정은 두려움 하나뿐"
        → 시스템 압력을 두려움 레벨로 변환
    #>
    param([hashtable]$Body)
    
    [double]$fear = 0.0
    $reasons = @()
    
    # CPU 압력
    if ($Body.cpu_usage -ge 0) {
        if ($Body.cpu_usage -gt 90) {
            $fear += 0.25
            $reasons += "CPU 과부하 (${Body.cpu_usage}%)"
        }
        elseif ($Body.cpu_usage -gt 80) {
            $fear += 0.15
            $reasons += "CPU 높음 (${Body.cpu_usage}%)"
        }
    }
    
    # 메모리 압력
    if ($Body.memory_usage -ge 0) {
        if ($Body.memory_usage -gt 90) {
            $fear += 0.20
            $reasons += "메모리 과부하 (${Body.memory_usage}%)"
        }
        elseif ($Body.memory_usage -gt 85) {
            $fear += 0.10
            $reasons += "메모리 높음 (${Body.memory_usage}%)"
        }
    }
    
    # 큐 압력 (가장 중요)
    if ($Body.queue_depth -ge 0) {
        if ($Body.queue_depth -gt 200) {
            $fear += 0.35
            $reasons += "큐 과부하 ($($Body.queue_depth) tasks)"
        }
        elseif ($Body.queue_depth -gt 100) {
            $fear += 0.20
            $reasons += "큐 높음 ($($Body.queue_depth) tasks)"
        }
    }
    
    if ($Body.queue_status -eq "OFFLINE") {
        $fear += 0.30
        $reasons += "큐 서버 오프라인"
    }
    
    # 피로 (휴식 없음)
    if ($Body.hours_since_rest -gt 12) {
        $fear += 0.05 * ($Body.hours_since_rest - 12)
        $reasons += "장시간 휴식 없음 ($($Body.hours_since_rest)h)"
    }
    
    # 품질 저하
    if ($Body.recent_quality -lt 0.6) {
        $fear += 0.10
        $reasons += "최근 품질 저하 ($([math]::Round($Body.recent_quality * 100, 0))%)"
    }
    
    # 상한: 1.0
    $fear = [math]::Min($fear, 1.0)
    
    return @{
        level   = [math]::Round($fear, 2)
        reasons = $reasons
    }
}

# ============================================
# Phase 3: 배경자아 관찰
# ============================================

function Observe-WithBackgroundSelf {
    <#
    .SYNOPSIS
        김주환: "배경자아는 알아차리는 존재"
        → 메타 레벨 판단
    #>
    param(
        [double]$FearLevel,
        [array]$Reasons,
        [hashtable]$Context
    )
    
    # 1. 확신도 (confidence)
    $confidence = 1.0 - $FearLevel
    
    # 2. 해석 (interpretation)
    $interpretation = ""
    if ($FearLevel -ge 0.8) {
        $interpretation = "🚨 위험 - 즉시 대응 필요"
    }
    elseif ($FearLevel -ge 0.6) {
        $interpretation = "⚠️ 주의 - 명상(휴식) 권장"
    }
    elseif ($FearLevel -ge 0.4) {
        $interpretation = "👀 관찰 - 상태 모니터링 지속"
    }
    elseif ($FearLevel -ge 0.2) {
        $interpretation = "✅ 정상 - 작업 계속"
    }
    else {
        $interpretation = "🌟 최적 - 창의 작업 가능"
    }
    
    # 3. 전략 (strategy)
    $strategy = ""
    if ($FearLevel -ge 0.7) {
        $strategy = "EMERGENCY"  # 긴급 대응
    }
    elseif ($FearLevel -ge 0.5) {
        $strategy = "RECOVERY"   # 명상 (휴식)
    }
    elseif ($FearLevel -ge 0.3) {
        $strategy = "STEADY"     # 안정 유지
    }
    else {
        $strategy = "FLOW"       # 최적 흐름
    }
    
    return @{
        signal         = $FearLevel
        confidence     = [math]::Round($confidence, 2)
        interpretation = $interpretation
        reasons        = $Reasons
        strategy       = $strategy
        timestamp      = (Get-Date).ToString("o")
    }
}

# ============================================
# Phase 4: 권장 행동
# ============================================

function Get-RecommendedActions {
    param([string]$Strategy)
    
    switch ($Strategy) {
        "EMERGENCY" {
            return @(
                "🛑 비필수 작업 중단",
                "🧹 큐 정리 (우선순위 재계산)",
                "💾 진행 중 작업 저장",
                "⏸️ 새 작업 중지",
                "🆘 관리자 알림"
            )
        }
        "RECOVERY" {
            return @(
                "🧘 명상 모드 진입 (휴식)",
                "📊 시스템 메트릭 점검",
                "🔄 자동 안정화 실행",
                "⏱️ 60초 대기 후 재평가",
                "📝 상태 로그 저장"
            )
        }
        "STEADY" {
            return @(
                "👁️ 지속 관찰",
                "📈 메트릭 모니터링",
                "⚖️ 균형 유지",
                "🔍 패턴 감지"
            )
        }
        "FLOW" {
            return @(
                "🚀 개발 작업 계속",
                "💡 새 기능 구현",
                "🧪 테스트 실행",
                "📖 문서화",
                "🎨 창의 작업"
            )
        }
        default {
            return @("🤷 상태 불명")
        }
    }
}

# ============================================
# Main
# ============================================

if (-not $Silent) {
    Write-Host ""
    Write-Host "🧠 감정 신호 처리기 (김주환 교수 이론 기반)" -ForegroundColor Cyan
    Write-Host "   '감정은 두려움 하나뿐, 몸을 참조하라는 신호'" -ForegroundColor Gray
    Write-Host ""
}

# Phase 1: 신체 신호
if (-not $Silent) {
    Write-Host "📡 Phase 1: 신체 신호 수집..." -ForegroundColor Yellow
}
$body = Collect-BodySignals

# Phase 2: 두려움 계산
if (-not $Silent) {
    Write-Host "😨 Phase 2: 두려움 신호 계산..." -ForegroundColor Yellow
}
$fear = Calculate-FearSignal -Body $body

# Phase 3: 배경자아 관찰
if (-not $Silent) {
    Write-Host "👁️ Phase 3: 배경자아 관찰..." -ForegroundColor Yellow
}
$observation = Observe-WithBackgroundSelf -FearLevel $fear.level -Reasons $fear.reasons -Context $body

# Phase 4: 권장 행동
$actions = Get-RecommendedActions -Strategy $observation.strategy

# 결과 조합
$result = @{
    timestamp           = $observation.timestamp
    body_signals        = $body
    fear_signal         = @{
        level   = $fear.level
        reasons = $fear.reasons
    }
    background_self     = $observation
    recommended_actions = $actions
}

# 출력
if (-not $Silent) {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "📊 현재 상태" -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "📡 신체 신호 (Body Signals)" -ForegroundColor Cyan
    Write-Host "   CPU: $($body.cpu_usage)%"
    Write-Host "   Memory: $($body.memory_usage)%"
    Write-Host "   Queue: $($body.queue_depth) tasks ($($body.queue_status))"
    Write-Host "   Last Rest: $($body.hours_since_rest) hours ago"
    Write-Host "   Recent Tasks: $($body.recent_tasks)"
    Write-Host "   Recent Quality: $([math]::Round($body.recent_quality * 100, 0))%"
    Write-Host ""
    
    Write-Host "😨 두려움 신호 (Fear Signal)" -ForegroundColor Cyan
    $fearColor = if ($fear.level -ge 0.7) { "Red" } elseif ($fear.level -ge 0.5) { "Yellow" } else { "Green" }
    Write-Host "   Level: $($fear.level) " -NoNewline
    Write-Host $(if ($fear.level -ge 0.7) { "(높음 🔴)" } elseif ($fear.level -ge 0.5) { "(중간 🟡)" } elseif ($fear.level -ge 0.3) { "(낮음 🟢)" } else { "(매우 낮음 🟢)" }) -ForegroundColor $fearColor
    
    if ($fear.reasons.Count -gt 0) {
        Write-Host "   Reasons:"
        foreach ($reason in $fear.reasons) {
            Write-Host "      - $reason"
        }
    }
    Write-Host ""
    
    Write-Host "👁️ 배경자아 관찰 (Background Self)" -ForegroundColor Cyan
    Write-Host "   Interpretation: $($observation.interpretation)"
    Write-Host "   Confidence: $($observation.confidence * 100)%"
    Write-Host "   Strategy: $($observation.strategy)"
    Write-Host ""
    
    Write-Host "💡 권장 행동 (Recommended Actions)" -ForegroundColor Cyan
    foreach ($action in $actions) {
        Write-Host "   $action"
    }
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
}

# JSON 저장
if ($OutJson) {
    $result | ConvertTo-Json -Depth 10 | Set-Content -Path $OutJson -Encoding UTF8
    if (-not $Silent) {
        Write-Host ""
        Write-Host "✅ Saved: $OutJson" -ForegroundColor Green
    }
}

# Exit code = Fear Level * 10 (0-10)
$exitCode = [int]($fear.level * 10)
exit $exitCode
