param([switch]$Register, [switch]$Unregister, [switch]$Status)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = 'Stop'
$TaskName = 'AGI_Phase25_AutoResume'
$ScriptPath = Join-Path $WorkspaceRoot 'scripts\auto_resume_on_startup.ps1'
$StartupDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$StartupLink = Join-Path $StartupDir 'AGI_AutoResume.lnk'

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
    $registered = $false
    try {
        $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existing) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
        $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`" -Silent"
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
        $principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'AGI Auto Resume' | Out-Null
        $registered = $true
        Write-Host 'Registered (Scheduled Task)'
    }
    catch {
        Write-Host 'Scheduled Task registration failed. Falling back to Startup shortcut...' -ForegroundColor Yellow
        if (-not (Test-Path $StartupDir)) { New-Item -ItemType Directory -Path $StartupDir -Force | Out-Null }
        $lnk = $StartupLink
        $shell = New-Object -ComObject WScript.Shell
        $sc = $shell.CreateShortcut($lnk)
        $sc.TargetPath = 'powershell.exe'
        $sc.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`" -Silent"
        $sc.WorkingDirectory = $WorkspaceRoot
        $sc.Save()
        Write-Host 'Registered (Startup Shortcut)'
    }
    exit 0
}

Write-Host 'Usage:'
Write-Host '  -Register     Register scheduled task at logon'
Write-Host '  -Unregister   Remove scheduled task'
Write-Host '  -Status       Show status'