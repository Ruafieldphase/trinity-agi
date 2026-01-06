#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Automatic Cache Validation - Runs analysis and generates report
.DESCRIPTION
    This script runs cache performance analysis automatically at scheduled times.
    Saves results to outputs/ folder with timestamps.
.PARAMETER Hours
    Time window to analyze (default: 12)
.PARAMETER Interval
    Time bucket interval (default: 1)
.PARAMETER SendNotification
    Show Windows notification when complete
.EXAMPLE
    .\auto_cache_validation.ps1 -Hours 12 -Interval 1 -SendNotification
#>

param(
    [int]$Hours = 12,
    [int]$Interval = 1,
    [switch]$SendNotification
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


# UTF-8 console bootstrap
try { chcp 65001 > $null 2> $null } catch {}
try {
    [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
}
catch {}

$ErrorActionPreference = "Continue"
$RepoRoot = "$WorkspaceRoot"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Log file
$LogFile = "$RepoRoot\outputs\cache_validation_$Timestamp.log"
$null = New-Item -ItemType Directory -Force -Path "$RepoRoot\outputs"

function Write-Log {
    param([string]$Message)
    $LogMessage = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

Write-Log "=== Auto Cache Validation Started ==="
Write-Log "Hours: $Hours, Interval: $Interval"

# 1. Run timeline analysis
Write-Log "Running timeline analysis..."
try {
    $output = & py -3 "$RepoRoot\scripts\cache_monitor_timeline.py" --window-hours $Hours --interval-hours $Interval 2>&1
    Write-Log "Timeline analysis completed"
    $output | ForEach-Object { Write-Log "  $_" }
}
catch {
    Write-Log "ERROR: Timeline analysis failed - $_"
}

# 2. Run full cache analysis
Write-Log "Running full cache analysis..."
try {
    $output = & py -3 "$RepoRoot\scripts\analyze_cache_effectiveness.py" 2>&1
    Write-Log "Cache analysis completed"
    $output | ForEach-Object { Write-Log "  $_" }
}
catch {
    Write-Log "ERROR: Cache analysis failed - $_"
}

# 3. Run quick verify
Write-Log "Running quick verification..."
try {
    $output = & py -3 "$RepoRoot\scripts\quick_cache_verify.py" 2>&1
    Write-Log "Quick verify completed"
    $output | ForEach-Object { Write-Log "  $_" }
}
catch {
    Write-Log "ERROR: Quick verify failed - $_"
}

# 4. Parse hit rate from latest results
Write-Log "Checking hit rate..."
$HitRate = 0
$TimelineFile = "$RepoRoot\outputs\cache_timeline_latest.json"
if (Test-Path $TimelineFile) {
    try {
        $data = Get-Content $TimelineFile -Raw | ConvertFrom-Json
        $HitRate = $data.overall_hit_rate
        Write-Log "Current Hit Rate: $HitRate%"
    }
    catch {
        Write-Log "WARNING: Could not parse hit rate"
    }
}

# 5. Generate summary
$SummaryFile = "$RepoRoot\outputs\cache_validation_summary_$Timestamp.txt"
$Summary = @"
==============================================
CACHE VALIDATION SUMMARY
==============================================
Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Analysis Window: $Hours hours
Interval: $Interval hour(s)

RESULTS:
- Hit Rate: $HitRate%
- Status: $(if ($HitRate -ge 40) { "SUCCESS" } elseif ($HitRate -ge 20) { "IMPROVING" } elseif ($HitRate -ge 5) { "LOW" } else { "NO EFFECT" })

FILES GENERATED:
- Timeline: outputs/cache_timeline_latest.md
- Analysis: outputs/cache_analysis_latest.md
- Log: $(Split-Path $LogFile -Leaf)

NEXT STEPS:
$(if ($HitRate -ge 40) {
    "Optimization successful! Monitor over next 7 days."
} elseif ($HitRate -ge 20) {
    "Continue monitoring. Check again in 12 hours."
} elseif ($HitRate -ge 5) {
    "Limited improvement. Consider increasing TTL to 1200s."
} else {
    "No improvement yet. Wait 12 more hours or check AGI process."
})

==============================================
"@

$Summary | Out-File -FilePath $SummaryFile -Encoding UTF8
Write-Log "Summary saved to: $SummaryFile"

# 6. Send notification
if ($SendNotification) {
    $NotificationTitle = "Cache Validation Complete"
    $statusStr = if ($HitRate -ge 40) { 'SUCCESS' } elseif ($HitRate -ge 20) { 'IMPROVING' } elseif ($HitRate -ge 5) { 'LOW' } else { 'NO EFFECT' }
    $NotificationMessage = "Hit Rate: $HitRate% - Status: $statusStr"
    
    # Windows 10/11 Toast Notification
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        
        $template = @"
<toast>
    <visual>
        <binding template="ToastText02">
            <text id="1">$NotificationTitle</text>
            <text id="2">$NotificationMessage</text>
        </binding>
    </visual>
</toast>
"@
        
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Cache Validator").Show($toast)
        
        Write-Log "Notification sent"
    }
    catch {
        # Fallback: Simple message box
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show($NotificationMessage, $NotificationTitle, 'OK', 'Information')
        Write-Log "Notification shown (fallback)"
    }
}

Write-Log "=== Auto Cache Validation Completed ==="
Write-Log "Review: $SummaryFile"
Write-Host "`n** Validation complete! Check: $SummaryFile"

# Open summary in VS Code (optional)
if (Get-Command code -ErrorAction SilentlyContinue) {
    try {
        Start-Process code -ArgumentList $SummaryFile -NoNewWindow
    }
    catch {
        # Ignore if code not available
    }
}