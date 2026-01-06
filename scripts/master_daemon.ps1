<#
.SYNOPSIS
AGI Master Daemon - 모든 AGI 작업을 하나의 프로세스에서 제어

.DESCRIPTION
단일 백그라운드 프로세스로 모든 AGI 작업을 관리합니다.
- 중앙 집중식 제어
- 통합 로깅
- 자동 재시작
- 창 관리
#>

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Status,
    [string]$ConfigPath = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\config\master_daemon_config.json"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"

# 로깅 함수
function Write-DaemonLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # 콘솔 출력
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "Cyan" }
    }
    Write-Host $logEntry -ForegroundColor $color
    
    # 파일 로깅
    $logPath = "$WorkspaceRoot\outputs\master_daemon.log"
    Add-Content -Path $logPath -Value $logEntry -Force -ErrorAction SilentlyContinue
}

# PSCustomObject를 Hashtable로 변환
function ConvertTo-Hashtable {
    param([Parameter(ValueFromPipeline)]$InputObject)
    
    if ($null -eq $InputObject) { return $null }
    
    if ($InputObject -is [System.Collections.IDictionary]) {
        return $InputObject
    }
    
    if ($InputObject -is [System.Collections.IEnumerable] -and $InputObject -isnot [string]) {
        $collection = @()
        foreach ($item in $InputObject) {
            $collection += ConvertTo-Hashtable $item
        }
        return $collection
    }
    
    if ($InputObject -is [PSCustomObject]) {
        $hash = @{}
        foreach ($prop in $InputObject.PSObject.Properties) {
            $hash[$prop.Name] = ConvertTo-Hashtable $prop.Value
        }
        return $hash
    }
    
    return $InputObject
}

# 설정 로드
function Get-DaemonConfig {
    param([string]$Path)
    
    if (!(Test-Path $Path)) {
        Write-DaemonLog "Config file not found: $Path" "ERROR"
        return $null
    }
    
    try {
        $config = Get-Content $Path -Raw | ConvertFrom-Json | ConvertTo-Hashtable
        Write-DaemonLog "Configuration loaded from $Path" "SUCCESS"
        return $config
    }
    catch {
        Write-DaemonLog "Failed to load config: $_" "ERROR"
        return $null
    }
}

# 프로세스 관리
$script:ManagedProcesses = @{}

function Start-ManagedTask {
    param(
        [string]$TaskName,
        [hashtable]$TaskConfig,
        [object]$GlobalConfig
    )
    
    if ($script:ManagedProcesses.ContainsKey($TaskName)) {
        $proc = $script:ManagedProcesses[$TaskName]
        if ($proc -and !$proc.HasExited) {
            Write-DaemonLog "$TaskName is already running (PID: $($proc.Id))" "WARN"
            return $proc
        }
    }
    
    try {
        $scriptPath = Join-Path $WorkspaceRoot $TaskConfig.script
        
        if (!(Test-Path $scriptPath)) {
            Write-DaemonLog "Script not found: $scriptPath" "ERROR"
            return $null
        }
        
        # Arguments 생성
        $argList = @()
        
        if ($TaskConfig.pythonVenv) {
            # Python 스크립트
            $pythonExe = Join-Path $WorkspaceRoot $TaskConfig.pythonVenv
            # 창 없는 실행을 우선한다 (pythonw가 있으면 사용).
            # - python.exe는 WindowStyle Hidden이어도 '깜빡임'이 발생할 수 있다.
            # - pythonw.exe는 콘솔 창을 만들지 않으므로 사용자 체감이 안정적이다.
            try {
                if ($TaskConfig.hidden -eq $true -and $pythonExe -match "python\\.exe$") {
                    $pythonwExe = Join-Path (Split-Path -Parent $pythonExe) "pythonw.exe"
                    if (Test-Path $pythonwExe) { $pythonExe = $pythonwExe }
                }
            }
            catch { }
            $argList = @($scriptPath) + $TaskConfig.args
            $executable = $pythonExe
        }
        else {
            # PowerShell 스크립트
            $argList = @(
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-File", $scriptPath
            ) + $TaskConfig.args
            $executable = "powershell.exe"
        }
        
        Write-DaemonLog "Starting $TaskName..." "INFO"
        $proc = Start-Process -FilePath $executable -ArgumentList $argList -WindowStyle Hidden -PassThru
        
        $script:ManagedProcesses[$TaskName] = $proc
        Write-DaemonLog "$TaskName started (PID: $($proc.Id))" "SUCCESS"
        
        return $proc
    }
    catch {
        Write-DaemonLog "Failed to start $TaskName : $_" "ERROR"
        return $null
    }
}

function Stop-ManagedTask {
    param([string]$TaskName)
    
    if (!$script:ManagedProcesses.ContainsKey($TaskName)) {
        Write-DaemonLog "$TaskName is not managed" "WARN"
        return
    }
    
    $proc = $script:ManagedProcesses[$TaskName]
    if ($proc -and !$proc.HasExited) {
        Write-DaemonLog "Stopping $TaskName (PID: $($proc.Id))..." "INFO"
        $proc.Kill()
        $proc.WaitForExit(5000)
        Write-DaemonLog "$TaskName stopped" "SUCCESS"
    }
    
    $script:ManagedProcesses.Remove($TaskName)
}

function Watch-ManagedTasks {
    param([object]$Config)
    
    foreach ($taskName in $Config.tasks.PSObject.Properties.Name) {
        $task = $Config.tasks.$taskName
        
        if (!$task.enabled) { continue }
        
        if ($task.type -eq "continuous") {
            # Continuous 작업 - 항상 실행 중이어야 함
            if ($script:ManagedProcesses.ContainsKey($taskName)) {
                $proc = $script:ManagedProcesses[$taskName]
                if ($proc.HasExited) {
                    Write-DaemonLog "$taskName exited unexpectedly. Restarting..." "WARN"
                    Start-ManagedTask -TaskName $taskName -TaskConfig $task -GlobalConfig $Config
                }
            }
            else {
                Start-ManagedTask -TaskName $taskName -TaskConfig $task -GlobalConfig $Config
            }
        }
    }
}

function Start-Daemon {
    param([string]$ConfigPath)
    
    Write-DaemonLog "=== AGI Master Daemon Starting ===" "INFO"
    
    $config = Get-DaemonConfig -Path $ConfigPath
    if (!$config) { return }
    
    # PID 파일 작성
    $pidFile = $config.daemon.pidFile
    $PID | Out-File -FilePath $pidFile -Force
    Write-DaemonLog "PID file created: $pidFile (PID: $PID)" "INFO"
    
    # Continuous 작업 시작
    foreach ($taskName in $config.tasks.Keys) {
        $task = $config.tasks[$taskName]
        if ($task.enabled -and $task.type -eq "continuous") {
            Start-ManagedTask -TaskName $taskName -TaskConfig $task -GlobalConfig $config
        }
    }
    
    Write-DaemonLog "Master Daemon is now running. Press Ctrl+C to stop." "SUCCESS"
    
    # Main loop
    $checkInterval = $config.daemon.checkInterval
    while ($true) {
        Start-Sleep -Seconds $checkInterval
        Watch-ManagedTasks -Config $config
        
        # 창 숨기기 강제 (윈도우 관리)
        if ($config.windowManagement.enforceHidden) {
            Get-Process -Name powershell, pwsh, python, py -EA SilentlyContinue | 
            Where-Object { $_.MainWindowHandle -ne 0 } | 
            ForEach-Object {
                try {
                    $_.Kill()
                    Write-DaemonLog "Killed visible process: $($_.ProcessName) (PID: $($_.Id))" "WARN"
                }
                catch {}
            }
        }
    }
}

function Stop-Daemon {
    Write-DaemonLog "=== Stopping Master Daemon ===" "INFO"
    
    # 모든 관리 프로세스 종료
    foreach ($taskName in $script:ManagedProcesses.Keys) {
        Stop-ManagedTask -TaskName $taskName
    }
    
    # PID 파일 삭제
    $pidFile = "$WorkspaceRoot\outputs\master_daemon.pid"
    if (Test-Path $pidFile) {
        Remove-Item $pidFile -Force
    }
    
    Write-DaemonLog "Master Daemon stopped" "SUCCESS"
}

function Install-DaemonService {
    Write-Host "Installing AGI Master Daemon as Scheduled Task..." -ForegroundColor Yellow
    
    $taskName = "AGI_Master_Daemon"
    $scriptPath = $MyInvocation.MyCommand.Path
    
    # 기존 작업 제거
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -EA SilentlyContinue
    
    # Trigger: 로그온 시 실행
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    
    # Action: 이 스크립트를 -Start로 실행
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`" -Start"
    
    # Settings
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden -ExecutionTimeLimit (New-TimeSpan -Days 365)
    
    # Register
    Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Force | Out-Null
    
    Write-Host "✓ AGI Master Daemon installed" -ForegroundColor Green
    Write-Host "  Run at logon: Yes" -ForegroundColor Cyan
    Write-Host "  Hidden: Yes" -ForegroundColor Cyan
}

function Uninstall-DaemonService {
    Write-Host "Uninstalling AGI Master Daemon..." -ForegroundColor Yellow
    
    Unregister-ScheduledTask -TaskName "AGI_Master_Daemon" -Confirm:$false -EA SilentlyContinue
    
    Write-Host "✓ AGI Master Daemon uninstalled" -ForegroundColor Green
}

function Show-DaemonStatus {
    Write-Host "`n=== AGI Master Daemon Status ===" -ForegroundColor Cyan
    
    # 실제 프로세스 확인 (CIM 사용)
    $daemonProc = Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*master_daemon.ps1*' -and $_.CommandLine -like '*-Start*' } |
    Select-Object -First 1
    
    if ($daemonProc) {
        $proc = Get-Process -Id $daemonProc.ProcessId -ErrorAction SilentlyContinue
        if ($proc) {
            $runtime = (Get-Date) - $proc.StartTime
            Write-Host "✓ Master Daemon is RUNNING" -ForegroundColor Green
            Write-Host "  PID: $($proc.Id)" -ForegroundColor Cyan
            Write-Host "  Runtime: $($runtime.ToString('hh\:mm\:ss'))" -ForegroundColor Cyan
            Write-Host "  CPU: $([math]::Round($proc.CPU, 2))s" -ForegroundColor Cyan
            Write-Host "  Memory: $([math]::Round($proc.WorkingSet64/1MB, 2)) MB" -ForegroundColor Cyan
        }
    }
    else {
        Write-Host "✗ Master Daemon is NOT RUNNING" -ForegroundColor Red
    }
    
    # 관리되는 작업들 상태 확인
    Write-Host "`n=== Managed Tasks ===" -ForegroundColor Cyan
    
    # Observer Telemetry (PowerShell)
    $observerProc = Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*observe_desktop_telemetry*' } |
    Select-Object -First 1
    if ($observerProc) {
        $proc = Get-Process -Id $observerProc.ProcessId -ErrorAction SilentlyContinue
        if ($proc) {
            $runtime = (Get-Date) - $proc.StartTime
            Write-Host "  ✓ Observer Telemetry" -ForegroundColor Green -NoNewline
            Write-Host " (PID: $($proc.Id), Runtime: $($runtime.ToString('hh\:mm\:ss')))" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  ✗ Observer Telemetry" -ForegroundColor Red
    }
    
    # RPA Worker (Python)
    $rpaProc = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*rpa_worker*' } |
    Select-Object -First 1
    if ($rpaProc) {
        $proc = Get-Process -Id $rpaProc.ProcessId -ErrorAction SilentlyContinue
        if ($proc) {
            $runtime = (Get-Date) - $proc.StartTime
            Write-Host "  ✓ RPA Worker" -ForegroundColor Green -NoNewline
            Write-Host " (PID: $($proc.Id), Runtime: $($runtime.ToString('hh\:mm\:ss')))" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  ✗ RPA Worker" -ForegroundColor Red
    }
    
    # Task Watchdog (Python)
    $watchdogProc = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*task_watchdog*' } |
    Select-Object -First 1
    if ($watchdogProc) {
        $proc = Get-Process -Id $watchdogProc.ProcessId -ErrorAction SilentlyContinue
        if ($proc) {
            $runtime = (Get-Date) - $proc.StartTime
            Write-Host "  ✓ Task Watchdog" -ForegroundColor Green -NoNewline
            Write-Host " (PID: $($proc.Id), Runtime: $($runtime.ToString('hh\:mm\:ss')))" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  ✗ Task Watchdog" -ForegroundColor Red
    }
    
    # Task Queue Server (Python)
    $queueProc = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*task_queue_server*' } |
    Select-Object -First 1
    if ($queueProc) {
        $proc = Get-Process -Id $queueProc.ProcessId -ErrorAction SilentlyContinue
        if ($proc) {
            $runtime = (Get-Date) - $proc.StartTime
            Write-Host "  ✓ Task Queue Server" -ForegroundColor Green -NoNewline
            Write-Host " (PID: $($proc.Id), Runtime: $($runtime.ToString('hh\:mm\:ss')))" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  ✗ Task Queue Server" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Main
if ($Install) {
    Install-DaemonService
}
elseif ($Uninstall) {
    Stop-Daemon
    Uninstall-DaemonService
}
elseif ($Start) {
    Start-Daemon -ConfigPath $ConfigPath
}
elseif ($Stop) {
    Stop-Daemon
}
elseif ($Restart) {
    Stop-Daemon
    Start-Sleep -Seconds 2
    Start-Daemon -ConfigPath $ConfigPath
}
elseif ($Status) {
    Show-DaemonStatus
}
else {
    Write-Host "AGI Master Daemon Control" -ForegroundColor Cyan
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  -Install    Install as Windows Scheduled Task"
    Write-Host "  -Uninstall  Remove Scheduled Task"
    Write-Host "  -Start      Start daemon manually"
    Write-Host "  -Stop       Stop daemon"
    Write-Host "  -Restart    Restart daemon"
    Write-Host "  -Status     Show daemon status"
}