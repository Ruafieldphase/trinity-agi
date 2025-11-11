param(
    [switch]$Register,
    [switch]$Unregister,
    [switch]$Status,
    [int]$DelayMinutes = 5,
    [string]$WorkspaceFolder = "${PSScriptRoot}\.."
)

$ErrorActionPreference = 'Stop'

$taskPath = '\AGI\'
$taskName = 'VSCode_AutoLaunch_AfterLogon'
$taskFullName = "$taskPath$taskName"

function Get-LauncherPath {
    $launcher = Join-Path $PSScriptRoot 'launch_vscode_after_logon.ps1'
    if (-not (Test-Path -LiteralPath $launcher)) {
        throw "Launcher script not found: $launcher"
    }
    return (Resolve-Path -LiteralPath $launcher).Path
}

function Register-WithSchTasks([string]$ws, [int]$delayMinutes) {
    $sleepSeconds = [int]([double]$delayMinutes * 60)
    $launcher = Get-LauncherPath
    $cmd = "Start-Sleep -Seconds $sleepSeconds; & '" + $launcher + "' -Workspace '" + $ws + "'"
    $tr = "powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command `"$cmd`""
    $trArg = '"' + $tr.Replace('"', '\"') + '"'
    $delaySpec = ('{0:D4}:{1:D2}' -f ($delayMinutes * 1), 0)
    $args = @('/Create', '/F', '/TN', "$taskName", '/SC', 'ONLOGON', '/DELAY', $delaySpec, '/RL', 'LIMITED', '/TR', $trArg)
    $proc = Start-Process -FilePath schtasks.exe -ArgumentList $args -NoNewWindow -PassThru -Wait
    if ($proc.ExitCode -ne 0) { throw "schtasks.exe failed with exit code $($proc.ExitCode)" }
}

function Create-StartupShortcut([string]$ws, [int]$delayMinutes) {
    $startup = [Environment]::GetFolderPath('Startup')
    if (-not $startup) { $startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup' }
    if (-not (Test-Path -LiteralPath $startup)) { throw "Startup folder not found: $startup" }

    $shortcutPath = Join-Path $startup 'VSCode_AutoLaunch_AfterLogon.lnk'
    $delayed = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'delayed_launch_vscode.ps1')).Path
    $launcherIcon = (Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code\Code.exe')
    if (-not (Test-Path -LiteralPath $launcherIcon)) { $launcherIcon = $null }

    $wsh = New-Object -ComObject WScript.Shell
    $sc = $wsh.CreateShortcut($shortcutPath)
    $sc.TargetPath = 'powershell.exe'
    $sc.Arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$delayed`" -DelayMinutes $delayMinutes -Workspace `"$ws`""
    $sc.WorkingDirectory = $ws
    if ($launcherIcon) { $sc.IconLocation = $launcherIcon }
    $sc.WindowStyle = 7 # Minimized
    $sc.Save()

    Write-Host "Created Startup shortcut: $shortcutPath (Delay: $delayMinutes min)" -ForegroundColor Green
}

if ($Register) {
    $trigger = New-ScheduledTaskTrigger -AtLogOn

    $launcher = Get-LauncherPath

    # Ensure workspace path is resolved for the task arguments
    try { $ws = Resolve-Path -LiteralPath $WorkspaceFolder | Select-Object -ExpandProperty Path } catch { $ws = $WorkspaceFolder }

    $sleepSeconds = [int]([double]$DelayMinutes * 60)
    $cmd = "Start-Sleep -Seconds $sleepSeconds; & '" + $launcher + "' -Workspace '" + $ws + "'"
    $argString = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command `"$cmd`""
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argString -WorkingDirectory $ws

    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

    $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Description "Open VS Code on this workspace $DelayMinutes minutes after logon"

    try {
        Register-ScheduledTask -TaskName $taskName -TaskPath $taskPath -InputObject $task -Force | Out-Null
        Write-Host "Registered scheduled task: $taskFullName (Delay: $DelayMinutes min)" -ForegroundColor Green
    }
    catch {
        try {
            Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null
            Write-Host "Registered scheduled task in root: $taskName (Delay: $DelayMinutes min)" -ForegroundColor Green
        }
        catch {
            Write-Host "Register-ScheduledTask failed. Falling back to schtasks.exe..." -ForegroundColor Yellow
            try {
                Register-WithSchTasks -ws $ws -delayMinutes $DelayMinutes
                Write-Host "Registered via schtasks: $taskName (Delay: $DelayMinutes min)" -ForegroundColor Green
            }
            catch {
                Write-Host "schtasks.exe failed. Falling back to Startup shortcut method..." -ForegroundColor Yellow
                try {
                    Create-StartupShortcut -ws $ws -delayMinutes $DelayMinutes
                }
                catch {
                    Write-Error "Failed to register autostart via all methods: $($_.Exception.Message)"
                    exit 1
                }
            }
        }
    }
    exit 0
}

if ($Unregister) {
    try {
        $ok = $false
        try {
            Unregister-ScheduledTask -TaskName $taskName -TaskPath $taskPath -Confirm:$false -ErrorAction Stop
            $ok = $true
        }
        catch {}
        if (-not $ok) {
            try {
                Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
                $ok = $true
            }
            catch {}
        }
        if (-not $ok) {
            # Fallback to schtasks
            $proc = Start-Process schtasks.exe -ArgumentList @('/Delete', '/TN', "$taskName", '/F') -NoNewWindow -PassThru -Wait
            if ($proc.ExitCode -ne 0) { throw "schtasks /Delete failed with exit code $($proc.ExitCode)" }
        }
        # Remove Startup shortcut if present
        $startup = [Environment]::GetFolderPath('Startup')
        if (-not $startup) { $startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup' }
        $shortcutPath = Join-Path $startup 'VSCode_AutoLaunch_AfterLogon.lnk'
        if (Test-Path -LiteralPath $shortcutPath) {
            Remove-Item -LiteralPath $shortcutPath -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Unregistered scheduled task: $taskName" -ForegroundColor Yellow
    }
    catch {
        Write-Error "Failed to unregister scheduled task: $($_.Exception.Message)"
        exit 1
    }
    exit 0
}

if ($Status) {
    try {
        $printed = $false
        try {
            $task = Get-ScheduledTask -TaskName $taskName -TaskPath $taskPath -ErrorAction Stop
            $task | Select-Object TaskName, TaskPath, State, @{n = 'Triggers'; e = { $_.Triggers } }, @{n = 'Actions'; e = { $_.Actions } } | Format-List | Out-String | Write-Output
            $printed = $true
        }
        catch {}
        if (-not $printed) {
            try {
                $task = Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
                $task | Select-Object TaskName, TaskPath, State, @{n = 'Triggers'; e = { $_.Triggers } }, @{n = 'Actions'; e = { $_.Actions } } | Format-List | Out-String | Write-Output
                $printed = $true
            }
            catch {}
        }
        if (-not $printed) {
            # Fallback: schtasks query
            Start-Process schtasks.exe -ArgumentList @('/Query', '/TN', "$taskName") -NoNewWindow -Wait
            $printed = $true
        }
        # Also report Startup shortcut presence
        $startup = [Environment]::GetFolderPath('Startup')
        if (-not $startup) { $startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup' }
        $shortcutPath = Join-Path $startup 'VSCode_AutoLaunch_AfterLogon.lnk'
        if (Test-Path -LiteralPath $shortcutPath) {
            Write-Host "Startup shortcut present: $shortcutPath" -ForegroundColor Green
        }
        else {
            Write-Host "Startup shortcut not found" -ForegroundColor Yellow
        }
        if ($printed) { exit 0 } else { throw 'Status retrieval failed' }
    }
    catch {
        Write-Host "Task not found: $taskFullName" -ForegroundColor Red
        exit 1
    }
}

Write-Host 'Specify one of: -Register, -Unregister, -Status' -ForegroundColor Yellow
exit 2
