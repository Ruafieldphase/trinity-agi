param([switch]$OpenBrowser)

$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8; $OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}
$ErrorActionPreference = 'Continue'
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$OutDir = Join-Path $WorkspaceRoot 'outputs'
$HtmlPath = Join-Path $OutDir 'ai_autonomous_dashboard.html'

function Get-StatusEmoji {
    param([bool]$healthy)
    if ($healthy) { return 'OK' } else { return 'X' }
}

function Get-OpsManagerStatus {
    $statusFile = Join-Path $OutDir 'ai_ops_manager_status.json'
    if (Test-Path $statusFile) {
        try {
            $s = Get-Content $statusFile -Raw | ConvertFrom-Json
            return [pscustomobject]@{
                exists           = $true
                ts               = $s.ts
                schedulerHealthy = $s.schedulerHealthy
                queueHealthy     = $s.queueHealthy
                actionTaken      = $s.actionTaken
                stabilized       = $s.stabilized
                loops            = $s.loops
            }
        }
        catch {
            return [pscustomobject]@{ exists = $false }
        }
    }
    return [pscustomobject]@{ exists = $false }
}

function Get-SchedulerStatus {
    try {
        $checkScript = Join-Path $WorkspaceRoot 'scripts\check_scheduler_status.ps1'
        $p = Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $checkScript -Wait -PassThru -WindowStyle Hidden
        return ($p.ExitCode -eq 0)
    }
    catch { return $false }
}

function Get-QueueServerStatus {
    try {
        $r = Invoke-WebRequest -Uri 'http://localhost:8091/api/health' -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        return ($r.StatusCode -eq 200)
    }
    catch { return $false }
}

function Get-RegistrationStatus {
    try {
        $regScript = Join-Path $WorkspaceRoot 'scripts\register_ai_ops_manager.ps1'
        $p = Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $regScript, '-Status' -Wait -PassThru -WindowStyle Hidden
        return ($p.ExitCode -eq 0)
    }
    catch { return $false }
}

$ops = Get-OpsManagerStatus
$scheduler = Get-SchedulerStatus
$queue = Get-QueueServerStatus
$registered = Get-RegistrationStatus

$schedulerEmoji = Get-StatusEmoji $scheduler
$queueEmoji = Get-StatusEmoji $queue
$registeredEmoji = Get-StatusEmoji $registered

$html = @"
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Autonomous Operations Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 30px; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .card { background: white; border-radius: 15px; padding: 25px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .status-item { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 10px; text-align: center; }
        .status-item h3 { font-size: 1.2em; margin-bottom: 10px; color: #333; }
        .status-value { font-size: 2em; margin: 10px 0; }
        .healthy { color: #10b981; }
        .unhealthy { color: #ef4444; }
        .info-section { background: #f8fafc; padding: 15px; border-radius: 8px; margin-top: 15px; }
        .info-section h4 { color: #475569; margin-bottom: 10px; }
        .info-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }
        .info-row:last-child { border-bottom: none; }
        .label { font-weight: 600; color: #64748b; }
        .value { color: #1e293b; }
        .timestamp { text-align: center; color: #94a3b8; font-size: 0.9em; margin-top: 20px; }
        .footer { text-align: center; color: white; margin-top: 30px; opacity: 0.8; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Autonomous Operations Dashboard</h1>
        
        <div class="card">
            <h2 style="margin-bottom: 20px; color: #1e293b;">System Status</h2>
            <div class="status-grid">
                <div class="status-item">
                    <h3>AI Scheduler</h3>
                    <div class="status-value">$schedulerEmoji</div>
                    <div class="$(if($scheduler){'healthy'}else{'unhealthy'})">$(if($scheduler){'Running'}else{'Stopped'})</div>
                </div>
                <div class="status-item">
                    <h3>Queue Server (8091)</h3>
                    <div class="status-value">$queueEmoji</div>
                    <div class="$(if($queue){'healthy'}else{'unhealthy'})">$(if($queue){'Healthy'}else{'Down'})</div>
                </div>
                <div class="status-item">
                    <h3>Auto Manager</h3>
                    <div class="status-value">$registeredEmoji</div>
                    <div class="$(if($registered){'healthy'}else{'unhealthy'})">$(if($registered){'Registered'}else{'Not Registered'})</div>
                </div>
            </div>
        </div>

        $(if($ops.exists) {
"        <div class='card'>
            <h2 style='margin-bottom: 20px; color: #1e293b;'>AI Ops Manager Details</h2>
            <div class='info-section'>
                <div class='info-row'>
                    <span class='label'>Scheduler Health:</span>
                    <span class='value'>$(Get-StatusEmoji $ops.schedulerHealthy) $(if($ops.schedulerHealthy){'Healthy'}else{'Unhealthy'})</span>
                </div>
                <div class='info-row'>
                    <span class='label'>Queue Health:</span>
                    <span class='value'>$(Get-StatusEmoji $ops.queueHealthy) $(if($ops.queueHealthy){'Healthy'}else{'Unhealthy'})</span>
                </div>
                <div class='info-row'>
                    <span class='label'>Action Taken:</span>
                    <span class='value'>$(if($ops.actionTaken){'Yes'}else{'No'})</span>
                </div>
                <div class='info-row'>
                    <span class='label'>Stabilized:</span>
                    <span class='value'>$(if($ops.stabilized){'Yes'}else{'No'})</span>
                </div>
                <div class='info-row'>
                    <span class='label'>Loop Count:</span>
                    <span class='value'>$($ops.loops)</span>
                </div>
                <div class='info-row'>
                    <span class='label'>Last Update:</span>
                    <span class='value'>$($ops.ts)</span>
                </div>
            </div>
        </div>"
        })

        <div class="timestamp">
            Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        </div>
        
        <div class="footer">
            <p>🚀 Autonomous AI Operations - Self-Healing System</p>
            <p>Refresh this page to see latest status</p>
        </div>
    </div>
</body>
</html>
"@

try {
    $html | Set-Content -Path $HtmlPath -Encoding UTF8
    Write-Host "Dashboard created: $HtmlPath" -ForegroundColor Green
    if ($OpenBrowser) {
        Start-Process $HtmlPath
    }
}
catch {
    Write-Host "Error creating dashboard: $_" -ForegroundColor Red
    exit 1
}
