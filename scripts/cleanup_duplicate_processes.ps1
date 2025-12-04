# 중복 프로세스 정리 스크립트
# 안전하게 중복된 프로세스만 종료하고 1개씩만 유지

param(
    [switch]$DryRun = $false,
    [switch]$Force = $false
)

Write-Host "`n╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  중복 프로세스 정리                                  ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "🔍 DRY-RUN 모드 (실제 종료하지 않음)`n" -ForegroundColor Yellow
}

# 안전하게 유지해야 할 프로세스
$keepAlive = @(
    "task_queue_server.py",
    "ai_ops_manager.ps1",
    "adaptive_master_scheduler.ps1"
)

# 중복 정리 대상
$targets = @(
    @{
        Name        = "monitoring_daemon.py"
        MaxCount    = 1
        Description = "모니터링 데몬"
    },
    @{
        Name        = "self_healing_watchdog.ps1"
        MaxCount    = 1
        Description = "자가 치유 워치독"
    },
    @{
        Name        = "task_watchdog.py"
        MaxCount    = 1
        Description = "Task 워치독"
    },
    @{
        Name        = "rpa_worker.py"
        MaxCount    = 1
        Description = "RPA Worker"
    },
    @{
        Name        = "simple_autonomous_worker.py"
        MaxCount    = 1
        Description = "자율 작업 처리"
    }
)

$totalKilled = 0

foreach ($target in $targets) {
    $scriptName = $target.Name
    $maxCount = $target.MaxCount
    $desc = $target.Description
    
    Write-Host "🔍 검사: $desc ($scriptName)" -ForegroundColor Cyan
    
    # 해당 스크립트를 실행 중인 프로세스 찾기
    $processes = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine
        $cmdLine -like "*$scriptName*" -and $cmdLine -notlike "*cleanup_duplicate_processes*"
    } | Sort-Object StartTime
    
    $count = ($processes | Measure-Object).Count
    
    if ($count -le $maxCount) {
        Write-Host "  ✅ 정상: $count 개 실행 중 (유지)" -ForegroundColor Green
        continue
    }
    
    # 중복 개수
    $duplicates = $count - $maxCount
    Write-Host "  ⚠️  중복 발견: $count 개 중 $duplicates 개 제거 필요" -ForegroundColor Yellow
    
    # 가장 오래된 것을 유지하고 나머지 제거
    $toKeep = $processes | Select-Object -First $maxCount
    $toKill = $processes | Select-Object -Skip $maxCount
    
    Write-Host "  📋 유지할 프로세스:" -ForegroundColor Green
    foreach ($p in $toKeep) {
        Write-Host "     PID $($p.Id) (시작: $($p.StartTime))" -ForegroundColor Gray
    }
    
    Write-Host "  🗑️  제거할 프로세스:" -ForegroundColor Red
    foreach ($p in $toKill) {
        Write-Host "     PID $($p.Id) (시작: $($p.StartTime))" -ForegroundColor Gray
        
        if (-not $DryRun) {
            try {
                Stop-Process -Id $p.Id -Force -ErrorAction Stop
                Write-Host "     ✅ 종료 완료" -ForegroundColor Green
                $totalKilled++
            }
            catch {
                Write-Host "     ❌ 종료 실패: $_" -ForegroundColor Red
            }
        }
    }
    
    Write-Host ""
}

# 요약
Write-Host "`n╔═══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  정리 완료                                            ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════╝`n" -ForegroundColor Green

if ($DryRun) {
    Write-Host "🔍 DRY-RUN 결과:" -ForegroundColor Yellow
    Write-Host "   제거 예정: $totalKilled 개 프로세스`n" -ForegroundColor Yellow
    Write-Host "💡 실제 실행:" -ForegroundColor Cyan
    Write-Host "   .\scripts\cleanup_duplicate_processes.ps1`n" -ForegroundColor White
}
else {
    Write-Host "✅ 종료된 프로세스: $totalKilled 개`n" -ForegroundColor Green
}

# 최종 상태 확인
Write-Host "📊 현재 실행 중인 핵심 프로세스:" -ForegroundColor Cyan

$coreProcesses = @(
    "task_queue_server.py",
    "ai_ops_manager.ps1",
    "adaptive_master_scheduler.ps1",
    "monitoring_daemon.py",
    "self_healing_watchdog.ps1",
    "task_watchdog.py",
    "rpa_worker.py",
    "simple_autonomous_worker.py"
)

foreach ($scriptName in $coreProcesses) {
    $processes = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine
        $cmdLine -like "*$scriptName*"
    }
    
    $count = ($processes | Measure-Object).Count
    
    if ($count -eq 0) {
        Write-Host "  ❌ $scriptName`: 실행 안됨" -ForegroundColor Red
    }
    elseif ($count -eq 1) {
        Write-Host "  ✅ $scriptName`: $count 개 (정상)" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠️  $scriptName`: $count 개 (중복!)" -ForegroundColor Yellow
    }
}

Write-Host ""
