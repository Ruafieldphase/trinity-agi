param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$RunNow,
    [int]$IntervalSeconds = 1800,
    [int]$DurationMinutes = 1440,
    [switch]$WithProbe,
    [switch]$RunAsSystem,
    [string]$TaskName = 'ION Monitor Loop',
    [string]$TaskDescription = 'Runs the ION canary monitoring loop every 30 minutes (24h). Auto-start at logon and daily. Configured for maximum reliability.'
)

$ErrorActionPreference = 'Stop'

# Resolve monitor script path
$baseDir = $PSScriptRoot
$loopScript = Join-Path $baseDir 'start_monitor_loop.ps1'
$loopProbeScript = Join-Path $baseDir 'start_monitor_loop_with_probe.ps1'
if ($WithProbe) {
    if (-not (Test-Path $loopProbeScript)) { Write-Error "Missing: $loopProbeScript"; exit 1 }
}
else {
    if (-not (Test-Path $loopScript)) { Write-Error "Missing: $loopScript"; exit 1 }
}

function Get-Task {
    param([string]$Name)
    try { return Get-ScheduledTask -TaskName $Name -ErrorAction Stop } catch { return $null }
}

function Test-IsAdmin {
    try {
        $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    catch { return $false }
}

function Register-MonitorTask {
    param([string]$Name)

    $psExe = 'powershell.exe'
    $scriptToRun = if ($WithProbe) { $loopProbeScript } else { $loopScript }

    # Build arguments for the monitor loop
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $scriptToRun,
        '-IntervalSeconds', "$IntervalSeconds",
        '-DurationMinutes', "$DurationMinutes",
        '-KillExisting')
    if ($WithProbe -and -not ($scriptToRun -eq $loopProbeScript)) { $argList += '-IncludeRateLimitProbe' }

    $action = New-ScheduledTaskAction -Execute $psExe -Argument ($argList -join ' ')

    $isAdmin = Test-IsAdmin
    $preferSystem = if ($PSBoundParameters.ContainsKey('RunAsSystem')) { [bool]$RunAsSystem } else { $true }
    # Triggers: if admin+SYSTEM: any logon; else user-specific to avoid extra privileges requirement
    if ($isAdmin -and $preferSystem) {
        $trigger1 = New-ScheduledTaskTrigger -AtLogOn
    }
    else {
        $trigger1 = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERNAME"
    }
    $trigger2 = New-ScheduledTaskTrigger -Daily -At 00:05

    # Settings for maximum resilience
    function New-SettingsSafe {
        try {
            $params = @{
                MultipleInstances          = 'IgnoreNew'
                AllowStartIfOnBatteries    = $true
                DontStopIfGoingOnBatteries = $true
                StartWhenAvailable         = $true
                WakeToRun                  = $true
                RestartCount               = 5
                RestartInterval            = (New-TimeSpan -Minutes 1)
                ExecutionTimeLimit         = (New-TimeSpan -Hours 24)
                RunOnlyIfNetworkAvailable  = $true
            }
            return New-ScheduledTaskSettingsSet @params
        }
        catch {
            # Retry without network constraint if not supported
            $params2 = @{
                MultipleInstances          = 'IgnoreNew'
                AllowStartIfOnBatteries    = $true
                DontStopIfGoingOnBatteries = $true
                StartWhenAvailable         = $true
                WakeToRun                  = $true
                RestartCount               = 5
                RestartInterval            = (New-TimeSpan -Minutes 1)
                ExecutionTimeLimit         = (New-TimeSpan -Hours 24)
            }
            return New-ScheduledTaskSettingsSet @params2
        }
    }
    $settings = New-SettingsSafe

    # Principal: prefer SYSTEM highest privileges for run-when-not-logged-on; fallback to current user highest
    $principal = $null
    if ($preferSystem -and $isAdmin) {
        try {
            $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
        }
        catch {
            Write-Warning "[scheduler] Failed to create SYSTEM principal: $($_.Exception.Message). Falling back to current user."
        }
    }
    if (-not $principal) {
        $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -RunLevel Limited
    }

    $definition = New-ScheduledTask -Action $action -Trigger @($trigger1, $trigger2) -Settings $settings -Principal $principal -Description $TaskDescription

    $existing = Get-Task -Name $Name
    $registered = $false
    $finalName = $Name
    try {
        if ($existing) {
            Register-ScheduledTask -TaskName $Name -InputObject $definition -Force | Out-Null
            Write-Host "[scheduler] Updated existing task '$Name'" -ForegroundColor Yellow
        }
        else {
            Register-ScheduledTask -TaskName $Name -InputObject $definition | Out-Null
            Write-Host "[scheduler] Registered new task '$Name'" -ForegroundColor Green
        }
        $registered = $true
    }
    catch {
        # If SYSTEM attempt failed and we preferred SYSTEM, fallback to current user (Highest -> Limited)
        $err = $_.Exception.Message
        if ($preferSystem -and $principal.UserId -eq 'SYSTEM') {
            Write-Warning "[scheduler] Registration with SYSTEM failed: $err. Retrying with current user."
            try {
                $principal2 = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -RunLevel Highest
                $definition2 = New-ScheduledTask -Action $action -Trigger @($trigger1, $trigger2) -Settings $settings -Principal $principal2 -Description $TaskDescription
                if ($existing) {
                    Register-ScheduledTask -TaskName $Name -InputObject $definition2 -Force | Out-Null
                    Write-Host "[scheduler] Updated existing task '$Name' (current user)" -ForegroundColor Yellow
                }
                else {
                    Register-ScheduledTask -TaskName $Name -InputObject $definition2 | Out-Null
                    Write-Host "[scheduler] Registered new task '$Name' (current user)" -ForegroundColor Green
                }
                $registered = $true
            }
            catch {
                $err2 = $_.Exception.Message
                Write-Warning "[scheduler] Registration with current user (Highest) failed: $err2. Retrying with Limited privileges."
                try {
                    $principal3 = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -RunLevel Limited
                    $definition3 = New-ScheduledTask -Action $action -Trigger @($trigger1, $trigger2) -Settings $settings -Principal $principal3 -Description $TaskDescription
                    try {
                        Register-ScheduledTask -TaskName $Name -InputObject $definition3 -Force | Out-Null
                        Write-Host "[scheduler] Updated/Registered task '$Name' (current user, Limited)" -ForegroundColor Yellow
                        $registered = $true
                    }
                    catch {
                        # As a last resort, register a new user-scoped task name to avoid permission conflicts
                        $finalName = "$Name (User)"
                        Register-ScheduledTask -TaskName $finalName -InputObject $definition3 | Out-Null
                        Write-Host "[scheduler] Registered new task '$finalName' (current user, Limited)" -ForegroundColor Green
                        $registered = $true
                    }
                }
                catch {
                    throw
                }
            }
        }
        else {
            # As last resort, create per-user tasks via schtasks.exe (no admin). We'll create two triggers as two tasks.
            Write-Warning "[scheduler] Register-ScheduledTask failed: $err. Falling back to 'schtasks' per-user tasks."
            $ps = 'powershell -NoProfile -ExecutionPolicy Bypass -File ' + '"' + $scriptToRun + '"' + " -IntervalSeconds $IntervalSeconds -DurationMinutes $DurationMinutes -KillExisting"
            if ($WithProbe -and ($scriptToRun -eq $loopScript)) { $ps += ' -IncludeRateLimitProbe' }
            $tn1 = "$Name (User OnLogon)"
            $tn2 = "$Name (User Daily)"
            # Create or update OnLogon task
            & schtasks.exe /Create /TN "$tn1" /TR "$ps" /SC ONLOGON /RL LIMITED /F | Out-Null
            # Create or update Daily task at 00:05
            & schtasks.exe /Create /TN "$tn2" /TR "$ps" /SC DAILY /ST 00:05 /RL LIMITED /F | Out-Null
            $registered = $true
            $finalName = $tn1
        }
    }
    if (-not $registered) { throw "[scheduler] Failed to register task '$Name'" }
    return $finalName
}

function Remove-Registered {
    param([string]$Name)
    $existing = Get-Task -Name $Name
    if ($existing) {
        try { Stop-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue } catch {}
        Unregister-ScheduledTask -TaskName $Name -Confirm:$false
        Write-Host "[scheduler] Unregistered task '$Name'" -ForegroundColor Yellow
    }
    else {
        Write-Host "[scheduler] Task '$Name' not found" -ForegroundColor DarkYellow
    }
}

function Start-Registered {
    param([string]$Name)
    $existing = Get-Task -Name $Name
    if (-not $existing) { Write-Error "Task '$Name' not found. Use -Register first."; exit 1 }
    Start-ScheduledTask -TaskName $Name
    Write-Host "[scheduler] Started task '$Name'" -ForegroundColor Green
}

if ($Unregister) {
    Remove-Registered -Name $TaskName
    exit 0
}

if ($Register) {
    $regName = Register-MonitorTask -Name $TaskName
    if ($RunNow) { Start-Registered -Name $regName }
    # Show brief status
    $t = Get-Task -Name $regName
    if ($t) {
        $state = ($t | Select-Object -ExpandProperty State)
        $info = $t | Get-ScheduledTaskInfo
        $last = $info.LastRunTime
        $nxt = $info.NextRunTime
        $res = $info.LastTaskResult
        Write-Host ("[scheduler] Name={0}; State={1}; LastRun={2}; NextRun={3}; LastResult={4}" -f $regName, $state, $last, $nxt, $res) -ForegroundColor Cyan
    }
    exit 0
}

# If no explicit action, print help
Write-Host @"
Usage:
  Register (with probe):
    .\register_monitor_schedule.ps1 -Register -RunNow -WithProbe -IntervalSeconds 1800 -DurationMinutes 1440

  Register (without probe):
    .\register_monitor_schedule.ps1 -Register -RunNow -IntervalSeconds 1800 -DurationMinutes 1440

  Remove:
    .\register_monitor_schedule.ps1 -Unregister

Notes:
  - Task triggers at user logon and daily at 00:05.
  - The monitor script itself runs 24h with 30m intervals by default; -KillExisting prevents duplicates.
  - Check status: Get-ScheduledTask -TaskName '$TaskName' | fl *
"@
exit 0
