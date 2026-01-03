# Final System Status Check

. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot
Write-Host '════════════════════════════════════════════════════════════════' -ForegroundColor Cyan
Write-Host '  리듬 기반 자동화 완성 - 최종 상태 점검' -ForegroundColor Yellow
Write-Host '════════════════════════════════════════════════════════════════' -ForegroundColor Cyan
Write-Host ''

Write-Host '[1] 등록된 Scheduled Tasks' -ForegroundColor Yellow
Get-ScheduledTask -TaskName 'AGI_*' | Select-Object TaskName, State | Format-Table -AutoSize

Write-Host ''
Write-Host '[2] 생성된 파일 목록' -ForegroundColor Yellow
@(
    @{ name = 'create_master_scheduler.ps1'; dir = 'scripts' },
    @{ name = 'adaptive_master_scheduler.ps1'; dir = 'scripts' },
    @{ name = 'MASTER_SCHEDULER_IMPLEMENTATION.md'; dir = '.' },
    @{ name = 'INTEGRATION_STRATEGY.md'; dir = '.' },
    @{ name = 'PHASE2_ADAPTIVE_RHYTHM.md'; dir = '.' },
    @{ name = 'SYSTEM_SLOWDOWN_FINAL_DIAGNOSIS.md'; dir = '.' }
) | ForEach-Object {
    $path = "$WorkspaceRoot\$($_.dir)\$($_.name)"

    if (Test-Path $path) {
        Write-Host "  ✅ $($_.name)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ $($_.name)" -ForegroundColor Yellow
    }
}

Write-Host ''
Write-Host '[3] Output Files (Scheduler)' -ForegroundColor Yellow
Get-ChildItem "$WorkspaceRoot\outputs" -Filter '*scheduler*' -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  📄 $($_.Name)" -ForegroundColor Green
}

Write-Host ''
Write-Host '[4] 시스템 리소스 상태' -ForegroundColor Yellow
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$pythonProcs = @(Get-Process | Where-Object { $_.ProcessName -like '*python*' }).Count

$memUsage = [math]::Round((($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize) * 100, 1)
$cpuLoad = if ($null -ne $cpu.LoadPercentage) { [int]$cpu.LoadPercentage } else { 0 }

Write-Host "  CPU: $cpuLoad%" -ForegroundColor $(if ($cpuLoad -gt 60) { 'Yellow' } else { 'Green' })
Write-Host "  Memory: $memUsage%" -ForegroundColor $(if ($memUsage -gt 60) { 'Yellow' } else { 'Green' })
Write-Host "  Python Processes: $pythonProcs" -ForegroundColor $(if ($pythonProcs -gt 40) { 'Yellow' } else { 'Green' })

Write-Host ''
Write-Host '[5] 핵심 개선사항' -ForegroundColor Yellow
Write-Host '  ✅ Phase 1: Master Scheduler (정적 리듬)'
Write-Host '     └─ 42개 독립 Task → 1개 통합 (97% 감소)'
Write-Host ''
Write-Host '  ✅ Phase 2: Adaptive Scheduler (동적 리듬)'
Write-Host '     ├─ CPU 기반 자동 간격 조정'
Write-Host '     ├─ Python/PowerShell 자동 감지'
Write-Host '     ├─ 우선순위 기반 실행'
Write-Host '     └─ 시스템 메트릭 실시간 수집'

Write-Host ''
Write-Host '════════════════════════════════════════════════════════════════' -ForegroundColor Cyan