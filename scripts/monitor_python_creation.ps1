# 파이썬 프로세스 생성 실시간 모니터링

Write-Host "`n👁️  파이썬 프로세스 생성 모니터링 (15초)" -ForegroundColor Cyan
Write-Host "=" * 60

$startTime = Get-Date
$duration = 15
$tracked = @{}

# 현재 존재하는 프로세스 기록
$existing = Get-Process python* -ErrorAction SilentlyContinue
foreach ($proc in $existing) {
    $tracked[$proc.Id] = $true
}

Write-Host "시작 시간: $($startTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
Write-Host "기존 프로세스: $($tracked.Count)개" -ForegroundColor Gray
Write-Host "모니터링 중...\`n" -ForegroundColor Yellow

$newProcessCount = 0

while ((Get-Date) -lt $startTime.AddSeconds($duration)) {
    $currentProcesses = Get-WmiObject Win32_Process | Where-Object {
        $_.Name -like "python*.exe"
    }

    foreach ($proc in $currentProcesses) {
        if (-not $tracked.ContainsKey($proc.ProcessId)) {
            # 새 프로세스 발견!
            Write-Host "🆕 새 파이썬 프로세스 발견!" -ForegroundColor Red
            Write-Host "   PID: $($proc.ProcessId)" -ForegroundColor Yellow
            Write-Host "   이름: $($proc.Name)" -ForegroundColor Gray
            Write-Host "   생성: $($proc.CreationDate)" -ForegroundColor Gray

            # 부모 프로세스
            if ($proc.ParentProcessId) {
                $parent = Get-WmiObject Win32_Process | Where-Object { $_.ProcessId -eq $proc.ParentProcessId }
                if ($parent) {
                    Write-Host "   부모: $($parent.Name) (PID: $($parent.ProcessId))" -ForegroundColor Cyan
                    if ($parent.CommandLine) {
                        $cmdLine = $parent.CommandLine
                        if ($cmdLine.Length -gt 100) {
                            $cmdLine = $cmdLine.Substring(0, 100) + "..."
                        }
                        Write-Host "   부모 명령: $cmdLine" -ForegroundColor White
                    }
                } else {
                    Write-Host "   부모: 없음 (PID: $($proc.ParentProcessId))" -ForegroundColor Red
                }
            }

            # 명령행
            if ($proc.CommandLine) {
                $cmdLine = $proc.CommandLine
                if ($cmdLine.Length -gt 150) {
                    $cmdLine = $cmdLine.Substring(0, 150) + "..."
                }
                Write-Host "   명령: $cmdLine" -ForegroundColor White
            } else {
                Write-Host "   명령: (정보 없음 - 권한 필요)" -ForegroundColor Red
            }

            Write-Host ""

            $tracked[$proc.ProcessId] = $true
            $newProcessCount++
        }
    }

    Start-Sleep -Milliseconds 500
}

$endTime = Get-Date
Write-Host "" + "=" * 60
Write-Host "종료 시간: $($endTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
Write-Host "감지된 새 프로세스: $newProcessCount 개" -ForegroundColor $(if ($newProcessCount -eq 0) { "Green" } else { "Red" })

if ($newProcessCount -gt 0) {
    Write-Host "`n⚠️  파이썬 프로세스가 계속 생성되고 있습니다!" -ForegroundColor Red
    Write-Host "   부모 프로세스를 중지해야 합니다." -ForegroundColor Yellow
} else {
    Write-Host "`n✅ 새로운 파이썬 프로세스 생성 없음" -ForegroundColor Green
}

Write-Host ""