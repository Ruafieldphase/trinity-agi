param(
    [string]$Server = 'http://127.0.0.1:8091',
    [int]$IntervalSeconds = 5,
    [switch]$KillExisting,
    [string]$LogFile = (Join-Path $( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } ) \"outputs\worker_monitor.log\"),
    [int]$MaxWorkers = 2
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

function Write-Log([string]$Msg, [string]$Level = 'INFO') {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $line = "[$ts][$Level] $Msg"
    Write-Host $line
    try { Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8 } catch {}
}

try {
    if ($KillExisting) {
        $jobs = Get-Job -Name 'RPA_Worker_Monitor' -ErrorAction SilentlyContinue
        if ($jobs) {
            Write-Log "Stopping existing monitor jobs: $($jobs.Count)" 'WARN'
            $jobs | ForEach-Object { try { Stop-Job -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {}; try { Remove-Job -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {} }
        }
    }

    $repoRoot = $WorkspaceRoot
    $ensureScript = Join-Path $repoRoot 'scripts\ensure_rpa_worker.ps1'
    $startServerScript = Join-Path $repoRoot 'LLM_Unified\ion-mentoring\start_task_queue_server_background.ps1'
    if (-not (Test-Path -LiteralPath $ensureScript)) { throw "ensure script not found: $ensureScript" }

    $logDir = Split-Path -Parent $LogFile
    if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

    $argsForJob = @($Server, [string]$IntervalSeconds, $ensureScript, $LogFile, [int]$MaxWorkers, $startServerScript)

    Start-Job -Name 'RPA_Worker_Monitor' -ScriptBlock {
        param($ServerArg, $IntervalArg, $EnsureScriptArg, $LogFileArg, $MaxWorkersArg, $StartServerScriptArg)
        $ErrorActionPreference = 'SilentlyContinue'
        function JWrite([string]$m, [string]$lvl = 'INFO') {
            $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
            $line = "[$ts][$lvl] $m"
            try { Add-Content -LiteralPath $LogFileArg -Value $line -Encoding UTF8 } catch {}
        }
        while ($true) {
            try {
                $running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*rpa_worker.py*' }
                if (-not $running) {
                    JWrite 'Worker not running. Attempting start...' 'WARN'
                    try { & powershell -NoProfile -ExecutionPolicy Bypass -File $EnsureScriptArg -Server $ServerArg -EnforceSingle -MaxWorkers $MaxWorkersArg | Out-Null; JWrite 'Start invoked.' 'INFO' } catch { JWrite ("Start failed: $($_.Exception.Message)") 'ERROR' }
                }
                else {
                    $pids = $running | Select-Object -ExpandProperty ProcessId
                    JWrite ("Worker alive: PID(s)=" + ($pids -join ',')) 'DEBUG'
                    try {
                        $cnt = @($running).Count
                        if ($cnt -gt [int]$MaxWorkersArg) {
                            JWrite ("Too many workers detected ($cnt). Enforcing MaxWorkers=$MaxWorkersArg ...") 'WARN'
                            & powershell -NoProfile -ExecutionPolicy Bypass -File $EnsureScriptArg -Server $ServerArg -EnforceSingle -MaxWorkers $MaxWorkersArg | Out-Null
                            JWrite 'EnforceSingle invoked.' 'INFO'
                        }
                    }
                    catch { JWrite ("EnforceSingle failed: $($_.Exception.Message)") 'ERROR' }
                }
                # Optional: server health ping
                try {
                    $resp = Invoke-RestMethod -Uri ("$ServerArg/api/health") -TimeoutSec 2
                    if ($resp) { JWrite 'Server health OK' 'DEBUG' }
                }
                catch {
                    JWrite 'Server health unreachable' 'DEBUG'
                    if (Test-Path -LiteralPath $StartServerScriptArg) {
                        try { & powershell -NoProfile -ExecutionPolicy Bypass -File $StartServerScriptArg | Out-Null; JWrite 'Task queue server start invoked.' 'INFO' } catch { JWrite ("Server start failed: $($_.Exception.Message)") 'ERROR' }
                    }
                }
            }
            catch { JWrite ("Loop error: $($_.Exception.Message)") 'ERROR' }
            Start-Sleep -Seconds ([int]$IntervalArg)
        }
    } -ArgumentList $argsForJob | Out-Null

    Write-Log "Worker monitor started (Job: RPA_Worker_Monitor), interval=${IntervalSeconds}s, log=$LogFile, MaxWorkers=$MaxWorkers" 'INFO'
    exit 0
}
catch {
    Write-Log $_.Exception.Message 'ERROR'
    exit 1
}