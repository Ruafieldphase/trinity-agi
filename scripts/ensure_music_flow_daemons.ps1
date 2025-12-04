#Requires -Version 5.1
<#
.SYNOPSIS
    Ensures Music and Flow Observer daemons are running with auto-restart.

.DESCRIPTION
    - Checks if Music Daemon and Flow Observer are running
    - Starts them if not running or hung (no activity for N seconds)
    - Kills hung processes and restarts fresh
    - Supports -Silent, -JsonOnly, -Force modes
    - Returns structured status for automation

.PARAMETER Silent
    Suppress console output (errors still shown).

.PARAMETER JsonOnly
    Output only JSON status to stdout.

.PARAMETER Force
    Kill existing daemons and restart fresh.

.PARAMETER MaxHungSeconds
    Consider daemon hung if no activity for this long (default: 300).

.PARAMETER RetryCount
    Number of startup retries (default: 2).

.EXAMPLE
    .\ensure_music_flow_daemons.ps1
    .\ensure_music_flow_daemons.ps1 -Silent
    .\ensure_music_flow_daemons.ps1 -JsonOnly
    .\ensure_music_flow_daemons.ps1 -Force
#>

[CmdletBinding()]
param(
    [switch]$Silent,
    [switch]$JsonOnly,
    [switch]$Force,
    [int]$MaxHungSeconds = 300,
    [int]$RetryCount = 2
    , [switch]$EnableAutoGoal
)

$ErrorActionPreference = 'Stop'
$ws = Split-Path -Parent $PSScriptRoot

# Helper: Write output unless silent
function Write-Status {
    param([string]$Message, [string]$Color = 'White')
    if (-not $Silent -and -not $JsonOnly) {
        Write-Host $Message -ForegroundColor $Color
    }
}

# Helper: Get Flow Observer Job
function Get-FlowObserverJob {
    Get-Job -Name 'FlowObserverDaemon' -ErrorAction SilentlyContinue
}

# Helper: Start Flow Observer (PowerShell Job)
function Start-FlowObserver {
    param([int]$Retries, [bool]$Quiet)
    
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            Write-Status "🚀 Starting Flow Observer (attempt $i/$Retries)..." 'Cyan'
            
            $startScript = Join-Path $ws 'scripts\start_flow_observer_daemon.ps1'
            
            if ($Quiet) {
                & $startScript -IntervalSeconds 300 *>&1 | Out-Null
            }
            else {
                & $startScript -IntervalSeconds 300
            }
            
            # Wait 2s and verify job exists
            Start-Sleep -Seconds 2
            $job = Get-FlowObserverJob
            if ($job -and $job.State -eq 'Running') {
                Write-Status "✅ Flow Observer started (Job ID: $($job.Id))" 'Green'
                return @{ success = $true; jobId = $job.Id }
            }
            
            Write-Status "⚠️ Flow Observer job not running" 'Yellow'
        }
        catch {
            Write-Status "❌ Failed to start Flow Observer: $_" 'Red'
        }
        
        if ($i -lt $Retries) {
            Start-Sleep -Seconds 2
        }
    }
    
    return @{ success = $false; error = "Failed after $Retries attempts" }
}

# Helper: Get daemon process
function Get-DaemonProcess {
    param([string]$ScriptPattern)
    Get-Process -Name 'python' -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*$ScriptPattern*" } |
    Select-Object -First 1
}

# Helper: Check if daemon is hung (no CPU activity)
function Test-DaemonHung {
    param($Process, [int]$MaxSeconds)
    if (-not $Process) { return $false }
    
    $startCpu = $Process.CPU
    Start-Sleep -Seconds 2
    $Process.Refresh()
    $endCpu = $Process.CPU
    
    $cpuDelta = $endCpu - $startCpu
    return ($cpuDelta -lt 0.01)  # Less than 0.01s of CPU in 2s = hung
}

# Helper: Start daemon
function Start-Daemon {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [int]$Retries,
        [string]$StartArgs = ''
    )
    
    for ($i = 1; $i -le $Retries; $i++) {
        try {
            Write-Status "🚀 Starting $Name (attempt $i/$Retries)..." 'Cyan'
            
            $pythonExe = Join-Path $ws 'fdo_agi_repo\.venv\Scripts\python.exe'
            if (-not (Test-Path -LiteralPath $pythonExe)) {
                $pythonExe = 'python'
            }
            
            $startInfo = New-Object System.Diagnostics.ProcessStartInfo
            $startInfo.FileName = $pythonExe
            $startInfo.Arguments = "`"$ScriptPath`" $StartArgs"
            $startInfo.UseShellExecute = $false
            $startInfo.CreateNoWindow = $true
            $startInfo.RedirectStandardOutput = $true
            $startInfo.RedirectStandardError = $true
            $startInfo.WorkingDirectory = $ws
            
            $process = [System.Diagnostics.Process]::Start($startInfo)
            
            # Wait 3s and verify it's still running
            Start-Sleep -Seconds 3
            if (-not $process.HasExited) {
                Write-Status "✅ $Name started (PID: $($process.Id))" 'Green'
                return @{ success = $true; pid = $process.Id }
            }
            
            Write-Status "⚠️ $Name exited immediately" 'Yellow'
        }
        catch {
            Write-Status "❌ Failed to start $Name`: $_" 'Red'
        }
        
        if ($i -lt $Retries) {
            Start-Sleep -Seconds 2
        }
    }
    
    return @{ success = $false; error = "Failed after $Retries attempts" }
}

# Main execution
try {
    $status = @{
        timestamp = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')
        music     = @{ running = $false; pid = $null; action = 'none' }
        flow      = @{ running = $false; pid = $null; action = 'none' }
        errors    = @()
    }
    
    # === Music Daemon ===
    Write-Status "`n🎵 Checking Music Daemon..." 'Cyan'
    $musicProc = Get-DaemonProcess 'music_daemon.py'
    $musicScript = Join-Path $ws 'scripts\music_daemon.py'
    
    if ($Force -and $musicProc) {
        Write-Status "🔄 Force restart requested - killing existing Music Daemon" 'Yellow'
        Stop-Process -Id $musicProc.Id -Force
        $musicProc = $null
        Start-Sleep -Seconds 2
    }
    
    if ($musicProc) {
        $isHung = Test-DaemonHung -Process $musicProc -MaxSeconds $MaxHungSeconds
        if ($isHung) {
            Write-Status "⚠️ Music Daemon appears hung - restarting" 'Yellow'
            Stop-Process -Id $musicProc.Id -Force
            Start-Sleep -Seconds 2
            $startArgs = if ($EnableAutoGoal) { '--auto-goal' } else { '' }
            $result = Start-Daemon -Name 'Music Daemon' -ScriptPath $musicScript -Retries $RetryCount -StartArgs $startArgs
            $status.music.action = 'restarted_hung'
            $status.music.running = $result.success
            $status.music.pid = $result.pid
            if (-not $result.success) {
                $status.errors += $result.error
            }
        }
        else {
            Write-Status "✅ Music Daemon is running (PID: $($musicProc.Id))" 'Green'
            $status.music.running = $true
            $status.music.pid = $musicProc.Id
            $status.music.action = 'already_running'
        }
    }
    else {
        Write-Status "❌ Music Daemon not running - starting" 'Yellow'
        $startArgs = if ($EnableAutoGoal) { '--auto-goal' } else { '' }
        $result = Start-Daemon -Name 'Music Daemon' -ScriptPath $musicScript -Retries $RetryCount -StartArgs $startArgs
        $status.music.action = 'started'
        $status.music.running = $result.success
        $status.music.pid = $result.pid
        if (-not $result.success) {
            $status.errors += $result.error
        }
    }

    # === Music->Goal PoC listener ===
    $musicToGoalScript = Join-Path $ws 'scripts\music_to_goal.py'
    if (Test-Path $musicToGoalScript) {
        $mtgProc = Get-DaemonProcess 'music_to_goal.py'
        if (-not $mtgProc) {
            Write-Status "🔁 Music->Goal PoC not running - starting" 'Cyan'
            $result = Start-Daemon -Name 'Music->Goal' -ScriptPath $musicToGoalScript -Retries 1
            $status.music_to_goal = @{ running = $result.success; pid = $result.pid }
        }
        else {
            Write-Status "✅ Music->Goal PoC is running (PID: $($mtgProc.Id))" 'Green'
            $status.music_to_goal = @{ running = $true; pid = $mtgProc.Id }
        }
    }
    
    # === Flow Observer ===
    Write-Status "`n🌊 Checking Flow Observer..." 'Cyan'
    $flowJob = Get-FlowObserverJob
    
    if ($Force -and $flowJob) {
        Write-Status "🔄 Force restart requested - stopping existing Flow Observer" 'Yellow'
        Stop-Job -Id $flowJob.Id
        Remove-Job -Id $flowJob.Id -Force
        $flowJob = $null
        Start-Sleep -Seconds 2
    }
    
    if ($flowJob) {
        if ($flowJob.State -eq 'Running') {
            Write-Status "✅ Flow Observer is running (Job ID: $($flowJob.Id))" 'Green'
            $status.flow.running = $true
            $status.flow.pid = $flowJob.Id
            $status.flow.action = 'already_running'
        }
        else {
            Write-Status "⚠️ Flow Observer job exists but not running - restarting" 'Yellow'
            Remove-Job -Id $flowJob.Id -Force
            Start-Sleep -Seconds 2
            $result = Start-FlowObserver -Retries $RetryCount -Quiet $Silent
            $status.flow.action = 'restarted_stopped'
            $status.flow.running = $result.success
            $status.flow.pid = $result.jobId
            if (-not $result.success) {
                $status.errors += $result.error
            }
        }
    }
    else {
        Write-Status "❌ Flow Observer not running - starting" 'Yellow'
        $result = Start-FlowObserver -Retries $RetryCount -Quiet $Silent
        $status.flow.action = 'started'
        $status.flow.running = $result.success
        $status.flow.pid = $result.jobId
        if (-not $result.success) {
            $status.errors += $result.error
        }
    }
    
    # === Summary ===
    if ($JsonOnly) {
        $status | ConvertTo-Json -Depth 5 -Compress
    }
    else {
        Write-Status "`n📊 Summary:" 'Cyan'
        Write-Status "   Music Daemon: $(if($status.music.running){'✅ Running'}else{'❌ Failed'}) (PID: $($status.music.pid))" $(if ($status.music.running) { 'Green' }else { 'Red' })
        Write-Status "   Flow Observer: $(if($status.flow.running){'✅ Running'}else{'❌ Failed'}) (Job ID: $($status.flow.pid))" $(if ($status.flow.running) { 'Green' }else { 'Red' })
        
        if ($status.errors.Count -gt 0) {
            Write-Status "`n⚠️ Errors encountered:" 'Yellow'
            $status.errors | ForEach-Object { Write-Status "   - $_" 'Red' }
        }
    }
    
    # Exit code: 0 if both running, 1 if any failed
    $exitCode = if ($status.music.running -and $status.flow.running) { 0 } else { 1 }
    exit $exitCode
}
catch {
    if ($JsonOnly) {
        @{
            timestamp = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')
            music     = @{ running = $false; pid = $null; action = 'error' }
            flow      = @{ running = $false; pid = $null; action = 'error' }
            errors    = @("Script error: $_")
        } | ConvertTo-Json -Depth 5 -Compress
    }
    else {
        Write-Host "❌ Script error: $_" -ForegroundColor Red
    }
    exit 1
}
