param(
    [string]$OutPath = "$env:TEMP\quick_status_test.json"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = 'Stop'

function Write-Result {
    param([string]$Status, [string]$Message)
    $color = if ($Status -eq 'PASS') { 'Green' } elseif ($Status -eq 'WARN') { 'Yellow' } else { 'Red' }
    Write-Host ("[$Status] " + $Message) -ForegroundColor $color
}

try {
    $ws = "$WorkspaceRoot"
    $script = Join-Path $ws 'scripts\quick_status.ps1'

    if (-not (Test-Path -LiteralPath $script)) {
        Write-Result 'FAIL' "quick_status.ps1 not found at $script"
        exit 1
    }

    & $script -OutJson $OutPath -Perf | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Result 'FAIL' "quick_status.ps1 exited with code $LASTEXITCODE"
        exit 1
    }

    if (-not (Test-Path -LiteralPath $OutPath)) {
        Write-Result 'FAIL' "OutJson not produced: $OutPath"
        exit 1
    }

    $json = Get-Content -LiteralPath $OutPath -Raw | ConvertFrom-Json

    $basicOk = ($null -ne $json.Online) -and ($null -ne $json.Channels) -and ($null -ne $json.Timestamp)
    if ($basicOk) {
        Write-Result 'PASS' 'Basic fields present: Online, Channels, Timestamp'
    }
    else {
        Write-Result 'FAIL' 'Missing basic fields (Online/Channels/Timestamp)'
        exit 1
    }

    # Conditional checks based on available upstream sources
    $goalsPath = Join-Path $ws 'fdo_agi_repo\memory\goal_tracker.json'
    if (Test-Path -LiteralPath $goalsPath) {
        if ($null -ne $json.Goals) {
            Write-Result 'PASS' 'Goals block present'
        }
        else {
            Write-Result 'WARN' 'Goals source exists but Goals block missing in output'
        }
    }
    else {
        Write-Result 'PASS' 'Goals source not present (skipped)'
    }

    $perfPath = Join-Path $ws 'outputs\monitoring_metrics_latest.json'
    $perfAlt = Join-Path $ws 'outputs\performance_metrics_latest.json'
    $hasPerfSource = (Test-Path -LiteralPath $perfPath) -or (Test-Path -LiteralPath $perfAlt)
    if ($hasPerfSource) {
        if ($null -ne $json.Perf) {
            Write-Result 'PASS' 'Perf block present'
        }
        else {
            Write-Result 'WARN' 'Perf source exists but Perf block missing in output'
        }
    }
    else {
        Write-Result 'PASS' 'Perf source not present (skipped)'
    }

    Write-Result 'PASS' "quick_status output validation finished. OutJson: $OutPath"
    exit 0
}
catch {
    Write-Result 'FAIL' $_.Exception.Message
    exit 1
}