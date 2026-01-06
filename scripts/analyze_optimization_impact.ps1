#Requires -Version 5.1
<#$
.SYNOPSIS
    Gateway 최적화 효과 분석 - Before/After 비교
.DESCRIPTION
    Task 1 기준선과 최적화 이후의 레이턴시/품질 변화를 비교합니다.
    baseline JSON이 세부 지연 수치를 포함하지 않는 경우에도
    레조넌스 레저( fdo_agi_repo/memory/resonance_ledger.jsonl )를 이용해
    Baseline/After 윈도우의 정책 이벤트를 집계합니다.
.PARAMETER BaselineFile
    Task 1 기준선 데이터 (JSON)
.PARAMETER OptimizedFile
    최적화 로그 파일 (JSONL)
.PARAMETER OutMarkdown
    결과 리포트 (Markdown)
.PARAMETER BaselineHours
    Baseline으로 삼을 시간 범위 (최적화 시작 이전, 기본 6시간)
.PARAMETER PostHours
    최적화 이후 비교 대상 시간 범위 (기본 6시간)
.PARAMETER PeakStart
    피크 시간 시작 시각 (24h 기준)
.PARAMETER PeakEnd
    피크 시간 종료 시각 (24h 기준)
.EXAMPLE
    .\analyze_optimization_impact.ps1
#>

param(
    [string]$BaselineFile = "outputs\network_profile_latest.json",
    [string]$OptimizedFile = "outputs\gateway_optimization_log.jsonl",
    [string]$OutMarkdown = "outputs\optimization_impact_report.md",
    [int]$BaselineHours = 6,
    [int]$PostHours = 6,
    [int]$PeakStart = 8,
    [int]$PeakEnd = 16
)

$ErrorActionPreference = 'Stop'
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

Write-Host "`n=== Gateway 최적화 효과 분석 ===`n" -ForegroundColor Cyan

# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------
function New-EmptyStats {
    return [ordered]@{
        count          = 0
        mean           = "N/A"
        p50            = "N/A"
        p95            = "N/A"
        std            = "N/A"
        warn_ratio     = "N/A"
        block_ratio    = "N/A"
        quality_mean   = "N/A"
        evidence_ratio = "N/A"
        peak           = [ordered]@{ count = 0; mean = "N/A"; p95 = "N/A" }
        offpeak        = [ordered]@{ count = 0; mean = "N/A"; p95 = "N/A" }
    }
}

function Get-PeakFlag {
    param(
        [datetime]$Timestamp,
        [int]$PeakStart,
        [int]$PeakEnd
    )
    $hour = $Timestamp.Hour
    if ($PeakStart -eq $PeakEnd) { return $true }
    if ($PeakStart -lt $PeakEnd) {
        return ($hour -ge $PeakStart -and $hour -lt $PeakEnd)
    }
    else {
        # Wrap-around (예: 20~04)
        return ($hour -ge $PeakStart -or $hour -lt $PeakEnd)
    }
}

function Get-LatencyStats {
    param(
        [object[]]$Events,
        [int]$PeakStart,
        [int]$PeakEnd
    )
    $stats = New-EmptyStats
    if (-not $Events -or $Events.Count -eq 0) { return $stats }

    $latEvents = @($Events | Where-Object { $_.observed -and $_.observed.latency_ms -ne $null })
    if ($latEvents.Count -eq 0) { return $stats }

    $latencies = @($latEvents | ForEach-Object { [double]$_.observed.latency_ms })

    $stats.count = $latencies.Count
    $stats.mean = [Math]::Round(($latencies | Measure-Object -Average).Average, 2)
    $sorted = $latencies | Sort-Object
    $stats.p50 = [Math]::Round($sorted[[Math]::Floor(($sorted.Count - 1) * 0.5)], 2)
    $stats.p95 = [Math]::Round($sorted[[Math]::Floor(($sorted.Count - 1) * 0.95)], 2)

    if ($latencies.Count -gt 1) {
        $avg = $stats.mean
        $variance = ($latencies | ForEach-Object { ([math]::Pow($_ - $avg, 2)) }) | Measure-Object -Sum
        $stats.std = [Math]::Round([Math]::Sqrt($variance.Sum / ($latencies.Count)), 2)
    }

    # 비율
    $warnCount = ($Events | Where-Object { $_.action -eq 'warn' }).Count
    $blockCount = ($Events | Where-Object { $_.action -eq 'block' }).Count
    if ($Events.Count -gt 0) {
        $stats.warn_ratio = [Math]::Round(($warnCount / $Events.Count) * 100, 1)
        $stats.block_ratio = [Math]::Round(($blockCount / $Events.Count) * 100, 1)
    }

    $qualityValues = @($latEvents | Where-Object { $_.observed.quality -ne $null } | ForEach-Object { [double]$_.observed.quality })
    if ($qualityValues.Count -gt 0) {
        $stats.quality_mean = [Math]::Round(($qualityValues | Measure-Object -Average).Average, 3)
    }

    $evidenceOk = ($latEvents | Where-Object { $_.observed.evidence_ok -eq $true }).Count
    if ($latEvents.Count -gt 0) {
        $stats.evidence_ratio = [Math]::Round(($evidenceOk / $latEvents.Count) * 100, 1)
    }

    $peakEvents = @($latEvents | Where-Object { Get-PeakFlag -Timestamp $_.LocalTimestamp -PeakStart $PeakStart -PeakEnd $PeakEnd })
    $offEvents = @($latEvents | Where-Object { -not (Get-PeakFlag -Timestamp $_.LocalTimestamp -PeakStart $PeakStart -PeakEnd $PeakEnd) })

    if ($peakEvents.Count -gt 0) {
        $peakLat = @($peakEvents | ForEach-Object { [double]$_.observed.latency_ms }) | Sort-Object
        $stats.peak.count = $peakLat.Count
        $stats.peak.mean = [Math]::Round(($peakLat | Measure-Object -Average).Average, 2)
        $stats.peak.p95 = [Math]::Round($peakLat[[Math]::Floor(($peakLat.Count - 1) * 0.95)], 2)
    }
    if ($offEvents.Count -gt 0) {
        $offLat = @($offEvents | ForEach-Object { [double]$_.observed.latency_ms }) | Sort-Object
        $stats.offpeak.count = $offLat.Count
        $stats.offpeak.mean = [Math]::Round(($offLat | Measure-Object -Average).Average, 2)
        $stats.offpeak.p95 = [Math]::Round($offLat[[Math]::Floor(($offLat.Count - 1) * 0.95)], 2)
    }

    return $stats
}

function Format-Value {
    param($Value, $Suffix)
    if ($Value -is [double]) { return "{0}{1}" -f $Value, $Suffix }
    return "$Value"
}

function Format-TableRow {
    param($Name, $BaselineValue, $AfterValue)
    return "| $Name | $BaselineValue | $AfterValue |"
}

# ------------------------------------------------------------
# Baseline 정보
# ------------------------------------------------------------
if (-not (Test-Path $BaselineFile)) {
    Write-Host "❌ Baseline file not found: $BaselineFile" -ForegroundColor Red
    Write-Host "   Run Task 1 first to generate baseline" -ForegroundColor Yellow
    exit 1
}

$Baseline = Get-Content $BaselineFile -Raw | ConvertFrom-Json
Write-Host "✅ Baseline loaded: $BaselineFile"

# ------------------------------------------------------------
# 최적화 로그
# ------------------------------------------------------------
if (-not (Test-Path $OptimizedFile)) {
    Write-Host "❌ Optimization log not found: $OptimizedFile" -ForegroundColor Red
    Write-Host "   Run optimization first" -ForegroundColor Yellow
    exit 1
}

$OptimizationLog = @(Get-Content $OptimizedFile | ForEach-Object { $_ | ConvertFrom-Json })
$logCount = $OptimizationLog.Count
if ($logCount -le 0) {
    Write-Host "⚠️ Optimization log has no entries." -ForegroundColor Yellow
}
Write-Host "✅ Optimization log loaded: $logCount entries" -ForegroundColor Green
Write-Host ""

$Report = [ordered]@{
    timestamp       = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    baseline        = [ordered]@{
        date               = $Baseline.timestamp
        peak_latency_ms    = "N/A"
        offpeak_latency_ms = "N/A"
        std_dev            = "N/A"
    }
    optimization    = [ordered]@{
        entries          = $logCount
        start_time       = "N/A"
        end_time         = "N/A"
        duration_minutes = "N/A"
    }
    policy_baseline = New-EmptyStats
    policy_after    = New-EmptyStats
    improvement     = [ordered]@{}
}

if ($logCount -gt 0) {
    try {
        $Report.optimization.start_time = $OptimizationLog[0].timestamp
        $Report.optimization.end_time = $OptimizationLog[-1].timestamp
        $startTs = [DateTime]::Parse($Report.optimization.start_time)
        $endTs = [DateTime]::Parse($Report.optimization.end_time)
        $Report.optimization.duration_minutes = [Math]::Round(($endTs - $startTs).TotalMinutes, 1)
    }
    catch {
        $Report.optimization.duration_minutes = "N/A"
    }
}

# ------------------------------------------------------------
# 레저 기반 정책 이벤트 집계
# ------------------------------------------------------------
$ResonanceLedgerPath = "fdo_agi_repo/memory/resonance_ledger.jsonl"
$policyEvents = @()
if (Test-Path $ResonanceLedgerPath) {
    Write-Host "📥 Loading resonance ledger for policy events..." -ForegroundColor Cyan
    $epoch = [DateTime]::new(1970, 1, 1, 0, 0, 0, 0, [System.DateTimeKind]::Utc)
    Get-Content $ResonanceLedgerPath | ForEach-Object {
        try {
            if ([string]::IsNullOrWhiteSpace($_)) { return }
            $entry = $_ | ConvertFrom-Json
            if ($entry.event -ne "resonance_policy") { return }
            if ($entry.ts -eq $null) { return }
            $unix = [double]$entry.ts
            $entry | Add-Member -NotePropertyName LocalTimestamp -NotePropertyValue ($epoch.AddSeconds($unix).ToLocalTime()) -Force
            $policyEvents += $entry
        }
        catch {}
    }
}
else {
    Write-Host "⚠️ Resonance ledger not found: $ResonanceLedgerPath" -ForegroundColor Yellow
}

if ($policyEvents.Count -gt 0) {
    $epoch = [DateTime]::new(1970, 1, 1, 0, 0, 0, 0, [System.DateTimeKind]::Utc)
    $optStartUtc = $null
    if ($logCount -gt 0) {
        try { $optStartUtc = [DateTime]::Parse($OptimizationLog[0].timestamp).ToUniversalTime() } catch {}
    }
    if (-not $optStartUtc) { $optStartUtc = (Get-Date).ToUniversalTime() }
    $optStartUnix = ($optStartUtc - $epoch).TotalSeconds

    $baselineStartUnix = $optStartUnix - ($BaselineHours * 3600)
    $postEndUnix = $optStartUnix + ($PostHours * 3600)

    $baselineEvents = @($policyEvents | Where-Object { $_.ts -lt $optStartUnix -and $_.ts -ge $baselineStartUnix })
    $postEvents = @($policyEvents | Where-Object { $_.ts -ge $optStartUnix -and $_.ts -le $postEndUnix })

    $Report.policy_baseline = Get-LatencyStats -Events $baselineEvents -PeakStart $PeakStart -PeakEnd $PeakEnd
    $Report.policy_after = Get-LatencyStats -Events $postEvents -PeakStart $PeakStart -PeakEnd $PeakEnd

    Write-Host "Baseline policy events: $($Report.policy_baseline.count)"
    Write-Host "After policy events:    $($Report.policy_after.count)"
}
else {
    Write-Host "⚠️ No resonance_policy events found in ledger." -ForegroundColor Yellow
}

if ($Report.policy_baseline.mean -is [double] -and $Report.policy_after.mean -is [double]) {
    $delta = [Math]::Round($Report.policy_after.mean - $Report.policy_baseline.mean, 2)
    $deltaPct = if ($Report.policy_baseline.mean -ne 0) {
        [Math]::Round(($delta / $Report.policy_baseline.mean) * 100, 2)
    }
    else { "N/A" }
    $Report.improvement.mean_delta = $delta
    $Report.improvement.mean_delta_percent = $deltaPct
}
if ($Report.policy_baseline.p95 -is [double] -and $Report.policy_after.p95 -is [double]) {
    $delta = [Math]::Round($Report.policy_after.p95 - $Report.policy_baseline.p95, 2)
    $deltaPct = if ($Report.policy_baseline.p95 -ne 0) {
        [Math]::Round(($delta / $Report.policy_baseline.p95) * 100, 2)
    }
    else { "N/A" }
    $Report.improvement.p95_delta = $delta
    $Report.improvement.p95_delta_percent = $deltaPct
}

# ------------------------------------------------------------
# 출력 요약
# ------------------------------------------------------------
Write-Host "📊 기준선 (Baseline):" -ForegroundColor White
Write-Host "  - Peak latency: $(Format-Value $Report.baseline.peak_latency_ms ' ms')" -ForegroundColor Gray
Write-Host "  - Off-peak latency: $(Format-Value $Report.baseline.offpeak_latency_ms ' ms')" -ForegroundColor Gray
Write-Host "  - Std dev: $(Format-Value $Report.baseline.std_dev '')" -ForegroundColor Gray
Write-Host ""

Write-Host "최적화 전략 적용:" -ForegroundColor White
$adaptivePercent = if ($logCount -gt 0) { [Math]::Round((($OptimizationLog | Where-Object { $_.strategies.adaptive_timeout.enabled -eq $true }).Count / $logCount) * 100, 1) } else { 0 }
$phasePercent = if ($logCount -gt 0) { [Math]::Round((($OptimizationLog | Where-Object { $_.strategies.phase_sync_scheduler.enabled -eq $true }).Count / $logCount) * 100, 1) } else { 0 }
Write-Host "  - Adaptive Timeout: $adaptivePercent%" -ForegroundColor Gray
Write-Host "  - Phase Sync: $phasePercent%" -ForegroundColor Gray
Write-Host ""

Write-Host "🎯 목표:" -ForegroundColor Cyan
Write-Host "  - Off-peak latency: $(Format-Value $Report.baseline.offpeak_latency_ms ' ms') → 210 ms" -ForegroundColor Gray
Write-Host "  - 목표 개선율: $(if ($Report.improvement.mean_delta_percent) { $Report.improvement.mean_delta_percent } else { 'N/A' })%" -ForegroundColor Gray
Write-Host ""

Write-Host "⏳ 현재 상태:" -ForegroundColor Yellow
Write-Host "  - 최적화 실행 중: $($Report.optimization.duration_minutes) minutes" -ForegroundColor Gray
Write-Host "  - 실시간 모니터링 진행 중" -ForegroundColor Gray
Write-Host ""

# ------------------------------------------------------------
# Markdown/JSON 리포트 생성
# ------------------------------------------------------------
$baselineStats = $Report.policy_baseline
$afterStats = $Report.policy_after
$offpeakBase = Format-Value $baselineStats.offpeak.mean ' ms'
$offpeakAfter = Format-Value $afterStats.offpeak.mean ' ms'

$Markdown = @"
# Gateway 최적화 효과 분석

생성일시: $($Report.timestamp)

## 📊 기준선 요약

- **측정일**: $($Report.baseline.date)
- **Peak latency**: $(Format-Value $Report.baseline.peak_latency_ms ' ms')
- **Off-peak latency**: $(Format-Value $Report.baseline.offpeak_latency_ms ' ms')
- **표준편차**: $(Format-Value $Report.baseline.std_dev '')

## 🔧 최적화 전략 적용

- Adaptive Timeout: $adaptivePercent%
- Phase Sync: $phasePercent%
- Off-peak 워밍업: $(if ($OptimizationLog | Where-Object { $_.strategies.off_peak_warmup.should_warmup -eq $true }) { '실행' } else { '대기/없음' })

## 📈 정책 이벤트 기반 레이턴시 비교

| 구분 | Baseline (최근 $BaselineHours h) | After (최신 $PostHours h) |
|------|-------------------------------|-----------------------------|
$(Format-TableRow '샘플 수' $($baselineStats.count) $($afterStats.count))
$(Format-TableRow '평균 지연 (ms)' $(Format-Value $baselineStats.mean ' ms') $(Format-Value $afterStats.mean ' ms'))
$(Format-TableRow 'p95 지연 (ms)' $(Format-Value $baselineStats.p95 ' ms') $(Format-Value $afterStats.p95 ' ms'))
$(Format-TableRow 'Warn 비율' $(Format-Value $baselineStats.warn_ratio ' %') $(Format-Value $afterStats.warn_ratio ' %'))
$(Format-TableRow 'Block 비율' $(Format-Value $baselineStats.block_ratio ' %') $(Format-Value $afterStats.block_ratio ' %'))
$(Format-TableRow '품질 평균' $(Format-Value $baselineStats.quality_mean '') $(Format-Value $afterStats.quality_mean ''))
$(Format-TableRow '증거 충족 비율' $(Format-Value $baselineStats.evidence_ratio ' %') $(Format-Value $afterStats.evidence_ratio ' %'))

### Peak vs Off-peak

| 구분 | Baseline Mean (ms) | After Mean (ms) | Baseline p95 | After p95 |
|------|-------------------|-----------------|-------------|-----------|
| Peak | $(Format-Value $baselineStats.peak.mean ' ms') | $(Format-Value $afterStats.peak.mean ' ms') | $(Format-Value $baselineStats.peak.p95 ' ms') | $(Format-Value $afterStats.peak.p95 ' ms') |
| Off-peak | $offpeakBase | $offpeakAfter | $(Format-Value $baselineStats.offpeak.p95 ' ms') | $(Format-Value $afterStats.offpeak.p95 ' ms') |

## 🎯 개선도

- 평균 지연 변화: $($Report.improvement.mean_delta) ms ($($Report.improvement.mean_delta_percent)% )
- P95 지연 변화: $($Report.improvement.p95_delta) ms ($($Report.improvement.p95_delta_percent)% )

## ⏳ 진행 상황

- **시작 시각**: $($Report.optimization.start_time)
- **현재 시각**: $($Report.timestamp)
- **실행 시간**: $($Report.optimization.duration_minutes) minutes
- **로그 엔트리**: $($Report.optimization.entries)

## 📝 다음 단계

1. 24시간 모니터링 완료 대기
2. 실측 레이턴시 데이터 수집
3. 기준선 대비 개선율 계산
4. Phase 8.5 완료 보고

---

*자동 생성: analyze_optimization_impact.ps1*
"@

$Markdown | Out-File -FilePath $OutMarkdown -Encoding UTF8
Write-Host "✅ 리포트 생성 완료: $OutMarkdown" -ForegroundColor Green

$Report | ConvertTo-Json -Depth 10 | Out-File -FilePath ($OutMarkdown -replace '\.md$', '.json') -Encoding UTF8
Write-Host "✅ JSON 저장 완료: $($OutMarkdown -replace '\.md$', '.json')" -ForegroundColor Green
Write-Host "`n============================================================`n" -ForegroundColor Cyan