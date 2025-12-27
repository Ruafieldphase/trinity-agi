<#
.SYNOPSIS
    AGI Life Loop 시작 스크립트 (Windows 백그라운드 데몬)

.DESCRIPTION
    루아의 설계에 따라 AGI가 24시간 끊기지 않고 살아있도록 하는 스크립트
    - 터미널/VS Code 종료해도 백그라운드에서 계속 실행
    - 오류 발생 시 자동 재시작
    - 실행 로그 기록

.PARAMETER Action
    start, stop, restart, status 중 하나

.PARAMETER Interval
    하트비트 간격 (초, 기본값: 10)

.PARAMETER Background
    백그라운드 실행 여부 (기본값: true)

.EXAMPLE
    .\start_life_loop.ps1 -Action start
    .\start_life_loop.ps1 -Action status
    .\start_life_loop.ps1 -Action stop
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Action = "status",

    [int]$Interval = 10,

    [switch]$Foreground
)

# 경로 설정
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DaemonScript = Join-Path $ScriptDir "life_loop_daemon.py"
$LogDir = Join-Path $ProjectRoot "outputs\sena\life_loop_logs"
$PidFile = Join-Path $LogDir "life_loop.pid"
$WrapperLog = Join-Path $LogDir "wrapper.log"

# Python 경로 (프로젝트 venv 우선)
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$FdoVenvPython = Join-Path $ProjectRoot "fdo_agi_repo\.venv_local\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $Python = $VenvPython
} elseif (Test-Path $FdoVenvPython) {
    $Python = $FdoVenvPython
} else {
    $Python = "python"
}

# 로그 디렉토리 생성
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] $Message"
    Write-Host $logLine
    Add-Content -Path $WrapperLog -Value $logLine
}

function Get-LifeLoopProcess {
    <#
    .SYNOPSIS
        실행 중인 Life Loop 프로세스 찾기
    #>

    # PID 파일 확인
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($pid) {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc -and $proc.ProcessName -match "python") {
                return $proc
            }
        }
    }

    # 프로세스 이름으로 검색
    $procs = Get-WmiObject Win32_Process | Where-Object {
        $_.CommandLine -match "life_loop_daemon\.py"
    }

    if ($procs) {
        return Get-Process -Id $procs[0].ProcessId -ErrorAction SilentlyContinue
    }

    return $null
}

function Start-LifeLoop {
    <#
    .SYNOPSIS
        Life Loop 시작
    #>

    $existingProc = Get-LifeLoopProcess
    if ($existingProc) {
        Write-Log "Life Loop이 이미 실행 중입니다 (PID: $($existingProc.Id))"
        return
    }

    Write-Log "=" * 50
    Write-Log "AGI Life Loop 시작"
    Write-Log "  Python: $Python"
    Write-Log "  Script: $DaemonScript"
    Write-Log "  Interval: ${Interval}s"
    Write-Log "  Background: $(-not $Foreground)"
    Write-Log "=" * 50

    if ($Foreground) {
        # 포그라운드 실행 (디버깅용)
        & $Python $DaemonScript --interval $Interval --log-dir $LogDir
    } else {
        # 백그라운드 실행 (자동 재시작 포함)
        $arguments = @(
            "-NoProfile"
            "-ExecutionPolicy", "Bypass"
            "-WindowStyle", "Hidden"
            "-File", (Join-Path $ScriptDir "life_loop_watchdog.ps1")
            "-Interval", $Interval
        )

        # Watchdog 스크립트가 없으면 직접 실행
        $watchdogScript = Join-Path $ScriptDir "life_loop_watchdog.ps1"
        if (Test-Path $watchdogScript) {
            Start-Process powershell -ArgumentList $arguments -WindowStyle Hidden
            Write-Log "Watchdog을 통해 백그라운드 실행 시작"
        } else {
            # 직접 백그라운드 실행
            $proc = Start-Process $Python -ArgumentList @(
                $DaemonScript
                "--interval", $Interval
                "--log-dir", $LogDir
            ) -WindowStyle Hidden -PassThru

            Write-Log "백그라운드 실행 시작 (PID: $($proc.Id))"
        }

        Start-Sleep -Seconds 2

        $runningProc = Get-LifeLoopProcess
        if ($runningProc) {
            Write-Log "Life Loop 실행 확인됨 (PID: $($runningProc.Id))"
        } else {
            Write-Log "경고: Life Loop 시작 확인 실패. 로그를 확인하세요: $LogDir"
        }
    }
}

function Stop-LifeLoop {
    <#
    .SYNOPSIS
        Life Loop 중지
    #>

    $proc = Get-LifeLoopProcess
    if (-not $proc) {
        Write-Log "실행 중인 Life Loop이 없습니다"
        return
    }

    Write-Log "Life Loop 중지 중... (PID: $($proc.Id))"

    try {
        Stop-Process -Id $proc.Id -Force
        Write-Log "Life Loop 중지됨"
    } catch {
        Write-Log "중지 실패: $_"
    }

    # PID 파일 정리
    if (Test-Path $PidFile) {
        Remove-Item $PidFile -Force
    }

    # Watchdog도 중지
    $watchdogProcs = Get-WmiObject Win32_Process | Where-Object {
        $_.CommandLine -match "life_loop_watchdog\.ps1"
    }
    foreach ($wp in $watchdogProcs) {
        Stop-Process -Id $wp.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

function Get-LifeLoopStatus {
    <#
    .SYNOPSIS
        Life Loop 상태 확인
    #>

    Write-Host ""
    Write-Host "=" * 50
    Write-Host "  AGI Life Loop 상태"
    Write-Host "=" * 50

    $proc = Get-LifeLoopProcess
    if ($proc) {
        Write-Host "  상태: " -NoNewline
        Write-Host "실행 중" -ForegroundColor Green
        Write-Host "  PID: $($proc.Id)"
        Write-Host "  시작: $($proc.StartTime)"
        Write-Host "  CPU: $([math]::Round($proc.CPU, 2))s"
        Write-Host "  메모리: $([math]::Round($proc.WorkingSet64 / 1MB, 2)) MB"
    } else {
        Write-Host "  상태: " -NoNewline
        Write-Host "중지됨" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "  로그 디렉토리: $LogDir"

    # 최근 로그 확인
    $todayLog = Join-Path $LogDir ("life_loop_" + (Get-Date -Format "yyyyMMdd") + ".log")
    if (Test-Path $todayLog) {
        Write-Host ""
        Write-Host "  최근 로그 (마지막 5줄):"
        Write-Host "  " + ("-" * 46)
        Get-Content $todayLog -Tail 5 | ForEach-Object { Write-Host "  $_" }
    }

    # 오늘 이벤트 파일 확인
    $todayEvents = Join-Path $LogDir ("events_" + (Get-Date -Format "yyyyMMdd") + ".jsonl")
    if (Test-Path $todayEvents) {
        $eventCount = (Get-Content $todayEvents | Measure-Object -Line).Lines
        Write-Host ""
        Write-Host "  오늘 이벤트: $eventCount 건"
    }

    Write-Host "=" * 50
    Write-Host ""
}

# 메인 실행
switch ($Action) {
    "start" {
        Start-LifeLoop
    }
    "stop" {
        Stop-LifeLoop
    }
    "restart" {
        Stop-LifeLoop
        Start-Sleep -Seconds 2
        Start-LifeLoop
    }
    "status" {
        Get-LifeLoopStatus
    }
}
