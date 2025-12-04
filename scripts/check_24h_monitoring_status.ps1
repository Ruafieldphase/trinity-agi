#!/usr/bin/env pwsh
# Check 24h monitoring status

Write-Host "`n=== 24h 모니터링 상태 체크 ===" -ForegroundColor Cyan

Write-Host "`n[1] Gateway 최적화 모니터링" -ForegroundColor Yellow
$gatewayLog = "C:\workspace\agi\outputs\gateway_optimization_log.jsonl"
if (Test-Path $gatewayLog) {
    $lines = Get-Content $gatewayLog -Tail 1
    if ($lines) {
        $last = $lines | ConvertFrom-Json
        Write-Host "  마지막 기록: $($last.timestamp)" -ForegroundColor White
        Write-Host "  레이턴시: $($last.avg_latency_ms)ms" -ForegroundColor Cyan
        Write-Host "  이벤트: $($last.events_processed)" -ForegroundColor Green
    }
}
else {
    Write-Host "  ❌ 로그 파일 없음" -ForegroundColor Red
}

Write-Host "`n[2] Orchestrator 24h Production" -ForegroundColor Yellow
$orchLog = "C:\workspace\agi\fdo_agi_repo\outputs\fullstack_24h_monitoring.jsonl"
if (Test-Path $orchLog) {
    $lines = Get-Content $orchLog -Tail 1
    if ($lines) {
        $last = $lines | ConvertFrom-Json
        Write-Host "  마지막 사이클: $($last.cycle)" -ForegroundColor White
        Write-Host "  이벤트 처리: $($last.events_processed)" -ForegroundColor Green
        Write-Host "  타임스탬프: $($last.timestamp)" -ForegroundColor Cyan
    }
}
else {
    Write-Host "  ❌ 로그 파일 없음" -ForegroundColor Red
}

Write-Host "`n[3] 1h 효과 측정 결과" -ForegroundColor Yellow
$effectLog = "C:\workspace\agi\outputs\optimization_effect_1h.json"
if (Test-Path $effectLog) {
    $result = Get-Content $effectLog -Raw | ConvertFrom-Json
    Write-Host "  시작: $($result.start_time)" -ForegroundColor White
    Write-Host "  종료: $($result.end_time)" -ForegroundColor White
    Write-Host "  평균 레이턴시: $($result.avg_latency_ms)ms" -ForegroundColor Cyan
    Write-Host "  개선율: $($result.improvement_percent)%" -ForegroundColor Green
}
else {
    Write-Host "  ⏳ 아직 완료되지 않음" -ForegroundColor Yellow
}

Write-Host "`n현재 시각: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')" -ForegroundColor White
Write-Host ""
