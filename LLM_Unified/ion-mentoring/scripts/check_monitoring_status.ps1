# 모니터링 진행 상황 실시간 체크 스크립트
# 목적: monitor_canary_health.ps1의 현재 상태를 빠르게 확인

param(
    [Parameter(Mandatory = $false)]
    [switch]$Continuous,
    [Parameter(Mandatory = $false)]
    [int]$RefreshSeconds = 30,
    [Parameter(Mandatory = $false)]
    [switch]$ReturnExitCode,
    [Parameter(Mandatory = $false)]
    [string]$OutJson
)

$ErrorActionPreference = 'Continue'

$scriptDir = Split-Path -Parent $PSCommandPath
$projectRoot = Split-Path -Parent $scriptDir

function Invoke-GetCanaryMetricsSafe {
    param(
        [Parameter(Mandatory = $false)] [string]$BaseUrl,
        [Parameter(Mandatory = $false)] [string]$LegacyUrl
    )
    $scriptPath = Join-Path $scriptDir 'get_canary_metrics.ps1'
    if (-not (Test-Path $scriptPath)) {
        return @{ ExitCode = 1; Output = ""; Error = "Script not found: $scriptPath" }
    }

    $argsList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $scriptPath)
    if ($BaseUrl -and $BaseUrl.Trim().Length -gt 0) { $argsList += @('-BaseUrl', $BaseUrl) }
    if ($LegacyUrl -and $LegacyUrl.Trim().Length -gt 0) { $argsList += @('-LegacyUrl', $LegacyUrl) }

    $tmpOut = [System.IO.Path]::GetTempFileName()
    try {
        $psExe = 'powershell.exe'
        $proc = Start-Process -FilePath $psExe -ArgumentList $argsList -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput $tmpOut
        $stdout = ''
        if (Test-Path $tmpOut) { $stdout = Get-Content -Path $tmpOut -Raw -ErrorAction SilentlyContinue }
        return @{ ExitCode = $proc.ExitCode; Output = $stdout; Error = "" }
    }
    catch {
        return @{ ExitCode = 1; Output = ""; Error = $_.Exception.Message }
    }
    finally {
        if (Test-Path $tmpOut) { Remove-Item -Path $tmpOut -Force -ErrorAction SilentlyContinue }
    }
}

function Get-MonitoringStatus {
    Write-Host "`n=== Phase 4 Monitoring Status ===" -ForegroundColor Cyan
    Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    
    # 현재 메트릭 가져오기
    $healthy = $false
    $statusObj = @{}
    try {
        Write-Host "`nFetching current metrics..." -ForegroundColor Yellow

        $metricsRes = Invoke-GetCanaryMetricsSafe
        $metricsJson = $metricsRes.Output

        if ($metricsRes.ExitCode -ne 0 -or -not $metricsJson -or $metricsJson.Trim().Length -eq 0) {
            Write-Host "  WARNING: Could not fetch metrics (empty output)" -ForegroundColor Yellow
            $healthy = $false
            $statusObj = [ordered]@{
                timestamp          = (Get-Date).ToString('s')
                healthy            = $false
                error_rate_percent = $null
                p95_ms             = $null
                telemetry_anomaly  = $true
                error              = 'metrics_unavailable'
            }
            if ($OutJson) {
                try { $statusObj | ConvertTo-Json -Depth 5 | Out-File -FilePath $OutJson -Encoding UTF8 } catch {}
            }
            if ($ReturnExitCode) { exit 1 } else { return }
        }

        $metrics = $metricsJson | ConvertFrom-Json -ErrorAction Stop
        $canary = $metrics.canary
        
        # 상태 출력
        Write-Host "`n📊 Current Metrics:" -ForegroundColor Cyan
        Write-Host "  Request Count: $($canary.request_count)" -ForegroundColor White
        Write-Host "  Error Count: $($canary.error_count)" -ForegroundColor $(if ($canary.error_count -eq 0) { 'Green' } else { 'Red' })
        # Normalize error rate accepting either numeric or percentage-string
        $errorRateStr = [string]$canary.error_rate
        $errorRateVal = $null
        if ($errorRateStr -match '%') { $errorRateVal = [double]($errorRateStr -replace '%', '') } else { $errorRateVal = [double]$errorRateStr }
        Write-Host "  Error Rate: $errorRateVal%" -ForegroundColor $(if ($errorRateVal -le 0.5) { 'Green' } else { 'Red' })
        Write-Host "  Avg Response Time: $($canary.avg_response_time_ms)ms" -ForegroundColor Gray
        Write-Host "  P50: $($canary.p50_response_time_ms)ms" -ForegroundColor Gray
        Write-Host "  P95: $($canary.p95_response_time_ms)ms" -ForegroundColor $(if ([double]$canary.p95_response_time_ms -le 200) { 'Green' } else { 'Yellow' })
        Write-Host "  P99: $($canary.p99_response_time_ms)ms" -ForegroundColor Gray
        
        # 임계값 체크
        $errorRate = [double]$errorRateVal
        $p95 = [double]$canary.p95_response_time_ms
        
        Write-Host "`n✅ Threshold Checks:" -ForegroundColor Cyan
        Write-Host "  Error Rate ≤ 0.5%: " -NoNewline
        if ($errorRate -le 0.5) {
            Write-Host "PASS ($errorRate%)" -ForegroundColor Green
        }
        else {
            Write-Host "FAIL ($errorRate%)" -ForegroundColor Red
        }
        
        Write-Host "  P95 ≤ 200ms: " -NoNewline
        if ($p95 -le 200) {
            Write-Host "PASS (${p95}ms)" -ForegroundColor Green
        }
        else {
            Write-Host "FAIL (${p95}ms)" -ForegroundColor Red
        }
        
        # 전체 상태
        # Additional sanity: if errorRate >> 50% but latencies are ultra low (<10ms), flag as telemetry anomaly
        $telemetryAnomaly = ($errorRate -ge 50) -and ($p95 -le 10)
        $healthy = ($errorRate -le 0.5) -and ($p95 -le 200) -and (-not $telemetryAnomaly)
        Write-Host "`n🏥 Overall Status: " -NoNewline
        if ($healthy) {
            Write-Host "HEALTHY" -ForegroundColor Green
        }
        else {
            if ($telemetryAnomaly) {
                Write-Host "UNHEALTHY (telemetry anomaly suspected)" -ForegroundColor Yellow
            }
            else {
                Write-Host "UNHEALTHY" -ForegroundColor Red
            }
        }
        
        $statusObj = [ordered]@{
            timestamp          = (Get-Date).ToString('s')
            healthy            = $healthy
            error_rate_percent = $errorRate
            p95_ms             = $p95
            telemetry_anomaly  = $telemetryAnomaly
        }
    }
    catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # 모니터링 결과 파일 체크
    Write-Host "`n📁 Monitoring Results:" -ForegroundColor Cyan
    $monitoringDir = Join-Path $projectRoot 'monitoring'
    $resultFiles = Get-ChildItem "$monitoringDir\monitoring_results_*.json" -ErrorAction SilentlyContinue | 
    Sort-Object LastWriteTime -Descending
    
    if ($resultFiles) {
        $latestFile = $resultFiles[0]
        Write-Host "  Latest: $($latestFile.Name)" -ForegroundColor Gray
        Write-Host "  Modified: $($latestFile.LastWriteTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
        
        try {
            $results = Get-Content $latestFile.FullName | ConvertFrom-Json
            Write-Host "  Total Checks: $($results.Count)" -ForegroundColor White
            
            $passed = ($results | Where-Object { $_.overall_pass }).Count
            $failed = $results.Count - $passed
            
            Write-Host "  Passed: $passed" -ForegroundColor Green
            Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { 'Green' } else { 'Red' })
            
            # 최근 3개 체크 요약
            if ($results.Count -gt 0) {
                Write-Host "`n  Recent Checks:" -ForegroundColor Cyan
                $results | Select-Object -Last 3 | ForEach-Object {
                    $status = if ($_.overall_pass) { "✓ PASS" } else { "✗ FAIL" }
                    $color = if ($_.overall_pass) { "Green" } else { "Red" }
                    Write-Host "    #$($_.check_number) @ $($_.timestamp): $status (P95: $($_.p95_ms)ms, Err: $($_.error_rate)%)" -ForegroundColor $color
                }
            }
        }
        catch {
            Write-Host "  Could not parse results file" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  No results files found yet (will be created when monitoring completes)" -ForegroundColor Yellow
    }
    
    if ($OutJson) {
        try { $statusObj | ConvertTo-Json -Depth 5 | Out-File -FilePath $OutJson -Encoding UTF8 } catch {}
    }

    Write-Host "`n" -NoNewline
    if ($ReturnExitCode) { if ($healthy) { exit 0 } else { exit 1 } }
}

# 단일 실행 또는 연속 실행
if ($Continuous) {
    Write-Host "Continuous monitoring mode (Ctrl+C to exit)" -ForegroundColor Yellow
    Write-Host "Refresh interval: $RefreshSeconds seconds`n" -ForegroundColor Gray
    
    while ($true) {
        Clear-Host
        Get-MonitoringStatus
        Write-Host "Next refresh in $RefreshSeconds seconds... (Ctrl+C to exit)" -ForegroundColor Gray
        Start-Sleep -Seconds $RefreshSeconds
    }
}
else {
    Get-MonitoringStatus
}
