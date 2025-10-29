<#
.SYNOPSIS
    모니터링 샘플 데이터 수집 스크립트

.DESCRIPTION
    일정 간격으로 quick_status.ps1을 실행하여 모니터링 데이터를 수집합니다.
    대시보드에 유의미한 추세 분석 데이터를 제공하기 위한 스크립트입니다.

.PARAMETER IntervalSeconds
    샘플링 간격 (초 단위, 기본값: 300 = 5분)

.PARAMETER DurationMinutes
    총 수집 시간 (분 단위, 기본값: 60 = 1시간)

.PARAMETER MaxSamples
    최대 샘플 수 (기본값: 20)

.EXAMPLE
    .\collect_monitoring_samples.ps1 -IntervalSeconds 300 -DurationMinutes 60
    5분 간격으로 1시간 동안 데이터 수집

.EXAMPLE
    .\collect_monitoring_samples.ps1 -MaxSamples 10
    10개 샘플 수집 후 종료
#>

param(
    [int]$IntervalSeconds = 300,
    [int]$DurationMinutes = 60,
    [int]$MaxSamples = 0
)

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent $scriptDir
$quickStatusScript = Join-Path $scriptDir "quick_status.ps1"
$outputPath = Join-Path $workspaceRoot "outputs\status_snapshots.jsonl"

# ========================================
# 사전 검증
# ========================================

if (-not (Test-Path $quickStatusScript)) {
    Write-Host "[ERROR] quick_status.ps1이 존재하지 않습니다: $quickStatusScript" -ForegroundColor Red
    exit 1
}

$outputDir = Split-Path -Parent $outputPath
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "[OK] 출력 디렉토리 생성: $outputDir" -ForegroundColor Green
}

# ========================================
# 설정 출력
# ========================================

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Monitoring Data Collection" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "   Interval:      $IntervalSeconds seconds" -ForegroundColor White
Write-Host "   Duration:      $DurationMinutes minutes" -ForegroundColor White
if ($MaxSamples -gt 0) {
    Write-Host "   Max Samples:   $MaxSamples" -ForegroundColor White
}
Write-Host "   Output:        $outputPath" -ForegroundColor White
Write-Host ""

# ========================================
# 수집 루프
# ========================================

$startTime = Get-Date
$endTime = $startTime.AddMinutes($DurationMinutes)
$sampleCount = 0

Write-Host "[START] Starting data collection..." -ForegroundColor Green
Write-Host "   Start:  $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
Write-Host "   End:    $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
Write-Host ""

while ($true) {
    $now = Get-Date
    
    # 종료 조건 확인
    if ($now -ge $endTime) {
        Write-Host ""
        Write-Host "[STOP] Duration reached. Stopping collection." -ForegroundColor Yellow
        break
    }
    
    if ($MaxSamples -gt 0 -and $sampleCount -ge $MaxSamples) {
        Write-Host ""
        Write-Host "[STOP] Max samples reached. Stopping collection." -ForegroundColor Yellow
        break
    }
    
    # 샘플 수집
    $sampleCount++
    Write-Host "[$($now.ToString('HH:mm:ss'))] Sample #$sampleCount collecting..." -ForegroundColor Cyan -NoNewline
    
    try {
        # quick_status.ps1 실행 (-LogJsonl 옵션으로 JSONL에 기록)
        $result = & $quickStatusScript -LogJsonl 2>&1 | Out-String
        
        # 성공 확인
        if ($LASTEXITCODE -eq 0) {
            Write-Host " [OK]" -ForegroundColor Green
        }
        else {
            Write-Host " [WARN] (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host " [ERROR] Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # 다음 샘플까지 대기
    if ($now.AddSeconds($IntervalSeconds) -lt $endTime -and ($MaxSamples -eq 0 -or $sampleCount -lt $MaxSamples)) {
        Start-Sleep -Seconds $IntervalSeconds
    }
    else {
        break
    }
}

# ========================================
# 완료 요약
# ========================================

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Collection Complete" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "   Total Samples:     $sampleCount" -ForegroundColor White
Write-Host "   Output File:       $outputPath" -ForegroundColor White

if (Test-Path $outputPath) {
    $lines = Get-Content -LiteralPath $outputPath | Measure-Object -Line
    Write-Host "   Lines in File:     $($lines.Lines)" -ForegroundColor White
    
    $fileSize = (Get-Item -LiteralPath $outputPath).Length
    if ($fileSize -lt 1024) {
        Write-Host "   File Size:         $fileSize bytes" -ForegroundColor White
    }
    elseif ($fileSize -lt 1024 * 1024) {
        Write-Host "   File Size:         $([math]::Round($fileSize/1KB, 2)) KB" -ForegroundColor White
    }
    else {
        Write-Host "   File Size:         $([math]::Round($fileSize/1MB, 2)) MB" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Run generate_monitoring_report.ps1 to create dashboard" -ForegroundColor White
Write-Host "   2. Open monitoring_dashboard_latest.html" -ForegroundColor White
Write-Host ""
