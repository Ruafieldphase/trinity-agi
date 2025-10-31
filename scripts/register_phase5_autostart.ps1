param(
    [switch]$Unregister,
    [string]$Server = 'http://127.0.0.1:8091'
)

$ErrorActionPreference = 'Stop'

function New-TaskAction($script, $args) {
    $exec = 'powershell.exe'
    $argLine = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$script`" $args"
    return New-ScheduledTaskAction -Execute $exec -Argument $argLine -WorkingDirectory (Split-Path -Parent $script)
}

$root = Split-Path -Parent $PSScriptRoot
$tasks = @(
    @{ Name = 'AGI_TaskQueue';
       Script = Join-Path $root 'LLM_Unified\ion-mentoring\start_task_queue_server_background.ps1';
       Args = '';
       Description = 'Start Task Queue Server (8091) at logon' },
    @{ Name = 'AGI_WebDashboard';
       Script = Join-Path $root 'fdo_agi_repo\monitoring\web_server.py';
       Args = '';
       Python = $true;
       Description = 'Start Web Dashboard (8000) at logon' },
    @{ Name = 'AGI_MonitoringDaemon';
       Script = Join-Path $root 'fdo_agi_repo\monitoring\monitoring_daemon.py';
       Args = "--server $Server --interval 5";
       Python = $true;
       Description = 'Start Monitoring Daemon at logon' },
    @{ Name = 'AGI_RPAWorkerEnsure';
       Script = Join-Path $root 'scripts\ensure_rpa_worker.ps1';
       Args = "-EnforceSingle -MaxWorkers 1 -Server $Server -Interval 0.5 -LogLevel INFO";
       Description = 'Ensure single RPA worker is running' }
)

if ($Unregister) {
    foreach ($t in $tasks) {
        try { Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false -ErrorAction Stop; Write-Host "Removed task: $($t.Name)" -ForegroundColor Yellow } catch {}
    }
    exit 0
}

# Ensure ScheduledTasks module is available
Import-Module ScheduledTasks | Out-Null

$trigger = New-ScheduledTaskTrigger -AtLogOn

foreach ($t in $tasks) {
    if (-not (Test-Path $t.Script)) {
        Write-Host "[SKIP] Script not found: $($t.Script)" -ForegroundColor DarkYellow
        continue
    }

    if ($t.Python) {
        # Wrap python script into a powershell launcher for consistency
        $launcher = [System.IO.Path]::ChangeExtension($t.Script, '.ps1') + '.launcher'
        $content = "python `"$($t.Script)`" $($t.Args)"
        Set-Content -Path $launcher -Value $content -Encoding UTF8
        $action = New-TaskAction -script $launcher -args ''
    } else {
        $action = New-TaskAction -script $t.Script -args $t.Args
    }

    try {
        # Remove existing
        Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    } catch {}

    $principal = New-ScheduledTaskPrincipal -UserId $env:UserName -RunLevel Highest -LogonType InteractiveToken
    $definition = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal -Description $t.Description
    Register-ScheduledTask -TaskName $t.Name -InputObject $definition -Force | Out-Null
    Write-Host "[OK] Registered task: $($t.Name)" -ForegroundColor Green
}

Write-Host "\nDone. Use -Unregister to remove all tasks." -ForegroundColor Cyan

