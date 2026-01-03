# PowerShell 5.1+ Compatible
<#
.SYNOPSIS
    Generate success rate alerts for Auto-healer
.DESCRIPTION
    Calculates success rate from AGI Resonance Ledger and Task Queue Results,
    then generates alerts if thresholds are violated.
    
    Phase 7 Task 2: Disaster Recovery - Alert Generation
.EXAMPLE
    .\generate_success_rate_alert.ps1 -TimeWindowHours 24 -LowerThreshold 50
#>

param(
    [int]$TimeWindowHours = 24,
    [double]$LowerThreshold = 50.0,
    [double]$UpperThreshold = 85.0,
    [string]$OutputPath = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\alerts\success_rate_alert.json"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'
# Set-StrictMode -Version Latest  # Disabled for PowerShell 5 compatibility

# Ensure output directory exists
$outputDir = Split-Path -Parent $OutputPath
if (!(Test-Path -LiteralPath $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host "🔍 Phase 7 Task 2: Success Rate Alert Generation" -ForegroundColor Cyan
Write-Host "   Time Window: Last $TimeWindowHours hours" -ForegroundColor Gray
Write-Host "   Thresholds: $LowerThreshold% < Success Rate < $UpperThreshold%" -ForegroundColor Gray

# === 1. Load AGI Resonance Ledger ===
$ledgerPath = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\resonance_ledger.jsonl"
if (!(Test-Path -LiteralPath $ledgerPath)) {
    Write-Host "❌ Resonance Ledger not found: $ledgerPath" -ForegroundColor Red
    exit 1
}

Write-Host "`n📖 Loading AGI Resonance Ledger..." -ForegroundColor Yellow
$agiEvents = @()
Get-Content -Path $ledgerPath -Encoding UTF8 | ForEach-Object {
    try {
        $line = $_.Trim()
        if ($line) {
            $agiEvents += ($line | ConvertFrom-Json)
        }
    }
    catch {
        # Skip invalid JSON lines
    }
}

Write-Host "   Total Events: $($agiEvents.Count)" -ForegroundColor Gray

# === 2. Calculate AGI Success Rate ===
$now = Get-Date
$timeWindowStart = $now.AddHours(-$TimeWindowHours)

$recentEvents = $agiEvents | Where-Object {
    $event = $_
    $eventTime = $null
    if ($event.timestamp) {
        try { $eventTime = [DateTime]::Parse($event.timestamp) } catch { }
    }
    if (-not $eventTime -and $event.ts) {
        try { $eventTime = [DateTime]::Parse($event.ts) } catch { }
    }
    $eventTime -and ($eventTime -ge $timeWindowStart)
}

Write-Host "   Recent Events (last ${TimeWindowHours}h): $($recentEvents.Count)" -ForegroundColor Gray

# Filter task-related events
$taskEvents = $recentEvents | Where-Object {
    $event = $_
    $event.event -notin @('system_startup', 'system_shutdown') -and
    ($null -ne $event.agi_quality -or $null -ne $event.agi_confidence)
}

$successfulTasks = ($taskEvents | Where-Object {
        $event = $_
        ($event.agi_quality -and $event.agi_quality -ge 0.6) -or
        ($event.agi_confidence -and $event.agi_confidence -ge 0.7)
    }).Count

$totalAgiTasks = $taskEvents.Count
$agiSuccessRate = if ($totalAgiTasks -gt 0) {
    [math]::Round(($successfulTasks / $totalAgiTasks) * 100, 2)
}
else { 0.0 }

Write-Host "   AGI Success Rate: $agiSuccessRate% ($successfulTasks/$totalAgiTasks)" -ForegroundColor $(if ($agiSuccessRate -ge $LowerThreshold) { 'Green' } else { 'Red' })

# === 3. Load Task Queue Results ===
$queueServer = 'http://127.0.0.1:8091'
$queueSuccessRate = 0.0
$totalQueueTasks = 0
$successfulQueueTasks = 0

try {
    Write-Host "`n📦 Checking Task Queue Results..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "$queueServer/api/results" -Method Get -TimeoutSec 5
    if ($response.results) {
        $queueResults = $response.results | Where-Object {
            $result = $_
            if ($result.timestamp) {
                try {
                    $ts = [DateTime]::Parse($result.timestamp)
                    $ts -ge $timeWindowStart
                }
                catch { $false }
            }
            else { $false }
        }
        
        $totalQueueTasks = $queueResults.Count
        $successfulQueueTasks = ($queueResults | Where-Object { $_.success -eq $true }).Count
        
        if ($totalQueueTasks -gt 0) {
            $queueSuccessRate = [math]::Round(($successfulQueueTasks / $totalQueueTasks) * 100, 2)
        }
        
        Write-Host "   Queue Success Rate: $queueSuccessRate% ($successfulQueueTasks/$totalQueueTasks)" -ForegroundColor $(if ($queueSuccessRate -ge $LowerThreshold) { 'Green' } else { 'Red' })
    }
}
catch {
    Write-Host "   ⚠️  Task Queue Server offline or unreachable" -ForegroundColor Yellow
}

# === 4. Calculate Combined Success Rate ===
$totalTasks = $totalAgiTasks + $totalQueueTasks
$totalSuccessful = $successfulTasks + $successfulQueueTasks

$combinedSuccessRate = if ($totalTasks -gt 0) {
    [math]::Round(($totalSuccessful / $totalTasks) * 100, 2)
}
else { 0.0 }

Write-Host "`n📊 Combined Success Rate: $combinedSuccessRate% ($totalSuccessful/$totalTasks)" -ForegroundColor $(if ($combinedSuccessRate -ge $LowerThreshold) { 'Green' } elseif ($combinedSuccessRate -ge $UpperThreshold) { 'Yellow' } else { 'Red' })

# === 5. Generate Alert ===
$alert = @{
    timestamp          = $now.ToString('o')
    metric             = 'success_rate'
    value              = $combinedSuccessRate
    threshold_lower    = $LowerThreshold
    threshold_upper    = $UpperThreshold
    status             = if ($combinedSuccessRate -lt $LowerThreshold) { 'critical' }
    elseif ($combinedSuccessRate -lt $UpperThreshold) { 'warning' }
    else { 'healthy' }
    message            = "Success Rate: $combinedSuccessRate% (Threshold: $LowerThreshold%-$UpperThreshold%)"
    details            = @{
        time_window_hours      = $TimeWindowHours
        agi_success_rate       = $agiSuccessRate
        agi_successful_tasks   = $successfulTasks
        agi_total_tasks        = $totalAgiTasks
        queue_success_rate     = $queueSuccessRate
        queue_successful_tasks = $successfulQueueTasks
        queue_total_tasks      = $totalQueueTasks
        combined_success_rate  = $combinedSuccessRate
        combined_successful    = $totalSuccessful
        combined_total         = $totalTasks
    }
    suggested_strategy = if ($combinedSuccessRate -lt $LowerThreshold) { 'low_success_rate' }
    elseif ($combinedSuccessRate -lt $UpperThreshold) { 'warning_success_rate' }
    else { $null }
}

# === 6. Save Alert ===
$alert | ConvertTo-Json -Depth 10 | Set-Content -Path $OutputPath -Encoding UTF8
Write-Host "`n✅ Alert generated: $OutputPath" -ForegroundColor Green
Write-Host "   Status: $($alert.status)" -ForegroundColor $(if ($alert.status -eq 'critical') { 'Red' } elseif ($alert.status -eq 'warning') { 'Yellow' } else { 'Green' })

exit 0