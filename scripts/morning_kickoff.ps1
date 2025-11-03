#Requires -Version 5.1
<#
.SYNOPSIS
    Morning kickoff: quick health + monitoring report + optional dashboard open.
.EXAMPLE
    .\morning_kickoff.ps1 -Hours 1 -OpenHtml
#>

param(
    [int]$Hours = 1,
    [switch]$OpenHtml,
    [switch]$WithStatus
)

$ErrorActionPreference = "Continue"
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}

Write-Host "`n===============================================" -ForegroundColor Cyan
Write-Host "|   Morning Kickoff                           |" -ForegroundColor Cyan
Write-Host "===============================================`n" -ForegroundColor Cyan

$root = Split-Path -Parent $PSScriptRoot
$dashboardPath = Join-Path $root 'outputs\monitoring_dashboard_latest.html'

function Invoke-ScriptIfExists {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [string[]]$Args
    )
    if (Test-Path -LiteralPath $Path) {
        & $Path @Args
        return $true
    }
    return $false
}

# 1) Quick health/status
Write-Host "[1/5] Running quick health/status..." -ForegroundColor Yellow
$ran = $false
$ran = Invoke-ScriptIfExists -Path (Join-Path $PSScriptRoot 'quick_status.ps1') -Args @()
if (-not $ran) { $ran = Invoke-ScriptIfExists -Path (Join-Path $PSScriptRoot 'system_health_check.ps1') -Args @() }
if ($ran) { Write-Host "  Health/status complete." -ForegroundColor Green } else { Write-Host "  Skipped (no script found)." -ForegroundColor Gray }

# 2) Auto-Stabilizer daemon check
Write-Host "`n[2/7] Checking Auto-Stabilizer daemon..." -ForegroundColor Yellow
$stabilizerCheck = Join-Path $PSScriptRoot 'check_auto_stabilizer_status.ps1'
if (Test-Path -LiteralPath $stabilizerCheck) {
    try {
        & $stabilizerCheck | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Auto-Stabilizer daemon is running." -ForegroundColor Green
        }
        else {
            Write-Host "  Warning: Auto-Stabilizer daemon is not running." -ForegroundColor Yellow
            Write-Host "  Tip: Run .\scripts\start_auto_stabilizer_daemon.ps1 -KillExisting" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  Warning: Auto-Stabilizer check failed." -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Skipped (check_auto_stabilizer_status.ps1 not found)." -ForegroundColor Gray
}

# 2.5) Emotion-Triggered Stabilizer check (once)
Write-Host "`n[2.5/7] Emotion-Triggered Stabilizer check..." -ForegroundColor Yellow
$emotionStabilizer = Join-Path $PSScriptRoot 'start_emotion_stabilizer.ps1'
if (Test-Path -LiteralPath $emotionStabilizer) {
    try {
        & $emotionStabilizer -Once -DryRun | Out-Null
        Write-Host "  Emotion signals evaluated." -ForegroundColor Green
        
        # Check stabilizer output log for recommendations
        $stabLog = Join-Path $root 'outputs\emotion_stabilizer.log'
        if (Test-Path -LiteralPath $stabLog) {
            $lastLines = Get-Content -LiteralPath $stabLog -Tail 5
            $needsAction = $false
            foreach ($line in $lastLines) {
                if ($line -match 'recommended|CRITICAL') {
                    Write-Host "  $line" -ForegroundColor Yellow
                    $needsAction = $true
                }
            }
            if (-not $needsAction) {
                Write-Host "  System emotionally stable (no action needed)." -ForegroundColor Green
            }
        }
    }
    catch {
        Write-Host "  Warning: Emotion Stabilizer check failed." -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Skipped (start_emotion_stabilizer.ps1 not found)." -ForegroundColor Gray
}

# 3) Daily health snapshot
Write-Host "`n[3/7] Saving health snapshot..." -ForegroundColor Yellow
$snapScript = Join-Path $PSScriptRoot 'daily_health_snapshot.ps1'
if (Test-Path -LiteralPath $snapScript) {
    try {
        & $snapScript | Out-Null
        Write-Host "  Health snapshot saved." -ForegroundColor Green
    }
    catch {
        Write-Host "  Warning: health snapshot failed (continuing)." -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Skipped (daily_health_snapshot.ps1 not found)." -ForegroundColor Gray
}

# 4) Monitoring report (JSON/MD/HTML)
Write-Host "`n[4/7] Generating monitoring report..." -ForegroundColor Yellow
$reportScript = Join-Path $PSScriptRoot 'generate_monitoring_report.ps1'
if (Test-Path -LiteralPath $reportScript) {
    $ok = $true
    try {
        & $reportScript -Hours $Hours
        if ($LASTEXITCODE -ne 0) { $ok = $false }
    }
    catch { $ok = $false }
    if ($ok) {
        Write-Host "  Monitoring report generated." -ForegroundColor Green
        $policySnapshotPath = Join-Path $root 'outputs\policy_ab_snapshot_latest.md'
        if (Test-Path -LiteralPath $policySnapshotPath) {
            Write-Host "  Policy snapshot preview:" -ForegroundColor Gray
            try {
                $previewLines = Get-Content -LiteralPath $policySnapshotPath -TotalCount 20
                if ($previewLines -and $previewLines.Count -gt 0) {
                    foreach ($line in $previewLines) {
                        Write-Host ("    {0}" -f $line) -ForegroundColor Gray
                    }
                    $totalLines = (Get-Content -LiteralPath $policySnapshotPath).Count
                    if ($totalLines -gt 20) {
                        Write-Host "    ... (see outputs\policy_ab_snapshot_latest.md for full report)" -ForegroundColor Gray
                    }
                }
                else {
                    Write-Host "    (no policy snapshot content)" -ForegroundColor Gray
                }
            }
            catch {
                Write-Host ("    (policy preview unavailable: {0})" -f $_.Exception.Message) -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "  Policy snapshot not found (expected at outputs\policy_ab_snapshot_latest.md)" -ForegroundColor Yellow
        }
        if ($OpenHtml -and (Test-Path -LiteralPath $dashboardPath)) {
            try { Start-Process -FilePath $dashboardPath } catch {}
            Write-Host "  Opened: $dashboardPath" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  Warning: report generation failed (see console)." -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Skipped (generate_monitoring_report.ps1 not found)." -ForegroundColor Gray
}

# 5) Performance dashboard (7 days)
Write-Host "`n[5/7] Regenerating performance dashboard..." -ForegroundColor Yellow
$perfDash = Join-Path $PSScriptRoot 'generate_performance_dashboard.ps1'
if (Test-Path -LiteralPath $perfDash) {
    try {
        & $perfDash -Days 7 -WriteLatest -ExportJson -ExportCsv | Out-Null
        Write-Host "  Performance dashboard updated." -ForegroundColor Green
    }
    catch {
        Write-Host "  Warning: performance dashboard generation failed." -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Skipped (generate_performance_dashboard.ps1 not found)." -ForegroundColor Gray
}

# 6) Optional: detailed status
if ($WithStatus) {
    Write-Host "`n[6/7] Gathering detailed status..." -ForegroundColor Yellow
    
    Write-Host "`n  [6.1] Resonance digest (12h window)..." -ForegroundColor Yellow
    $rd = Join-Path $PSScriptRoot 'morning_resonance_digest.ps1'
    if (Test-Path -LiteralPath $rd) {
        try { & $rd -Hours 12 | Out-Null; Write-Host "    Resonance digest generated." -ForegroundColor Green } catch { Write-Host "    Resonance digest failed (continuing)." -ForegroundColor Yellow }
    }
    
    Write-Host "`n  [6.2] Quick resonance status..." -ForegroundColor Yellow
    $rs = Join-Path $PSScriptRoot 'quick_resonance_status.ps1'
    if (Test-Path -LiteralPath $rs) {
        try { & $rs -ShowLedger | Out-Host } catch { Write-Host "    quick_resonance_status errored: $($_.Exception.Message)" -ForegroundColor Yellow }
    }
    else { Write-Host "    Skipped (quick_resonance_status.ps1 not found)." -ForegroundColor Gray }

    Write-Host "`n  [6.3] Last task latency summary..." -ForegroundColor Yellow
    $py = if (Test-Path "$root/.venv/Scripts/python.exe") { "$root/.venv/Scripts/python.exe" } else { 'python' }
    $sum = Join-Path $PSScriptRoot 'summarize_last_task_latency.py'
    if (Test-Path -LiteralPath $sum) {
        try { & $py $sum | Out-Host } catch { Write-Host "    summarize_last_task_latency errored: $($_.Exception.Message)" -ForegroundColor Yellow }
    }
    else { Write-Host "    Skipped (summarize_last_task_latency.py not found)." -ForegroundColor Gray }

    Write-Host "`n  [5.4] Policy A/B snapshot (ledger + synthetic)..." -ForegroundColor Yellow
    $polSnap = Join-Path $PSScriptRoot 'policy_ab_snapshot.ps1'
    if (Test-Path -LiteralPath $polSnap) {
        try { & $polSnap -Lines 50000 | Out-Null; Write-Host "    Policy A/B snapshot generated." -ForegroundColor Green } catch { Write-Host "    Policy A/B snapshot failed (continuing)." -ForegroundColor Yellow }
    }
    else { Write-Host "    Skipped (policy_ab_snapshot.ps1 not found)." -ForegroundColor Gray }
}

Write-Host "`n[Final] Summary" -ForegroundColor Yellow
Write-Host ("  Time Window: Last {0} hour(s)" -f $Hours) -ForegroundColor Gray
if (Test-Path -LiteralPath (Join-Path $root 'outputs\monitoring_metrics_latest.json')) {
    Write-Host "  Metrics: outputs\\monitoring_metrics_latest.json" -ForegroundColor Gray
}
if (Test-Path -LiteralPath (Join-Path $root 'outputs\monitoring_report_latest.md')) {
    Write-Host "  Report:  outputs\\monitoring_report_latest.md" -ForegroundColor Gray
}
if (Test-Path -LiteralPath $dashboardPath) {
    Write-Host "  Dashboard: $dashboardPath" -ForegroundColor Gray
}

Write-Host "`nMorning kickoff complete." -ForegroundColor Cyan

exit 0
