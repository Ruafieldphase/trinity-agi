# PowerShell 프로세스 생성 실시간 모니터링
# ==========================================
# 10초 동안 PowerShell 프로세스 생성을 감시합니다

Write-Host "`n👁️  PowerShell 프로세스 생성 모니터링 (10초)" -ForegroundColor Cyan
Write-Host "=" * 60

$startTime = Get-Date
$duration = 10
$lastCheck = @{}

Write-Host "시작 시간: $($startTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
Write-Host "모니터링 중...\`n" -ForegroundColor Yellow

while ((Get-Date) -lt $startTime.AddSeconds($duration)) {
    $currentProcesses = Get-Process powershell* -ErrorAction SilentlyContinue

    foreach ($proc in $currentProcesses) {
        if (-not $lastCheck.ContainsKey($proc.Id)) {
            # 새로운 프로세스 발견!
            Write-Host "🆕 새 PowerShell 프로세스 발견!" -ForegroundColor Red
            Write-Host "   PID: $($proc.Id)" -ForegroundColor Yellow
            Write-Host "   시작: $($proc.StartTime)" -ForegroundColor Gray

            # 부모 프로세스 찾기
            $wmiProc = Get-WmiObject Win32_Process | Where-Object { $_.ProcessId -eq $proc.Id }
            if ($wmiProc -and $wmiProc.ParentProcessId) {
                $parent = Get-WmiObject Win32_Process | Where-Object { $_.ProcessId -eq $wmiProc.ParentProcessId }
                if ($parent) {
                    Write-Host "   부모: $($parent.Name) (PID: $($parent.ProcessId))" -ForegroundColor Cyan
                    Write-Host "   부모 명령: $($parent.CommandLine)" -ForegroundColor White
                }
            }

            $lastCheck[$proc.Id] = $true
        }
    }

    Start-Sleep -Milliseconds 500
}

$endTime = Get-Date
Write-Host "`n" + "=" * 60
Write-Host "종료 시간: $($endTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
Write-Host "감지된 새 프로세스: $($lastCheck.Count)개" -ForegroundColor $(if ($lastCheck.Count -eq 0) { "Green" } else { "Red" })
Write-Host ""
