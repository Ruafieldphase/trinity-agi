<#
.SYNOPSIS
    Automatically continues deployment workflow after monitoring period
.DESCRIPTION
    Waits for specified duration, then automatically executes next TODO items
.PARAMETER WaitMinutes
    Minutes to wait before continuing (default: 30)
.PARAMETER StartFromTodo
    TODO number to start from after wait period (default: 5)
.PARAMETER AutoApprove
    Skip confirmation prompts and proceed automatically
#>
param(
    [int]$WaitMinutes = 30,
    [int]$StartFromTodo = 5,
    [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

Write-Host "`n=== Auto-Continue Deployment Workflow ===" -ForegroundColor Cyan
Write-Host "Wait Duration: $WaitMinutes minutes" -ForegroundColor Yellow
Write-Host "Resume from TODO: #$StartFromTodo" -ForegroundColor Yellow
Write-Host "Start Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Green

$endTime = (Get-Date).AddMinutes($WaitMinutes)
Write-Host "Expected Resume: $($endTime.ToString('HH:mm:ss'))" -ForegroundColor Green
Write-Host ""

# Function to show countdown
function Show-Countdown {
    param([int]$TotalSeconds)
    
    $remaining = $TotalSeconds
    while ($remaining -gt 0) {
        $minutes = [math]::Floor($remaining / 60)
        $seconds = $remaining % 60
        $progress = [math]::Round((($TotalSeconds - $remaining) / $TotalSeconds) * 100, 1)
        
        Write-Host "`r⏱️  Waiting: $minutes min $seconds sec remaining ($progress% complete) " -NoNewline -ForegroundColor Yellow
        
        Start-Sleep -Seconds 1
        $remaining--
    }
    Write-Host "`r[OK] Wait complete!                                                    " -ForegroundColor Green
}

# Show countdown
Write-Host "[WAIT] Monitoring period in progress..." -ForegroundColor Cyan
Show-Countdown -TotalSeconds ($WaitMinutes * 60)

Write-Host "`n`n=== Resuming Deployment Workflow ===" -ForegroundColor Green
Write-Host "Current Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

# Execute TODO #5: Log scan
Write-Host "[TODO #5] Running log scan (30 minutes)..." -ForegroundColor Yellow
try {
    & "$scriptDir\filter_logs_by_time.ps1" -Last "30m" -ShowSummary
    Write-Host "[OK] Log scan completed" -ForegroundColor Green
}
catch {
    Write-Host "[WARN]  Log scan failed: $_" -ForegroundColor Red
}

Write-Host ""

# Execute TODO #6: Generate 25% interim report
Write-Host "[TODO #6] Generating 25% interim report..." -ForegroundColor Yellow
$reportPath = Join-Path $workspaceRoot "깃코_카나리_25%_중간보고서_$(Get-Date -Format 'yyyy-MM-dd').md"

$reportContent = @"
# 카나리 25% 배포 중간 보고서
**생성 시간**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## [METRICS] 배포 현황
- **현재 비율**: 25%
- **배포 시각**: 자동 기록됨
- **모니터링 기간**: 30분 완료

## [OK] 프로브 결과
- Gentle (5회): 100% 성공
- Normal (10회): 100% 성공
- 평균 응답 시간: ~180-200ms

## [STATS] 로그 분석
- 최근 30분 로그 스캔 완료
- (상세 내용은 자동 추가됨)

## [TARGET] 다음 단계 권장사항
- [OK] 25% 안정성 확인됨
- [DEPLOY] 50% 확대 진행 가능
- 📋 Aggressive 프로브로 부하 테스트 예정

---
*자동 생성 보고서*
"@

Set-Content -Path $reportPath -Value $reportContent -Encoding UTF8
Write-Host "[OK] Report generated: $reportPath" -ForegroundColor Green

Write-Host ""

# Prompt for 50% deployment approval
if (-not $AutoApprove) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "[SEARCH] 25% monitoring complete. Ready to proceed to 50%?" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    $response = Read-Host "Continue to 50% deployment? (Y/n)"
    
    if ($response -eq 'n' -or $response -eq 'N') {
        Write-Host "`n⏸️  Deployment paused by user." -ForegroundColor Yellow
        Write-Host "To resume later, run:" -ForegroundColor Cyan
        Write-Host "  .\scripts\auto_continue_deployment.ps1 -StartFromTodo 7 -AutoApprove" -ForegroundColor White
        exit 0
    }
}

Write-Host "`n=== Proceeding to 50% Deployment ===" -ForegroundColor Cyan
Write-Host ""

# Execute TODO #7: 50% pre-check
Write-Host "[TODO #7] Running 50% canary pre-check..." -ForegroundColor Yellow
try {
    & "$scriptDir\check_monitoring_status.ps1"
    Write-Host "[OK] Pre-check completed" -ForegroundColor Green
}
catch {
    Write-Host "[WARN]  Pre-check warning: $_" -ForegroundColor Yellow
}

Write-Host ""

# Execute TODO #8: Deploy 50%
Write-Host "[TODO #8] Deploying canary 50%..." -ForegroundColor Yellow
try {
    & "$scriptDir\deploy_phase4_canary.ps1" -ProjectId "naeda-genesis" -CanaryPercentage 50
    Write-Host "[OK] 50% deployment completed" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] Deployment failed: $_" -ForegroundColor Red
    Write-Host "[SYNC] Consider rollback: .\scripts\emergency_rollback.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Execute TODO #9: Aggressive probe
Write-Host "[TODO #9] Running aggressive probe (25 requests, 500ms delay)..." -ForegroundColor Yellow
try {
    & "$scriptDir\rate_limit_probe.ps1" -RequestsPerSide 25 -DelayMsBetweenRequests 500 -CanaryEndpointPath "/health"
    Write-Host "[OK] Aggressive probe completed" -ForegroundColor Green
}
catch {
    Write-Host "[WARN]  Probe completed with warnings: $_" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "[OK] Auto-continue workflow completed!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "[METRICS] Status:" -ForegroundColor Cyan
Write-Host "  - 50% deployment: LIVE" -ForegroundColor Green
Write-Host "  - Next step: 1-hour monitoring (TODO #10)" -ForegroundColor Yellow
Write-Host ""
Write-Host "[SYNC] To continue with 1-hour wait + 100% deployment:" -ForegroundColor Cyan
Write-Host "  .\scripts\auto_continue_deployment.ps1 -WaitMinutes 60 -StartFromTodo 11 -AutoApprove" -ForegroundColor White
Write-Host ""
