<# 
Ensure Trigger Listener (Windowless, single instance)

목적:
- trigger_listener.py를 "한 프로세스"로 백그라운드 상시 구동
- --once 스케줄러가 다발적으로 떠서 프로세스/메모리 누수가 생기지 않게 방지

원칙:
- 창 없이(=pythonw) 실행
- 중복 실행 방지(락 파일)
- 코드 업데이트 시 자동 재시작(best-effort)
#>

param(
    [switch]$ForceRestart,
    [switch]$Silent
)

$ErrorActionPreference = "SilentlyContinue"

$WORKSPACE_ROOT = Resolve-Path "$PSScriptRoot\.."
$SCRIPT_PATH = "$WORKSPACE_ROOT\scripts\trigger_listener.py"
$PID_FILE = "$WORKSPACE_ROOT\outputs\trigger_listener.pid"
$LOCK_FILE = "$WORKSPACE_ROOT\outputs\trigger_listener.ensure.lock"
$PYW = "$WORKSPACE_ROOT\.venv\Scripts\pythonw.exe"
if (-not (Test-Path $PYW)) { $PYW = "pythonw.exe" }
if (-not (Get-Command $PYW -ErrorAction SilentlyContinue)) { $PYW = "C:\Python313\pythonw.exe" }

# 0) Best-effort single-flight lock
try {
    if (Test-Path $LOCK_FILE) {
        try {
            $lockAgeSec = ((Get-Date) - (Get-Item $LOCK_FILE).LastWriteTime).TotalSeconds
            if ($lockAgeSec -gt 120) { Remove-Item -LiteralPath $LOCK_FILE -Force -ErrorAction SilentlyContinue }
        } catch { }
    }
    New-Item -ItemType File -Path $LOCK_FILE -ErrorAction Stop | Out-Null
} catch {
    exit 0
}

try {
    $running = $false
    $needRestart = $false
    $proc = $null

    # 1) PID file check
    if (Test-Path $PID_FILE) {
        $pid_val = (Get-Content $PID_FILE -Raw).Trim()
        if ($pid_val -match "^\d+$") {
            $proc = Get-Process -Id $pid_val -ErrorAction SilentlyContinue
            if ($proc) {
                # If an old listener is still running with --auto-policy, force a restart.
                try {
                    $pinfo = Get-CimInstance Win32_Process -Filter "ProcessId=$pid_val" -ErrorAction SilentlyContinue
                    $cmd = ($pinfo.CommandLine | Out-String).Trim()
                    if ($cmd -match "--auto-policy") {
                        $needRestart = $true
                        try { Stop-Process -Id $pid_val -Force -ErrorAction SilentlyContinue } catch { }
                        $proc = $null
                        $running = $false
                    } else {
                        $running = $true
                    }
                } catch {
                    $running = $true
                }
            }
        }
    }

    # 2) Code update detection
    try {
        if ($running) {
            $scriptTime = (Get-Item $SCRIPT_PATH).LastWriteTime
            $startTime = $proc.StartTime
            if ($scriptTime -gt $startTime) { $needRestart = $true }
        }
    } catch { }

    if ($ForceRestart) { $needRestart = $true }

    # 3) De-duplicate: keep only the newest root instance
    try {
        $procs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
          Where-Object { $_.CommandLine -and $_.CommandLine -like "*trigger_listener.py*" -and $_.Name -match "python" }
        $procList = @($procs)

        # Remove any lingering auto-policy listeners (policy generation is handled by scheduler tasks).
        $autoPolicy = @($procList | Where-Object { $_.CommandLine -match "--auto-policy" })
        if ($autoPolicy.Count -gt 0) {
            foreach ($d in $autoPolicy) {
                try { Stop-Process -Id $d.ProcessId -Force -ErrorAction SilentlyContinue } catch { }
            }
            Start-Sleep -Milliseconds 200
            $procList = @($procList | Where-Object { $_.CommandLine -notmatch "--auto-policy" })
            $running = $false
        }

        if ($needRestart -and $procList.Count -gt 0) {
            foreach ($d in $procList) {
                try { Stop-Process -Id $d.ProcessId -Force -ErrorAction SilentlyContinue } catch { }
            }
            Start-Sleep -Milliseconds 200
            $procList = @()
            $running = $false
        } elseif ($procList.Count -gt 1) {
            # Multiple listeners detected (often due to layered autostart). Keep only the newest one.
            $keep = ($procList | Sort-Object { $_.CreationDate } -Descending | Select-Object -First 1)
            foreach ($d in $procList) {
                if ($keep -and ($d.ProcessId -eq $keep.ProcessId)) { continue }
                try { Stop-Process -Id $d.ProcessId -Force -ErrorAction SilentlyContinue } catch { }
            }
            Start-Sleep -Milliseconds 200
            if ($keep) {
                $keep.ProcessId | Out-File $PID_FILE -Encoding ascii -Force
                $running = $true
            } else {
                $running = $false
            }
        }
    } catch { }

    # 4) Start if not running
    if (-not $running) {
        # NOTE: auto_policy는 스케줄러(AGI_LuaAutoPolicy)에서만 돌린다.
        #       trigger_listener는 트리거 소비자(리스너)로만 상시 유지한다.
        $args = @("""$SCRIPT_PATH""", "--silent")
        $p = Start-Process -FilePath $PYW -ArgumentList $args -WorkingDirectory $WORKSPACE_ROOT -WindowStyle Hidden -PassThru
        $p.Id | Out-File $PID_FILE -Encoding ascii -Force
    }
} finally {
    try { Remove-Item -LiteralPath $LOCK_FILE -Force -ErrorAction SilentlyContinue } catch { }
}