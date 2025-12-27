<#
.SYNOPSIS
    Life Loop Watchdog - 자동 재시작 담당

.DESCRIPTION
    Life Loop Daemon이 죽으면 자동으로 재시작하는 워치독
    - 30초마다 프로세스 상태 확인
    - 비정상 종료 시 자동 재시작
    - 모든 이벤트 로그 기록

.NOTES
    이 스크립트는 start_life_loop.ps1에서 호출됩니다.
    직접 실행하지 마세요.
#>

param(
    [int]$Interval = 10,
    [int]$CheckInterval = 30,
    [int]$MaxRestarts = 100
)

$ErrorActionPreference = "Continue"

# 경로 설정
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DaemonScript = Join-Path $ScriptDir "life_loop_daemon.py"
$LogDir = Join-Path $ProjectRoot "outputs\sena\life_loop_logs"
$PidFile = Join-Path $LogDir "life_loop.pid"
$WatchdogLog = Join-Path $LogDir "watchdog.log"
$WatchdogPidFile = Join-Path $LogDir "watchdog.pid"

# Python 경로
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

# Watchdog PID 기록
Set-Content -Path $WatchdogPidFile -Value $PID

function Write-WatchdogLog {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [WATCHDOG] $Message"
    Add-Content -Path $WatchdogLog -Value $logLine
}

function Get-DaemonProcess {
    # PID 파일로 확인
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($pid) {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc -and $proc.ProcessName -match "python") {
                return $proc
            }
        }
    }

    # 명령줄로 검색
    $procs = Get-WmiObject Win32_Process | Where-Object {
        $_.CommandLine -match "life_loop_daemon\.py"
    }

    if ($procs) {
        return Get-Process -Id $procs[0].ProcessId -ErrorAction SilentlyContinue
    }

    return $null
}

function Start-Daemon {
    Write-WatchdogLog "Life Loop Daemon 시작 중..."

    $proc = Start-Process $Python -ArgumentList @(
        $DaemonScript
        "--interval", $Interval
        "--log-dir", $LogDir
    ) -WindowStyle Hidden -PassThru

    if ($proc) {
        Write-WatchdogLog "Daemon 시작됨 (PID: $($proc.Id))"
        return $proc.Id
    } else {
        Write-WatchdogLog "ERROR: Daemon 시작 실패"
        return $null
    }
}

# 메인 루프
Write-WatchdogLog "=" * 50
Write-WatchdogLog "Watchdog 시작 (PID: $PID)"
Write-WatchdogLog "  Daemon Script: $DaemonScript"
Write-WatchdogLog "  Check Interval: ${CheckInterval}s"
Write-WatchdogLog "  Max Restarts: $MaxRestarts"
Write-WatchdogLog "=" * 50

$restartCount = 0

while ($true) {
    $proc = Get-DaemonProcess

    if (-not $proc) {
        Write-WatchdogLog "Daemon이 실행 중이지 않음 - 재시작 시도 #$($restartCount + 1)"

        if ($restartCount -ge $MaxRestarts) {
            Write-WatchdogLog "ERROR: 최대 재시작 횟수 도달 - Watchdog 종료"
            break
        }

        $newPid = Start-Daemon

        if ($newPid) {
            $restartCount++
            Write-WatchdogLog "재시작 성공 (총 재시작: $restartCount)"
        } else {
            Write-WatchdogLog "재시작 실패 - 60초 후 재시도"
            Start-Sleep -Seconds 60
        }
    } else {
        # 정상 실행 중 - 상태 기록 (10분마다)
        if ((Get-Date).Minute % 10 -eq 0 -and (Get-Date).Second -lt $CheckInterval) {
            $uptime = (Get-Date) - $proc.StartTime
            Write-WatchdogLog "상태 양호 - PID: $($proc.Id), Uptime: $([math]::Round($uptime.TotalMinutes, 1))분"
        }
    }

    Start-Sleep -Seconds $CheckInterval
}

# 정리
if (Test-Path $WatchdogPidFile) {
    Remove-Item $WatchdogPidFile -Force
}

Write-WatchdogLog "Watchdog 종료"
