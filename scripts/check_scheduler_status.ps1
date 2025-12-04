param([switch]$Json)

$ErrorActionPreference = 'SilentlyContinue'
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $WorkspaceRoot 'outputs\ai_agent_monitor.pid'

$result = [ordered]@{
    pid_file     = $PidFile
    pid          = $null
    processAlive = $false
    message      = ''
}

if (Test-Path $PidFile) {
    $txt = Get-Content $PidFile -Raw
    $m = [regex]::Match($txt, 'PID=(\d+)')
    if ($m.Success) {
        $pid = [int]$m.Groups[1].Value
        $result.pid = $pid
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            $result.processAlive = $true
            $result.message = "Scheduler running (PID: $pid)"
        }
        else {
            $result.message = "PID file exists but process not running (PID: $pid)"
        }
    }
    else {
        $result.message = 'PID pattern not found in pid file'
    }
}
else {
    $result.message = 'PID file not found'
}

if ($Json) {
    $result | ConvertTo-Json -Depth 5 | Write-Output
}
else {
    if ($result.processAlive) {
        Write-Host $result.message -ForegroundColor Green
    }
    else {
        Write-Host $result.message -ForegroundColor Yellow
    }
}

if ($result.processAlive) { exit 0 } else { exit 1 }
