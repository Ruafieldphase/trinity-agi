# Enhance Metric Collection
# Core(合) 권장: 모든 주요 이벤트에 quality/latency 메트릭 추가

param(
    [switch]$AddQuality,
    [switch]$AddLatency,
    [switch]$DryRun
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

Write-Host "`n📊 Metric Collection Enhancement`n" -ForegroundColor Cyan
Write-Host "Core(合)의 권장: 정보 밀도 향상을 위한 메트릭 강화`n"

# 1. 현재 메트릭 커버리지 분석
Write-Host "[1/4] 현재 메트릭 커버리지 분석 중..." -ForegroundColor Yellow

$ledgerPath = "$WorkspaceRoot\fdo_agi_repo\memory\resonance_ledger.jsonl"
if (-not (Test-Path $ledgerPath)) {
    Write-Host "❌ Resonance ledger not found: $ledgerPath" -ForegroundColor Red
    exit 1
}

$recentEvents = Get-Content $ledgerPath -Tail 100 | ForEach-Object {
    try { $_ | ConvertFrom-Json } catch { $null }
} | Where-Object { $_ -ne $null }

$totalEvents = $recentEvents.Count
$withQuality = ($recentEvents | Where-Object { $_.quality -ne $null }).Count
$withLatency = ($recentEvents | Where-Object { $_.latency_ms -ne $null }).Count

$qualityCoverage = if ($totalEvents -gt 0) { [math]::Round(($withQuality / $totalEvents) * 100, 1) } else { 0 }
$latencyCoverage = if ($totalEvents -gt 0) { [math]::Round(($withLatency / $totalEvents) * 100, 1) } else { 0 }

Write-Host "   ✓ 총 이벤트: $totalEvents (최근 100개)" -ForegroundColor Green
Write-Host "   ✓ Quality 커버리지: $qualityCoverage% ($withQuality/$totalEvents)" -ForegroundColor $(if ($qualityCoverage -lt 50) { 'Yellow' } else { 'Green' })
Write-Host "   ✓ Latency 커버리지: $latencyCoverage% ($withLatency/$totalEvents)" -ForegroundColor $(if ($latencyCoverage -lt 50) { 'Yellow' } else { 'Green' })

# 2. 메트릭 추가 대상 이벤트 타입 식별
Write-Host "`n[2/4] 메트릭 추가 대상 이벤트 타입 식별..." -ForegroundColor Yellow

$eventTypes = $recentEvents | Group-Object -Property event_type | Sort-Object Count -Descending
$criticalTypes = @(
    'thesis_start', 'thesis_end',
    'antithesis_start', 'antithesis_end',
    'synthesis_start', 'synthesis_end',
    'binoche_decision', 'eval',
    'pipeline_e2e_complete'
)

$targetTypes = $eventTypes | Where-Object { $criticalTypes -contains $_.Name }
Write-Host "   ✓ 식별된 중요 이벤트 타입: $($targetTypes.Count)개" -ForegroundColor Green

foreach ($type in $targetTypes | Select-Object -First 5) {
    $withMetric = ($type.Group | Where-Object { $_.quality -ne $null -or $_.latency_ms -ne $null }).Count
    $coverage = [math]::Round(($withMetric / $type.Count) * 100, 0)
    Write-Host "     - $($type.Name): $coverage% ($withMetric/$($type.Count))" -ForegroundColor Cyan
}

# 3. 코드베이스에서 메트릭 추가 위치 찾기
Write-Host "`n[3/4] 코드베이스에서 메트릭 추가 위치 탐색..." -ForegroundColor Yellow

$scriptsToEnhance = @()

# Python 파일 검색
$pythonFiles = Get-ChildItem "$WorkspaceRoot\fdo_agi_repo" -Recurse -Filter "*.py" -ErrorAction SilentlyContinue |
Where-Object { $_.FullName -notmatch '\\\.venv\\|\\__pycache__\\|\\.pytest' }

foreach ($file in $pythonFiles | Select-Object -First 10) {
    $content = Get-Content $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($content -match 'event_type.*=.*(thesis|antithesis|synthesis|Binoche_Observer|eval)') {
        $hasQuality = $content -match '"quality":\s*\d'
        $hasLatency = $content -match '"latency_ms":\s*\d'
        
        if (-not $hasQuality -or -not $hasLatency) {
            $scriptsToEnhance += [PSCustomObject]@{
                File       = $file.Name
                Path       = $file.FullName
                HasQuality = $hasQuality
                HasLatency = $hasLatency
            }
        }
    }
}

Write-Host "   ✓ 개선 대상 파일: $($scriptsToEnhance.Count)개 발견" -ForegroundColor Green

# 4. 권장사항 생성
Write-Host "`n[4/4] 실행 가능한 권장사항 생성..." -ForegroundColor Yellow

$recommendations = @"

📊 메트릭 수집 강화 권장사항
================================

현재 상태:
  - Quality 커버리지: $qualityCoverage%
  - Latency 커버리지: $latencyCoverage%
  - 목표: 각 80% 이상

우선순위 개선 대상:
$($targetTypes | Select-Object -First 5 | ForEach-Object { "  - $($_.Name): $($_.Count)개 이벤트" } | Out-String)

코드 수정 권장:
$($scriptsToEnhance | Select-Object -First 5 | ForEach-Object {
    "  - $($_.File): " + $(if (-not $_.HasQuality) { "quality 추가 " } else { "" }) + $(if (-not $_.HasLatency) { "latency 추가" } else { "" })
} | Out-String)

다음 단계:
  1. 각 thesis/antithesis/synthesis 이벤트에 quality 메트릭 추가
  2. 시작/종료 이벤트 쌍에 latency_ms 계산 로직 추가
  3. eval 이벤트에 상세 품질 메트릭 포함

자동화 제안:
  - 메트릭 없는 이벤트 감지 → 자동 경고
  - 일일 메트릭 커버리지 리포트 생성
  - 목표치 미달 시 Slack/이메일 알림

"@

Write-Host $recommendations -ForegroundColor White

# 결과 저장
$outPath = "$WorkspaceRoot\outputs\metric_enhancement_report.md"
$recommendations | Out-File $outPath -Encoding UTF8
Write-Host "`n💾 리포트 저장: $outPath" -ForegroundColor Green

# 요약
Write-Host "`n════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ 메트릭 수집 강화 분석 완료!" -ForegroundColor Green
Write-Host "════════════════════════════════════════`n" -ForegroundColor Cyan

Write-Host "📈 즉시 실행 가능한 액션:" -ForegroundColor Yellow
Write-Host "   1. 리포트 확인: code $outPath" -ForegroundColor Cyan
Write-Host "   2. 코드 수정 시작: 우선순위 높은 파일부터" -ForegroundColor Cyan
Write-Host "   3. 자동화 스크립트 구축: 메트릭 커버리지 모니터링`n" -ForegroundColor Cyan

exit 0