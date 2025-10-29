#Requires -Version 5.1
<#
.SYNOPSIS
    오래된 깃코 봇 로그 파일을 정리합니다.

.DESCRIPTION
    지정된 일수보다 오래된 로그 파일을 삭제하여 디스크 공간을 확보합니다.

.PARAMETER KeepDays
    보관할 로그 파일의 일수 (기본값: 7일)

.PARAMETER DryRun
    실제 삭제하지 않고 삭제될 파일만 표시합니다.

.EXAMPLE
    .\cleanup_old_bot_logs.ps1
    # 7일 이상 된 로그 삭제

.EXAMPLE
    .\cleanup_old_bot_logs.ps1 -KeepDays 14 -DryRun
    # 14일 이상 된 로그 미리보기
#>

[CmdletBinding()]
param(
    [int]$KeepDays = 7,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$WORKSPACE_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$OUTPUTS_DIR = Join-Path $WORKSPACE_ROOT "LLM_Unified\ion-mentoring\outputs"
$LOG_DIR = Join-Path $OUTPUTS_DIR "logs"

if (-not (Test-Path $LOG_DIR)) {
    Write-Host "📁 로그 디렉토리가 없습니다: $LOG_DIR" -ForegroundColor Yellow
    exit 0
}

$cutoffDate = (Get-Date).AddDays(-$KeepDays)
Write-Host "🗑️  $KeepDays 일 이전 로그 정리 중..." -ForegroundColor Cyan
Write-Host "기준 날짜: $($cutoffDate.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray

$oldLogs = Get-ChildItem -Path $LOG_DIR -Filter "*.log" | Where-Object {
    $_.LastWriteTime -lt $cutoffDate
}

if ($oldLogs.Count -eq 0) {
    Write-Host "✅ 삭제할 오래된 로그가 없습니다." -ForegroundColor Green
    exit 0
}

$totalSize = ($oldLogs | Measure-Object -Property Length -Sum).Sum
$totalSizeMB = [math]::Round($totalSize / 1MB, 2)

Write-Host ""
Write-Host "📊 정리 대상:" -ForegroundColor Yellow
Write-Host "  • 파일 수: $($oldLogs.Count)" -ForegroundColor White
Write-Host "  • 총 크기: $totalSizeMB MB" -ForegroundColor White
Write-Host ""

if ($DryRun) {
    Write-Host "🔍 [DRY RUN] 다음 파일들이 삭제됩니다:" -ForegroundColor Yellow
    $oldLogs | ForEach-Object {
        $sizeMB = [math]::Round($_.Length / 1MB, 2)
        Write-Host "  • $($_.Name) ($sizeMB MB) - $($_.LastWriteTime.ToString('yyyy-MM-dd'))" -ForegroundColor Gray
    }
}
else {
    Write-Host "🗑️  로그 파일 삭제 중..." -ForegroundColor Yellow
    $deleted = 0
    foreach ($log in $oldLogs) {
        try {
            Remove-Item $log.FullName -Force
            $deleted++
        }
        catch {
            Write-Host "  ⚠️  삭제 실패: $($log.Name)" -ForegroundColor Red
        }
    }
    Write-Host "✅ $deleted 개 파일 삭제 완료 ($totalSizeMB MB 확보)" -ForegroundColor Green
}
