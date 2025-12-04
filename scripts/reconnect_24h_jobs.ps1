<#
.SYNOPSIS
    종료된 터미널에서 24h Production Job 로그 재연결

.DESCRIPTION
    백그라운드 Job은 계속 실행 중이며, 
    이 스크립트로 실시간 로그를 다시 볼 수 있습니다.

.EXAMPLE
    .\reconnect_24h_jobs.ps1
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'

Write-Host "`n=== 24h Production Jobs 상태 확인 ===" -ForegroundColor Cyan

# 실행 중인 Job 확인
$allJobs = Get-Job
$jobs = $allJobs | Where-Object { $_.Name -like 'AGI_*' }

Write-Host "Debug: Total jobs = $($allJobs.Count), AGI jobs = $($jobs.Count)" -ForegroundColor Gray

if ($jobs.Count -eq 0) {
    Write-Host "`n❌ 실행 중인 Job이 없습니다." -ForegroundColor Red
    Write-Host "   재시작: .\resume_24h_productions.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n✅ 실행 중인 Jobs: $($jobs.Count)개`n" -ForegroundColor Green

foreach ($job in $jobs) {
    Write-Host "  🟢 $($job.Name)" -ForegroundColor White
    Write-Host "     시작: $($job.PSBeginTime)" -ForegroundColor Gray
    Write-Host "     상태: $($job.State)" -ForegroundColor Gray
    
    # 최근 로그 (Non-blocking)
    $recentLogs = Receive-Job -Id $job.Id -Keep | Select-Object -Last 3
    if ($recentLogs) {
        Write-Host "     최근:" -ForegroundColor Gray
        $recentLogs | ForEach-Object {
            Write-Host "       $_" -ForegroundColor DarkGray
        }
    }
    Write-Host ""
}

Write-Host "`n📊 로그 파일 상태:" -ForegroundColor Cyan

$logFiles = @(
    "outputs\fullstack_24h_monitoring.jsonl",
    "outputs\lumen_24h_latest.json",
    "outputs\gateway_optimization_log.jsonl"
)

foreach ($logFile in $logFiles) {
    $fullPath = Join-Path $PSScriptRoot "..\$logFile"
    if (Test-Path $fullPath) {
        $size = (Get-Item $fullPath).Length / 1KB
        $lastWrite = (Get-Item $fullPath).LastWriteTime
        Write-Host "  ✅ $logFile" -ForegroundColor Green
        Write-Host "     크기: $([math]::Round($size, 2)) KB" -ForegroundColor Gray
        Write-Host "     수정: $lastWrite" -ForegroundColor Gray
    }
    else {
        Write-Host "  ❌ $logFile (없음)" -ForegroundColor Red
    }
}

Write-Host "`n💡 Tip:" -ForegroundColor Yellow
Write-Host "   실시간 로그 보기:" -ForegroundColor White
Write-Host "   Get-Job -Name 'AGI_Lumen_24h' | Receive-Job -Keep -Wait" -ForegroundColor Cyan
Write-Host ""
Write-Host "   특정 Job 로그 마지막 10줄:" -ForegroundColor White
Write-Host "   Get-Job -Name 'AGI_Lumen_24h' | Receive-Job -Keep | Select-Object -Last 10" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Job 중지:" -ForegroundColor White
Write-Host "   Get-Job -Name 'AGI_*' | Stop-Job" -ForegroundColor Cyan
Write-Host ""
