<#
.SYNOPSIS
    24시간 Gateway 최적화 모니터링 실행

.DESCRIPTION
    지정된 기간 동안 Gateway 최적화 효과를 모니터링하고 로그를 기록합니다.

.PARAMETER DurationHours
    모니터링 지속 시간 (시간 단위, 기본값: 24)

.PARAMETER IntervalMinutes
    샘플링 간격 (분 단위, 기본값: 10)

.EXAMPLE
    .\start_gateway_optimization.ps1 -DurationHours 24 -IntervalMinutes 10
#>

param(
    [int]$DurationHours = 24,
    [int]$IntervalMinutes = 10
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host "`n=== Gateway 최적화 24시간 모니터링 시작 ===" -ForegroundColor Cyan
Write-Host "`n현재 시각: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor White
Write-Host "지속 시간: $DurationHours 시간" -ForegroundColor Gray
Write-Host "샘플 간격: $IntervalMinutes 분" -ForegroundColor Gray

$endTime = (Get-Date).AddHours($DurationHours)
Write-Host "`n예상 완료: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Yellow

$totalSamples = ($DurationHours * 60) / $IntervalMinutes
Write-Host "총 샘플 수: $totalSamples 개" -ForegroundColor Gray

$logFile = "outputs\gateway_optimization_log.jsonl"
Write-Host "`n로그 파일: $logFile" -ForegroundColor Cyan

$workspaceRoot = Split-Path $PSScriptRoot -Parent
$pythonScript = Join-Path $workspaceRoot "fdo_agi_repo\scripts\optimize_gateway_resonance.py"

# Python 경로 찾기
$pythonExe = "python"
$venvPython = Join-Path $workspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
}

Write-Host "`nPython: $pythonExe" -ForegroundColor Gray
Write-Host "`n모니터링 시작...`n" -ForegroundColor Green

$sampleCount = 0

while ((Get-Date) -lt $endTime) {
    $sampleCount++
    $remaining = [math]::Round((($endTime - (Get-Date)).TotalMinutes), 1)
    
    Write-Host "[$sampleCount/$totalSamples] 샘플링 중... (남은 시간: $remaining 분)" -ForegroundColor Cyan
    
    try {
        # 최적화 스크립트 실행
        & $pythonExe $pythonScript --log-file $logFile 2>&1 | Out-Null
        
        Write-Host "  ✅ 샘플 기록 완료" -ForegroundColor Green
        
    }
    catch {
        Write-Host "  ⚠️  샘플링 오류: $_" -ForegroundColor Yellow
    }
    
    # 다음 샘플까지 대기
    if ((Get-Date) -lt $endTime) {
        Start-Sleep -Seconds ($IntervalMinutes * 60)
    }
}

Write-Host "`n=== 모니터링 완료 ===" -ForegroundColor Green
Write-Host "`n총 샘플: $sampleCount 개" -ForegroundColor White
Write-Host "로그 파일: $logFile" -ForegroundColor Cyan
Write-Host "`n다음 단계:" -ForegroundColor Yellow
Write-Host "  .\scripts\analyze_optimization_impact.ps1" -ForegroundColor Gray
Write-Host ""
