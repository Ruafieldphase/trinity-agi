param([switch]$Register, [switch]$Unregister, [switch]$Status)

$ErrorActionPreference = 'Stop'
$TaskName = 'AGI_AI_Ops_Manager'
$WorkspaceRoot = 'C:\workspace\agi'
$ScriptPath = Join-Path $WorkspaceRoot 'scripts\ai_ops_manager.ps1'
$StartupDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$StartupLink = Join-Path $StartupDir 'AGI_AIOpsManager.lnk'

if ($Status) {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($t) {
        Write-Host 'Registered (Scheduled Task):' $t.TaskName 'State=' $t.State
        Write-Host 'Script:' $ScriptPath
        exit 0
    }
    if (Test-Path $StartupLink) {
        Write-Host 'Registered (Startup Shortcut):' $StartupLink
        Write-Host 'Script:' $ScriptPath
        exit 0
    }
    Write-Host 'Not registered'
    exit 1
}

if ($Unregister) {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($t) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
    if (Test-Path $StartupLink) { Remove-Item $StartupLink -Force -ErrorAction SilentlyContinue }
    Write-Host 'Unregistered'
    exit 0
}

if ($Register) {
    try {
        $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existing) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
        $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`" -IntervalSeconds 60 -AutoRecover"
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Days 2)
        $principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'AGI Autonomous Ops Manager' | Out-Null
        Write-Host 'Registered (Scheduled Task)'
    }
    catch {
        Write-Host 'Scheduled Task registration failed. Falling back to Startup shortcut...' -ForegroundColor Yellow
        if (-not (Test-Path $StartupDir)) { New-Item -ItemType Directory -Path $StartupDir -Force | Out-Null }
        $lnk = $StartupLink
        $shell = New-Object -ComObject WScript.Shell
        $sc = $shell.CreateShortcut($lnk)
        $sc.TargetPath = 'powershell.exe'
        $sc.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`" -IntervalSeconds 60 -AutoRecover"
        $sc.WorkingDirectory = $WorkspaceRoot
        $sc.Save()
        Write-Host 'Registered (Startup Shortcut)'
    }
    exit 0
}

Write-Host 'Usage:'
Write-Host '  -Register     Register AI Ops Manager at logon'
Write-Host '  -Unregister   Remove AI Ops Manager registration'
Write-Host '  -Status       Show registration status'
