# Lumen 24h Production 실시간 모니터링
param(
    [int]$RefreshSeconds = 10
)

$logFile = "C:\workspace\agi\fdo_agi_repo\outputs\lumen_production_24h_stable.jsonl"

Write-Host "`n╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Lumen 24h Production - 실시간 모니터링      ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════╝`n" -ForegroundColor Cyan

while ($true) {
    Clear-Host
    
    Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  Lumen 24h Production Monitor                 ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════╝`n" -ForegroundColor Cyan
    
    # Job 상태
    $job = Get-Job -Name 'Lumen_24h_Stable' -ErrorAction SilentlyContinue
    if ($job) {
        Write-Host "🔄 Job 상태: " -NoNewline -ForegroundColor Yellow
        Write-Host $job.State -ForegroundColor $(if ($job.State -eq 'Running') { 'Green' } else { 'Red' })
        
        if ($job.PSBeginTime) {
            $elapsed = (Get-Date) - $job.PSBeginTime
            Write-Host "⏱️  실행 시간: " -NoNewline -ForegroundColor Yellow
            Write-Host "$([math]::Floor($elapsed.TotalHours))h $($elapsed.Minutes)m" -ForegroundColor White
        }
    }
    else {
        Write-Host "❌ Job 없음" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # 로그 파일 분석
    if (Test-Path $logFile) {
        $lines = Get-Content $logFile
        $count = $lines.Count
        
        Write-Host "📊 현재 진행:" -ForegroundColor Cyan
        Write-Host "   총 사이클: $count / 288" -ForegroundColor White
        
        if ($count -gt 0) {
            try {
                $latest = $lines[-1] | ConvertFrom-Json
                
                $progress = ($latest.elapsed_hours / 24) * 100
                Write-Host "   진행률: " -NoNewline -ForegroundColor White
                Write-Host "$([math]::Round($progress, 1))%" -ForegroundColor Green
                
                Write-Host "`n✨ 최신 사이클 #$($latest.cycle):" -ForegroundColor Yellow
                Write-Host "   시간: $($latest.timestamp.Substring(11,8))" -ForegroundColor Gray
                Write-Host "   상태: " -NoNewline -ForegroundColor White
                $stateColor = switch ($latest.system_state) {
                    "OPTIMAL" { "Green" }
                    "GOOD" { "Cyan" }
                    "DEGRADED" { "Yellow" }
                    default { "Gray" }
                }
                Write-Host $latest.system_state -ForegroundColor $stateColor
                
                Write-Host "`n📈 메트릭:" -ForegroundColor Cyan
                Write-Host "   Cache Hit: $([math]::Round($latest.metrics.cache_hit_rate, 1))%" -ForegroundColor White
                Write-Host "   GPU Memory: $([math]::Round($latest.metrics.gpu_memory_used_gb, 1)) GB" -ForegroundColor White
                Write-Host "   Latency: $([math]::Round($latest.metrics.system_latency_ms, 0)) ms" -ForegroundColor White
                
                Write-Host "`n🎯 최적화:" -ForegroundColor Cyan
                Write-Host "   실행: $($latest.total_optimizations) / $($latest.cycle)" -ForegroundColor White
                $optRate = ($latest.total_optimizations / $latest.cycle) * 100
                Write-Host "   비율: $([math]::Round($optRate, 0))%" -ForegroundColor Green
                
                # ETA
                if ($latest.elapsed_hours -gt 0) {
                    $remainingHours = 24 - $latest.elapsed_hours
                    $eta = (Get-Date).AddHours($remainingHours)
                    Write-Host "`n⏰ 예상 완료: $($eta.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Yellow
                }
                
            }
            catch {
                Write-Host "   ⚠️  JSON 파싱 오류" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host "⚠️  로그 파일 없음" -ForegroundColor Red
        Write-Host "   경로: $logFile" -ForegroundColor Gray
    }
    
    Write-Host "`n" + ("─" * 50) -ForegroundColor DarkGray
    Write-Host "다음 갱신: ${RefreshSeconds}초 후 (Ctrl+C로 종료)" -ForegroundColor Gray
    
    Start-Sleep -Seconds $RefreshSeconds
}
