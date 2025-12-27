# 긴급 PowerShell 프로세스 전체 중지 스크립트
# ============================================
# 사용법: .\agi\scripts\emergency_stop_all_powershell.ps1

Write-Host "`n🚨 긴급 PowerShell 프로세스 중지" -ForegroundColor Red
Write-Host "=" * 60

# 1. 현재 실행 중인 PowerShell 프로세스 확인
Write-Host "`n📊 현재 실행 중인 PowerShell 프로세스:" -ForegroundColor Yellow
$processes = Get-Process powershell* -ErrorAction SilentlyContinue
if ($processes) {
    $processes | Select-Object Id, ProcessName, StartTime, CPU | Format-Table -AutoSize
    Write-Host "총 $($processes.Count)개 프로세스 발견" -ForegroundColor Cyan
} else {
    Write-Host "실행 중인 PowerShell 프로세스가 없습니다." -ForegroundColor Green
    exit 0
}

# 2. 현재 스크립트를 제외한 모든 PowerShell 프로세스 중지
Write-Host "`n🛑 PowerShell 프로세스 중지 중..." -ForegroundColor Yellow

$currentPID = $PID
$stopped = 0
$failed = 0

foreach ($proc in $processes) {
    # 현재 실행 중인 스크립트는 제외
    if ($proc.Id -eq $currentPID) {
        Write-Host "  ⏭️  현재 스크립트 제외 (PID: $currentPID)" -ForegroundColor Gray
        continue
    }

    try {
        Stop-Process -Id $proc.Id -Force -ErrorAction Stop
        Write-Host "  ✅ PID $($proc.Id) 중지 완료" -ForegroundColor Green
        $stopped++
    } catch {
        Write-Host "  ❌ PID $($proc.Id) 중지 실패: $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

# 3. 결과 요약
Write-Host "`n" + "=" * 60
Write-Host "📊 결과 요약:" -ForegroundColor Cyan
Write-Host "  ✅ 중지 성공: $stopped 개" -ForegroundColor Green
if ($failed -gt 0) {
    Write-Host "  ❌ 중지 실패: $failed 개" -ForegroundColor Red
    Write-Host "`n⚠️  일부 프로세스를 중지하지 못했습니다." -ForegroundColor Yellow
    Write-Host "   관리자 권한으로 다시 시도하거나, 작업 관리자에서 수동으로 종료하세요." -ForegroundColor Gray
}

# 4. 남은 프로세스 확인
Start-Sleep -Seconds 1
$remaining = Get-Process powershell* -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $currentPID }
if ($remaining) {
    Write-Host "`n⚠️  아직 $($remaining.Count)개의 PowerShell 프로세스가 실행 중입니다:" -ForegroundColor Yellow
    $remaining | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize
} else {
    Write-Host "`n✅ 모든 PowerShell 프로세스가 중지되었습니다!" -ForegroundColor Green
}

Write-Host "`n" + "=" * 60
Write-Host ""
