param(
    [string]$Server = 'http://127.0.0.1:8091',
    [int]$IntervalSeconds = 5,
    [string]$LogFile = (Join-Path (Join-Path $PSScriptRoot '..') 'outputs\worker_monitor.log'),
    [int]$MaxWorkers = 2
)

$ErrorActionPreference = 'SilentlyContinue'

function MLog([string]$Msg, [string]$Level = 'INFO') {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $line = "[$ts][$Level] $Msg"
    Write-Host $line
    try { Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8 } catch {}
}

$repoRoot = Join-Path $PSScriptRoot '..'
$ensureWorkerScript = Join-Path $repoRoot 'scripts\ensure_rpa_worker.ps1'
if (-not (Test-Path -LiteralPath $ensureWorkerScript)) { MLog "ensure script missing: $ensureWorkerScript" 'ERROR'; exit 1 }

# Task Queue Server starter (optional but recommended)
$ensureServerScript = Join-Path $repoRoot 'LLM_Unified\ion-mentoring\start_task_queue_server_background.ps1'
if (-not (Test-Path -LiteralPath $ensureServerScript)) { MLog "server starter missing: $ensureServerScript" 'ERROR' }

$logDir = Split-Path -Parent $LogFile
if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

MLog ("Foreground monitor started. interval=${IntervalSeconds}s, log=$LogFile") 'INFO'
while ($true) {
    try {
        # 1) Ensure Task Queue Server health
        $serverHealthy = $false
        try {
            $resp = Invoke-RestMethod -Uri ("$Server/api/health") -TimeoutSec 2
            if ($resp) { $serverHealthy = $true }
        }
        catch { $serverHealthy = $false }

        if (-not $serverHealthy) {
            # check if server process exists
            $serverProc = $null
            try {
                $serverProc = Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*.exe' -and $_.CommandLine -like '*task_queue_server.py*' } | Select-Object -First 1
            }
            catch {}
            if ($serverProc) {
                MLog ("Server unhealthy (PID=$($serverProc.ProcessId) present). Waiting/retry...") 'WARN'
            }
            elseif (Test-Path -LiteralPath $ensureServerScript) {
                MLog 'Server not healthy. Attempting to start task queue server...' 'WARN'
                try { & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureServerScript | Out-Null; MLog 'Task queue server start invoked.' 'INFO' } catch { MLog ("Server start failed: $($_.Exception.Message)") 'ERROR' }
                Start-Sleep -Seconds 2
                try { $resp2 = Invoke-RestMethod -Uri ("$Server/api/health") -TimeoutSec 3; if ($resp2) { $serverHealthy = $true } } catch { $serverHealthy = $false }
            }
            else {
                MLog 'Server not healthy and starter script missing.' 'ERROR'
            }
        }

        if ($serverHealthy) { MLog 'Server health OK' 'DEBUG' } else { MLog 'Server health still failing' 'WARN' }

        # 2) Ensure RPA Worker
        $running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }
        if (-not $running) {
            MLog 'Worker not running. Attempting start...' 'WARN'
            try { & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureWorkerScript -Server $Server -EnforceSingle -MaxWorkers $MaxWorkers | Out-Null; MLog 'Start invoked.' 'INFO' } catch { MLog ("Start failed: $($_.Exception.Message)") 'ERROR' }
        }
        else {
            $pids = $running | Select-Object -ExpandProperty ProcessId
            MLog ("Worker alive: PID(s)=" + ($pids -join ',')) 'DEBUG'
            # Enforce max workers if more than allowed
            try {
                $count = @($running).Count
                if ($count -gt $MaxWorkers) {
                    MLog ("Too many workers detected ($count). Enforcing MaxWorkers=$MaxWorkers ...") 'WARN'
                    & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureWorkerScript -Server $Server -EnforceSingle -MaxWorkers $MaxWorkers | Out-Null
                    MLog 'EnforceSingle invoked.' 'INFO'
                }
            }
            catch { MLog ("EnforceSingle failed: $($_.Exception.Message)") 'ERROR' }
        }
    }
    catch { MLog ("Loop error: $($_.Exception.Message)") 'ERROR' }
    Start-Sleep -Seconds $IntervalSeconds
}
