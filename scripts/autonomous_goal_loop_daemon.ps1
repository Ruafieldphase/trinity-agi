# Auto-generated adaptive rhythm daemon script
param(
    [switch]$Once
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"

# Workspace root (SSOT)

# Paths
$PythonExe = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
$ExecutorScript = Join-Path $WorkspaceRoot "scripts\autonomous_goal_executor.py"
$RhythmCalculator = Join-Path $WorkspaceRoot "scripts\adaptive_rhythm_calculator.py"

# Files
$LogFile = Join-Path $WorkspaceRoot "outputs\autonomous_goal_loop.log"
$StatusFile = Join-Path $WorkspaceRoot "outputs\autonomous_goal_loop_status.json"
$StopFlag = Join-Path $WorkspaceRoot "outputs\stop_autonomous_goal_loop.flag"

# Utilities
function Write-StatusJson {
    param(
        [string]$phase,
        [int]$intervalMinutes,
        [int]$failureCount,
        [string]$lastResult,
        [datetime]$nextRun
    )
    try {
        $obj = [ordered]@{
            timestamp      = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
            phase          = $phase
            running        = $true
            interval_min   = $intervalMinutes
            failure_count  = $failureCount
            last_result    = $lastResult
            next_run_local = $nextRun.ToString('yyyy-MM-dd HH:mm:ss')
        }
        ($obj | ConvertTo-Json -Depth 5) | Out-File -FilePath $StatusFile -Encoding UTF8 -Force
    }
    catch {}
}

# Resolve python executable
if (-not (Test-Path -LiteralPath $PythonExe)) {
    $PythonExe = "python"
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 🌊 자율 목표 루프 시작 (적응형 리듬)" -ForegroundColor Green
"[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 적응형 리듬 루프 시작" | Out-File -FilePath $LogFile -Append

# Single-instance guard (global mutex)
$createdNew = $false
try {
    $global:GoalLoopMutex = New-Object System.Threading.Mutex($true, 'Global/AGI_AutonomousGoalLoop', [ref]$createdNew)
}
catch {
    $createdNew = $false
}
if (-not $createdNew) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️ 이미 실행 중인 루프가 감지되어 종료합니다." -ForegroundColor Yellow
    exit 0
}

$failureCount = 0

function Get-IntervalMinutes {
    param([int]$default = 10)
    try {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 🎵 리듬 계산 중..." -ForegroundColor Cyan
        $rhythmJson = & $PythonExe $RhythmCalculator 2>&1 | Out-String
        $rhythm = $rhythmJson | ConvertFrom-Json -ErrorAction Stop
        $interval = [int]$rhythm.next_interval_minutes
        if ($interval -le 0) { return $default }
        return $interval
    }
    catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️ 리듬 계산 실패. 기본 $default 분 사용" -ForegroundColor Yellow
        return $default
    }
}

function Health-Gate {
    try {
        $healthScript = Join-Path $WorkspaceRoot "scripts\run_quick_health.ps1"
        if (Test-Path -LiteralPath $healthScript) {
            & $healthScript -JsonOnly -Fast -TimeoutSec 10 -MaxDuration 8 | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 🛑 헬스 게이트: 시스템 상태 저하로 실행 건너뜀" -ForegroundColor Red
                return $false
            }
        }
        return $true
    }
    catch {
        # 헬스 체크 실패시 보수적으로 통과 (워치독이 별도 보호)
        return $true
    }
}

try {
    while ($true) {
        try {
            # Stop flag check
            if (Test-Path -LiteralPath $StopFlag) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⏹️ 정지 플래그 감지. 루프 종료." -ForegroundColor Yellow
                break
            }

            # 1. 현재 리듬 계산
            $intervalMinutes = Get-IntervalMinutes -default 10
        
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 🎯 다음 간격: $intervalMinutes 분" -ForegroundColor Yellow
            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 다음 간격: $intervalMinutes 분" | Out-File -FilePath $LogFile -Append
        
            # 1.5 Health gate
            if (-not (Health-Gate)) {
                $failureCount += 1
                $penalty = [math]::Min(3.0, 1.0 + ($failureCount * 0.5))
                $adjInterval = [int][math]::Ceiling([double]$intervalMinutes * $penalty)
                $nextTimeHG = (Get-Date).AddMinutes($adjInterval)
                Write-StatusJson -phase 'health-gated' -intervalMinutes $adjInterval -failureCount $failureCount -lastResult 'skipped' -nextRun $nextTimeHG
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 💤 다음 실행(헬스 게이트): $($nextTimeHG.ToString('HH:mm')) (약 $adjInterval 분 후)" -ForegroundColor Gray
                Start-Sleep -Seconds ($adjInterval * 60)
                if ($Once) { break }
                continue
            }

            # 1.6 Goal Pre-validation: 실행할 목표가 있는지 확인
            $trackerPath = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\goal_tracker.json"
            $hasGoals = $false
            if (Test-Path -LiteralPath $trackerPath) {
                try {
                    $tracker = Get-Content -LiteralPath $trackerPath -Raw -Encoding UTF8 | ConvertFrom-Json
                    $activeGoals = $tracker.goals | Where-Object { $_.status -in @('pending', 'in_progress', 'failed') }
                    $hasGoals = ($activeGoals.Count -gt 0)
                }
                catch {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️ goal_tracker.json 읽기 실패" -ForegroundColor Yellow
                }
            }

            # 1.7 목표가 없으면 자동으로 생성
            if (-not $hasGoals) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 📝 실행할 목표 없음. 자동 생성 중..." -ForegroundColor Yellow
                "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 목표 자동 생성 시도" | Out-File -FilePath $LogFile -Append
                
                $generatorScript = Join-Path $WorkspaceRoot "scripts\autonomous_goal_generator.py"
                if (Test-Path -LiteralPath $generatorScript) {
                    try {
                        & $PythonExe $generatorScript --hours 24 2>&1 | Out-File -FilePath $LogFile -Append
                        if ($LASTEXITCODE -eq 0) {
                            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ 목표 생성 완료" -ForegroundColor Green
                            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 목표 생성 성공" | Out-File -FilePath $LogFile -Append
                        }
                        else {
                            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️ 목표 생성 실패: $LASTEXITCODE" -ForegroundColor Yellow
                            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 목표 생성 실패: $LASTEXITCODE" | Out-File -FilePath $LogFile -Append
                        }
                    }
                    catch {
                        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ 목표 생성 오류: $_" -ForegroundColor Red
                    }
                }
            }

            # 2. Goal Executor 실행 (Quantum Mode)
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 🚀 Goal Executor 실행 중 (Quantum Mode)..." -ForegroundColor Cyan
            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Executor 시작 (Quantum)" | Out-File -FilePath $LogFile -Append
        
            & $PythonExe $ExecutorScript --use-quantum 2>&1 | Out-File -FilePath $LogFile -Append
        
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ 완료" -ForegroundColor Green
                "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 성공" | Out-File -FilePath $LogFile -Append
                $failureCount = 0
                $last = 'success'
            }
            else {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️  종료 코드: $LASTEXITCODE" -ForegroundColor Yellow
                "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 실패: $LASTEXITCODE" | Out-File -FilePath $LogFile -Append
                $failureCount += 1
                $last = "failed:$LASTEXITCODE"
            }
        }
        catch {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ 오류: $_" -ForegroundColor Red
            "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] 오류: $_" | Out-File -FilePath $LogFile -Append
            $intervalMinutes = 15  # fallback
            $failureCount += 1
            $last = 'error'
        }
    
        # 실패 백오프 + 지터
        $penalty = [math]::Min(3.0, 1.0 + ($failureCount * 0.5))
        $adjIntervalMin = [int][math]::Ceiling([double]$intervalMinutes * $penalty)
        $jitterSec = Get-Random -Minimum 0 -Maximum ([math]::Min(60, [int]($adjIntervalMin * 60 * 0.1)))
        $nextRun = (Get-Date).AddMinutes($adjIntervalMin).AddSeconds($jitterSec)
        Write-StatusJson -phase 'sleep' -intervalMinutes $adjIntervalMin -failureCount $failureCount -lastResult $last -nextRun $nextRun
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 💤 다음 실행: $($nextRun.ToString('HH:mm')) (약 $adjIntervalMin 분 후 + 지터 ${jitterSec}s)" -ForegroundColor Gray
        if ($Once) { break }
        Start-Sleep -Seconds (($adjIntervalMin * 60) + $jitterSec)
    }
}
finally {
    if ($null -ne $global:GoalLoopMutex) { try { $global:GoalLoopMutex.ReleaseMutex() | Out-Null } catch {} }
}