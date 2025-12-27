# 파이썬 프로세스의 명령행 확인

Write-Host "`n🐍 파이썬 프로세스 상세 정보" -ForegroundColor Cyan
Write-Host "=" * 80

$pythonProcesses = Get-WmiObject Win32_Process | Where-Object {
    $_.Name -like "python*.exe"
} | Sort-Object CreationDate -Descending

Write-Host "`n총 $($pythonProcesses.Count)개의 파이썬 프로세스 발견`n" -ForegroundColor Yellow

$recent = $pythonProcesses | Select-Object -First 10

foreach ($proc in $recent) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "PID: $($proc.ProcessId)" -ForegroundColor Yellow
    Write-Host "생성: $($proc.CreationDate)" -ForegroundColor Gray
    Write-Host "명령행:" -ForegroundColor Cyan
    if ($proc.CommandLine) {
        Write-Host "  $($proc.CommandLine)" -ForegroundColor White
    } else {
        Write-Host "  (명령행 정보 없음)" -ForegroundColor Red
    }

    # 부모 프로세스
    if ($proc.ParentProcessId) {
        $parent = Get-WmiObject Win32_Process | Where-Object { $_.ProcessId -eq $proc.ParentProcessId }
        if ($parent) {
            Write-Host "부모: $($parent.Name) (PID: $($parent.ProcessId))" -ForegroundColor Cyan
        }
    }
}

Write-Host "`n" + "=" * 80
Write-Host ""
