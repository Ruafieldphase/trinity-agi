param(
    [int]$IntervalSeconds = 60,
    [int]$DurationMinutes = 0,
    [switch]$AutoRecover,
    [switch]$Once
)

# ASCII-safe, PS 5.1 compatible, fail-safe: never return non-zero
try {
    $ErrorActionPreference = 'Continue'
    $WorkspaceRoot = Split-Path -Parent $PSScriptRoot
    $OutDir = Join-Path $WorkspaceRoot 'outputs'
    if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

    $StatusFile = Join-Path $OutDir 'ai_ops_manager_status.json'
    $PidFile = Join-Path $OutDir 'ai_ops_manager.pid'

    # Write PID for visibility
    try { "PID=$PID" | Set-Content -Path $PidFile -Encoding ASCII } catch { }

    function Get-NowIso {
        return (Get-Date).ToString('o')
    }

    function Test-QueueServerHealthy {
        try {
            $response = Invoke-WebRequest -Uri 'http://localhost:8091/api/health' -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            return ($response.StatusCode -eq 200)
        }
        catch { 
            Start-Sleep -Milliseconds 500
            try {
                $response = Invoke-WebRequest -Uri 'http://localhost:8091/api/health' -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
                return ($response.StatusCode -eq 200)
            }
            catch { return $false }
        }
    }

    function Test-SchedulerAlive {
        try {
            $script = Join-Path $WorkspaceRoot 'scripts\\check_scheduler_status.ps1'
            $args = "-NoProfile -ExecutionPolicy Bypass -File `"$script`""
            $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
            if ($p.ExitCode -eq 0) { return $true } else { return $false }
        }
        catch { return $false }
    }

    function Ensure-Healthy {
        param([ref]$actions)
        $tookAction = $false
        $stabilized = $false
        $retries = 0

        $schedulerOk = Test-SchedulerAlive
        $queueOk = Test-QueueServerHealthy

        if (-not $schedulerOk -or -not $queueOk) {
            if ($AutoRecover) {
                $autoResume = Join-Path $WorkspaceRoot 'scripts\auto_resume_on_startup.ps1'
                try {
                    $args = "-NoProfile -ExecutionPolicy Bypass -File `"$autoResume`" -Silent"
                    Start-Process -FilePath 'powershell.exe' -ArgumentList $args -Wait -WindowStyle Hidden | Out-Null
                    $tookAction = $true
                    $actions.Value += @{ type = 'auto_resume'; ts = (Get-NowIso); reason = @{ scheduler = $schedulerOk; queue = $queueOk } }
                }
                catch { }

                for ($i = 0; $i -lt 20; $i++) {
                    Start-Sleep -Milliseconds 1000
                    $retries++
                    if (Test-SchedulerAlive -and Test-QueueServerHealthy) { $stabilized = $true; break }
                }
                $actions.Value += @{ type = 'post_recover_check'; ts = (Get-NowIso); stabilized = $stabilized; retries = $retries }
            }
        }

        # Re-evaluate after possible repair
        $schedulerOk2 = Test-SchedulerAlive
        $queueOk2 = Test-QueueServerHealthy

        return [pscustomobject]@{
            schedulerHealthy = $schedulerOk2
            queueHealthy     = $queueOk2
            actionTaken      = $tookAction
            stabilized       = $stabilized
            retries          = $retries
        }
    }

    $start = Get-Date
    $loops = 0

    do {
        $loops++
        $actions = @()
        $result = Ensure-Healthy -actions ([ref]$actions)

        $status = [ordered]@{
            ts               = (Get-NowIso)
            pid              = $PID
            schedulerHealthy = $result.schedulerHealthy
            queueHealthy     = $result.queueHealthy
            actionTaken      = $result.actionTaken
            stabilized       = $result.stabilized
            retries          = $result.retries
            actions          = $actions
            loops            = $loops
            intervalSeconds  = $IntervalSeconds
            autoRecover      = [bool]$AutoRecover
        }
        try { $status | ConvertTo-Json -Depth 6 | Set-Content -Path $StatusFile -Encoding UTF8 } catch { }

        if ($Once) { break }

        if ($DurationMinutes -gt 0) {
            $elapsed = (Get-Date) - $start
            if ($elapsed.TotalMinutes -ge $DurationMinutes) { break }
        }

        Start-Sleep -Seconds $IntervalSeconds
    } while ($true)
}
catch {
    # swallow any unhandled exceptions
}
finally {
    try { [Environment]::Exit(0) } catch { exit 0 }
}
