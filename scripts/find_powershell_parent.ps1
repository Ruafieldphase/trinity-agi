# PowerShell을 생성하는 부모 프로세스 찾기

Write-Host "`n🔍 PowerShell 부모 프로세스 추적" -ForegroundColor Cyan
Write-Host "=" * 60

$psProcesses = Get-WmiObject Win32_Process | Where-Object { $_.Name -like "powershell*.exe" }

foreach ($proc in $psProcesses) {
    Write-Host "`n📋 PowerShell PID: $($proc.ProcessId)" -ForegroundColor Yellow
    Write-Host "   시작 시간: $($proc.CreationDate)" -ForegroundColor Gray
    Write-Host "   명령행: $($proc.CommandLine)" -ForegroundColor White

    # 부모 프로세스 찾기
    if ($proc.ParentProcessId) {
        $parent = Get-WmiObject Win32_Process | Where-Object { $_.ProcessId -eq $proc.ParentProcessId }
        if ($parent) {
            Write-Host "   부모 프로세스: $($parent.Name) (PID: $($parent.ProcessId))" -ForegroundColor Cyan
            Write-Host "   부모 명령행: $($parent.CommandLine)" -ForegroundColor Gray
        } else {
            Write-Host "   부모 프로세스: 없음 (PID: $($proc.ParentProcessId))" -ForegroundColor Red
        }
    }
}

Write-Host "`n" + "=" * 60
Write-Host ""
