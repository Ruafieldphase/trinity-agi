param(
    [string]$Server = 'http://127.0.0.1:8091',
    [int]$IntervalSeconds = 5,
    [string]$LogFile = (Join-Path $( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } ) \"outputs\worker_monitor.log\"),
    [int]$MaxWorkers = 2
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'SilentlyContinue'

function DLog([string]$Msg, [string]$Level = 'INFO') {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $line = "[$ts][$Level] $Msg"
    try { Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8 } catch {}
}

try {
    $repoRoot = $WorkspaceRoot
    $ensureScript = Join-Path $repoRoot 'scripts\ensure_rpa_worker.ps1'
    $startServerScript = Join-Path $repoRoot 'LLM_Unified\ion-mentoring\start_task_queue_server_background.ps1'
    if (-not (Test-Path -LiteralPath $ensureScript)) { DLog "ensure script missing: $ensureScript" 'ERROR'; exit 1 }

    $logDir = Split-Path -Parent $LogFile
    if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

    DLog ("Daemon started. interval=${IntervalSeconds}s, log=$LogFile") 'INFO'
    while ($true) {
        try {
            $running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }
            if (-not $running) {
                DLog 'Worker not running. Attempting start...' 'WARN'
                try { & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureScript -Server $Server -EnforceSingle -MaxWorkers $MaxWorkers | Out-Null; DLog 'Start invoked.' 'INFO' } catch { DLog ("Start failed: $($_.Exception.Message)") 'ERROR' }
            }
            else {
                $pids = $running | Select-Object -ExpandProperty ProcessId
                DLog ("Worker alive: PID(s)=" + ($pids -join ',')) 'DEBUG'
                try {
                    $cnt = @($running).Count
                    if ($cnt -gt [int]$MaxWorkers) {
                        DLog ("Too many workers detected ($cnt). Enforcing MaxWorkers=$MaxWorkers ...") 'WARN'
                        & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureScript -Server $Server -EnforceSingle -MaxWorkers $MaxWorkers | Out-Null
                        DLog 'EnforceSingle invoked.' 'INFO'
                    }
                }
                catch { DLog ("EnforceSingle failed: $($_.Exception.Message)") 'ERROR' }
            }
            try {
                $resp = Invoke-RestMethod -Uri ("$Server/api/health") -TimeoutSec 2
                if ($resp) { DLog 'Server health OK' 'DEBUG' }
            }
            catch {
                DLog 'Server health unreachable' 'DEBUG'
                if (Test-Path -LiteralPath $startServerScript) {
                    try { & powershell -NoProfile -ExecutionPolicy Bypass -File $startServerScript | Out-Null; DLog 'Task queue server start invoked.' 'INFO' } catch { DLog ("Server start failed: $($_.Exception.Message)") 'ERROR' }
                }
            }
        }
        catch { DLog ("Loop error: $($_.Exception.Message)") 'ERROR' }
        Start-Sleep -Seconds $IntervalSeconds
    }
}
catch {
    DLog $_.Exception.Message 'ERROR'
    exit 1
}