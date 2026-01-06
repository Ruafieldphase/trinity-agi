<#
.SYNOPSIS
Meta Supervisor 백그라운드 실행 상태 확인

.DESCRIPTION
실행 중인 Meta Supervisor 백그라운드 Job의 상태를 확인하고 최근 로그를 보여줍니다.

.PARAMETER ShowLogs
최근 로그 출력

.PARAMETER LogLines
출력할 로그 줄 수 (기본 20줄)

.EXAMPLE
.\check_meta_supervisor_daemon_status.ps1

.EXAMPLE
.\check_meta_supervisor_daemon_status.ps1 -ShowLogs -LogLines 50
#>

param(
    [switch]$ShowLogs,
    [int]$LogLines = 20
)

$ErrorActionPreference = "Stop"
$jobName = "MetaSupervisorDaemon"
$workspaceRoot = Split-Path $PSScriptRoot -Parent

Write-Host "📊 Meta Supervisor 상태 확인" -ForegroundColor Cyan
Write-Host ""

# Job 상태
$job = Get-Job -Name $jobName -ErrorAction SilentlyContinue

if (-not $job) {
    Write-Host "❌ Meta Supervisor가 실행 중이 아닙니다." -ForegroundColor Red
    Write-Host ""
    Write-Host "시작 방법:"
    Write-Host "  .\start_meta_supervisor_daemon.ps1"
    exit 1
}

Write-Host "✅ 실행 중" -ForegroundColor Green
Write-Host ""
Write-Host "Job 정보:"
Write-Host "  ID: $($job.Id)"
Write-Host "  이름: $jobName"
Write-Host "  상태: $($job.State)"
Write-Host "  시작 시각: $($job.PSBeginTime)"

if ($job.PSEndTime) {
    Write-Host "  종료 시각: $($job.PSEndTime)"
}

# 실행 시간 계산
$runningTime = (Get-Date) - $job.PSBeginTime
Write-Host "  실행 시간: $([int]$runningTime.TotalHours)시간 $($runningTime.Minutes)분"
Write-Host ""

# 최근 보고서 확인
$latestReport = Join-Path $workspaceRoot "outputs\meta_supervision_report.md"
$latestJson = Join-Path $workspaceRoot "outputs\meta_supervision_latest.json"

if (Test-Path $latestReport) {
    $reportTime = (Get-Item $latestReport).LastWriteTime
    $timeSince = (Get-Date) - $reportTime
    
    Write-Host "📄 최근 보고서:"
    Write-Host "  파일: $latestReport"
    Write-Host "  생성: $reportTime ($([int]$timeSince.TotalMinutes)분 전)"
    
    # JSON에서 점수 읽기
    if (Test-Path $latestJson) {
        try {
            $jsonData = Get-Content $latestJson -Raw | ConvertFrom-Json
            $score = $jsonData.analysis.score
            $status = $jsonData.analysis.status
            $interventionLevel = $jsonData.analysis.intervention_level
            
            Write-Host "  점수: $score/100"
            Write-Host "  상태: $status"
            Write-Host "  개입 수준: $interventionLevel"
        }
        catch {
            Write-Host "  (JSON 파싱 실패)" -ForegroundColor Gray
        }
    }
}
else {
    Write-Host "⚠️  보고서 파일 없음" -ForegroundColor Yellow
}

Write-Host ""

# 로그 출력
if ($ShowLogs) {
    Write-Host "📋 최근 로그 (마지막 $LogLines 줄):" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        $logs = Receive-Job -Name $jobName -Keep | Select-Object -Last $LogLines
        if ($logs) {
            $logs | ForEach-Object { Write-Host $_ }
        }
        else {
            Write-Host "  (로그 없음)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  로그 읽기 실패: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "💡 관리 명령:"
Write-Host "  종료: .\stop_meta_supervisor_daemon.ps1"
Write-Host "  재시작: .\start_meta_supervisor_daemon.ps1 -KillExisting"
Write-Host "  로그 보기: Get-Job -Name $jobName | Receive-Job -Keep"
Write-Host "  보고서 열기: code outputs\meta_supervision_report.md"