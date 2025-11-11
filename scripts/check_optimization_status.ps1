#Requires -Version 5.1
<#
.SYNOPSIS
    Gateway 최적화 진행 상황 리포트

.DESCRIPTION
    현재 최적화 실행 상태와 적용된 전략을 리포트합니다.
#>

param()

$ErrorActionPreference = 'Stop'
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'

Write-Host "`n=== Gateway 최적화 진행 상황 ===" -ForegroundColor Cyan
Write-Host ""

# 최적화 로그 확인
$LogFile = "outputs\gateway_optimization_log.jsonl"
if (-not (Test-Path $LogFile)) {
    Write-Host "⏳ 최적화가 아직 시작되지 않았습니다" -ForegroundColor Yellow
    exit 0
}

$LogEntries = Get-Content $LogFile | ForEach-Object { $_ | ConvertFrom-Json }
if ($LogEntries -isnot [System.Collections.IEnumerable]) { $LogEntries = @($LogEntries) }
$entryCount = $LogEntries.Count
if ($entryCount -le 0) {
    Write-Host "⚠️ 최적화 로그는 존재하지만 유효한 엔트리가 없습니다." -ForegroundColor Yellow
    exit 0
}
Write-Host "✅ 최적화 로그: $entryCount entries" -ForegroundColor Green
Write-Host ""

# 최신 상태
$Latest = $LogEntries[-1]
if (-not $Latest) {
    Write-Host "⚠️ 로그에서 최신 엔트리를 찾을 수 없습니다." -ForegroundColor Yellow
    exit 0
}
Write-Host "📊 현재 상태 (최신 엔트리):" -ForegroundColor White
Write-Host "  - 시각: $($Latest.timestamp)" -ForegroundColor Gray
Write-Host "  - Phase: $($Latest.phase.ToUpper())" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔧 적용된 전략:" -ForegroundColor White
Write-Host ""

# 1. 적응적 타임아웃
$AT = $Latest.strategies.adaptive_timeout
Write-Host "  1️⃣  적응적 타임아웃" -ForegroundColor Yellow
Write-Host "     - 상태: $(if ($AT.enabled) { '✅ 활성화' } else { '❌ 비활성화' })" -ForegroundColor $(if ($AT.enabled) { 'Green' } else { 'Red' })
Write-Host "     - Timeout: $($AT.timeout_ms)ms" -ForegroundColor Gray
Write-Host "     - Retries: $($AT.retry_attempts)" -ForegroundColor Gray
Write-Host "     - Phase: $($AT.phase)" -ForegroundColor Gray
Write-Host ""

# 2. 위상 동기화
$PS = $Latest.strategies.phase_sync_scheduler
Write-Host "  2️⃣  위상 동기화 스케줄러" -ForegroundColor Yellow
Write-Host "     - 상태: $(if ($PS.enabled) { '✅ 활성화' } else { '❌ 비활성화' })" -ForegroundColor $(if ($PS.enabled) { 'Green' } else { 'Red' })
Write-Host "     - Concurrency: $($PS.concurrency)" -ForegroundColor Gray
Write-Host "     - 설명: $($PS.description)" -ForegroundColor Gray
Write-Host ""

# 3. 워밍업
$WU = $Latest.strategies.off_peak_warmup
Write-Host "  3️⃣  Off-peak 워밍업" -ForegroundColor Yellow
Write-Host "     - 상태: $(if ($WU.enabled) { '✅ 활성화' } else { '❌ 비활성화' })" -ForegroundColor $(if ($WU.enabled) { 'Green' } else { 'Red' })
Write-Host "     - 실행 필요: $(if ($WU.should_warmup) { '✅ 예' } else { '❌ 아니오' })" -ForegroundColor $(if ($WU.should_warmup) { 'Green' } else { 'Gray' })
Write-Host "     - 다음 스케줄: $($WU.next_schedule)" -ForegroundColor Gray
Write-Host ""

# 목표
Write-Host "🎯 Phase 8.5 목표:" -ForegroundColor Cyan
Write-Host "  - Off-peak latency: 280ms → 210ms (25% 개선)" -ForegroundColor Gray
Write-Host "  - 표준편차 감소: σ 388 → 50" -ForegroundColor Gray
Write-Host "  - Peak/Off-peak 차이 축소" -ForegroundColor Gray
Write-Host ""

# 시간 정보
$FirstEntry = $LogEntries[0]
$startStamp = $null
$latestStamp = $null
try { $startStamp = [DateTime]::Parse($FirstEntry.timestamp) } catch {}
try { $latestStamp = [DateTime]::Parse($Latest.timestamp) } catch {}
if ($startStamp -and $latestStamp) {
    $Duration = $latestStamp - $startStamp
    $elapsedMinutes = [math]::Round($Duration.TotalMinutes, 1)
} else {
    $elapsedMinutes = "N/A"
}
Write-Host "⏱️  실행 시간:" -ForegroundColor White
Write-Host "  - 시작: $($FirstEntry.timestamp)" -ForegroundColor Gray
Write-Host "  - 현재: $($Latest.timestamp)" -ForegroundColor Gray
Write-Host "  - 경과: $elapsedMinutes 분" -ForegroundColor Cyan
Write-Host ""

# 다음 단계
Write-Host "📝 다음 단계:" -ForegroundColor Magenta
Write-Host "  - 24시간 모니터링 계속" -ForegroundColor Gray
Write-Host "  - 실측 레이턴시 데이터 수집" -ForegroundColor Gray
Write-Host "  - Task 1 기준선과 비교 분석" -ForegroundColor Gray
Write-Host ""

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
