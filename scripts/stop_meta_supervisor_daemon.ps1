<#
.SYNOPSIS
Meta Supervisor 백그라운드 실행 종료

.DESCRIPTION
실행 중인 Meta Supervisor 백그라운드 Job을 종료합니다.

.EXAMPLE
.\stop_meta_supervisor_daemon.ps1
#>

$ErrorActionPreference = "Stop"
$jobName = "MetaSupervisorDaemon"

Write-Host "🛑 Meta Supervisor 종료 중..." -ForegroundColor Yellow
Write-Host ""

$job = Get-Job -Name $jobName -ErrorAction SilentlyContinue

if (-not $job) {
    Write-Host "ℹ️  실행 중인 Meta Supervisor가 없습니다." -ForegroundColor Gray
    exit 0
}

Write-Host "Job 정보:"
Write-Host "  ID: $($job.Id)"
Write-Host "  상태: $($job.State)"
Write-Host "  시작 시각: $($job.PSBeginTime)"
Write-Host ""

# Job 종료
Stop-Job -Name $jobName -ErrorAction SilentlyContinue
Remove-Job -Name $jobName -Force

Write-Host "✅ Meta Supervisor 종료 완료" -ForegroundColor Green
