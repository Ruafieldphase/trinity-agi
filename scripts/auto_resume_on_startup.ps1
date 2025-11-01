<#
Auto resume script (ASCII-safe, PS 5.1 compatible)
Behavior:
 - Debounce: skip if run within the last 5 minutes
 - Ensure Task Queue Server on port 8091
 - Ensure AI Agent Scheduler (30m interval, 24h, AutoRecover)
#>

param([switch]$Silent)

# Be defensive: catch-all to ensure we never return non-zero unintentionally
try {
    $ErrorActionPreference = 'Continue'
    $WorkspaceRoot = Split-Path -Parent $PSScriptRoot

    # Debounce recent runs
    $StateDir = Join-Path $WorkspaceRoot 'outputs'
    if (-not (Test-Path $StateDir)) { New-Item -ItemType Directory -Path $StateDir -Force | Out-Null }
    $StateFile = Join-Path $StateDir 'auto_resume_state.json'
    $now = Get-Date
    if (Test-Path $StateFile) {
        try {
            $st = Get-Content $StateFile -Raw | ConvertFrom-Json
            $last = [DateTime]::Parse($st.last_run)
            if (($now - $last).TotalMinutes -lt 5) { if (-not $Silent) { Write-Host 'Skip: ran recently' -ForegroundColor Yellow }; return }
        }
        catch { }
    }
    @{ last_run = $now.ToString('o') } | ConvertTo-Json | Set-Content $StateFile

    # Ensure Task Queue Server
    try {
        Invoke-WebRequest -Uri 'http://localhost:8091/api/health' -TimeoutSec 2 -ErrorAction Stop | Out-Null
    }
    catch {
        $serverScript = Join-Path $WorkspaceRoot 'LLM_Unified\ion-mentoring\task_queue_server.py'
        $pythonExe = Join-Path $WorkspaceRoot 'LLM_Unified\.venv\Scripts\python.exe'
        if ((Test-Path $serverScript) -and (Test-Path $pythonExe)) {
            Start-Job -ScriptBlock { param($py, $sc) & $py $sc } -ArgumentList $pythonExe, $serverScript | Out-Null
            if (-not $Silent) { Write-Host 'Started Task Queue Server (bg job)' -ForegroundColor Green }
        }
    }

    # Ensure AI Agent Scheduler
    try {
        $PidFile = Join-Path $StateDir 'ai_agent_monitor.pid'
        $needStart = $true
        if (Test-Path $PidFile) {
            $txt = Get-Content $PidFile -Raw
            if ($txt -match 'PID=(\d+)') {
                $pid = [int]$Matches[1]
                if (Get-Process -Id $pid -ErrorAction SilentlyContinue) { $needStart = $false }
            }
        }
        if ($needStart) {
            & (Join-Path $WorkspaceRoot 'scripts\ai_agent_scheduler.ps1') -IntervalMinutes 30 -DurationMinutes 1440 -AutoRecover | Out-Null
        }
    }
    catch {
        if (-not $Silent) { Write-Host ('Scheduler ensure error: ' + $_.Exception.Message) -ForegroundColor Yellow }
    }
}
catch {
    if (-not $Silent) { Write-Host ('Auto-resume error: ' + $_.Exception.Message) -ForegroundColor Yellow }
}
finally {
    try { [Environment]::Exit(0) } catch { exit 0 }
}
