# Open Unified Monitoring Dashboard
# Quick access to all monitoring dashboards and reports

param(
    [ValidateSet("All", "Visual", "Performance", "Monitoring", "Latency", "Health")]
    [string]$Dashboard = "All",

    [switch]$Refresh,  # Refresh before opening
    [switch]$Browser   # Open in default browser instead of VS Code
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Continue"
$outputDir = "$WorkspaceRoot\outputs"

Write-Host "`n" -NoNewline
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Monitoring Dashboard Launcher" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

$dashboards = @{
    Visual = @{
        File = "$outputDir\system_dashboard_latest.html"
        Name = "Visual HTML Dashboard"
        Generator = "$PSScriptRoot\generate_visual_dashboard.ps1"
        PreferBrowser = $true
    }
    Performance = @{
        File = "$outputDir\performance_dashboard_latest.md"
        Name = "Performance Metrics Dashboard"
        Generator = "$PSScriptRoot\generate_performance_dashboard.ps1"
        PreferBrowser = $false
    }
    Monitoring = @{
        File = "$outputDir\monitoring_report_latest.md"
        Name = "24h Monitoring Report"
        Generator = "$PSScriptRoot\generate_monitoring_report.ps1"
        PreferBrowser = $false
    }
    Latency = @{
        File = "$outputDir\latency_spike_analysis.md"
        Name = "Latency Spike Analysis"
        Generator = "$PSScriptRoot\analyze_latency_spikes.ps1"
        PreferBrowser = $false
    }
    Health = @{
        File = "$outputDir\health_gate_state.json"
        Name = "AGI Health State"
        Generator = $null
        PreferBrowser = $false
    }
}

function Open-Dashboard {
    param(
        [string]$Key,
        [hashtable]$Info
    )

    Write-Host "[$Key] $($Info.Name)" -ForegroundColor Cyan

    # Refresh if requested
    if ($Refresh -and $Info.Generator) {
        Write-Host "  Refreshing..." -NoNewline
        try {
            $null = & $Info.Generator -ErrorAction Stop 2>&1
            Write-Host " Done" -ForegroundColor Green
        }
        catch {
            Write-Host " Failed" -ForegroundColor Yellow
        }
    }

    # Check if file exists
    if (-not (Test-Path $Info.File)) {
        Write-Host "  File not found: $($Info.File)" -ForegroundColor Red

        if ($Info.Generator) {
            Write-Host "  Generating..." -NoNewline
            try {
                $null = & $Info.Generator -ErrorAction Stop 2>&1
                Write-Host " Done" -ForegroundColor Green
            }
            catch {
                Write-Host " Failed: $_" -ForegroundColor Red
                return
            }
        }
        else {
            Write-Host "  Skipping (no generator available)" -ForegroundColor Yellow
            return
        }
    }

    # Open file
    if ($Browser -or $Info.PreferBrowser) {
        Write-Host "  Opening in browser..." -ForegroundColor White
        Start-Process $Info.File
    }
    else {
        Write-Host "  Opening in VS Code..." -ForegroundColor White
        code $Info.File
    }

    Write-Host ""
}

# Open requested dashboards
if ($Dashboard -eq "All") {
    Write-Host "Opening all dashboards...`n" -ForegroundColor Yellow

    foreach ($key in $dashboards.Keys) {
        Open-Dashboard -Key $key -Info $dashboards[$key]
    }
}
else {
    if ($dashboards.ContainsKey($Dashboard)) {
        Open-Dashboard -Key $Dashboard -Info $dashboards[$Dashboard]
    }
    else {
        Write-Host "Unknown dashboard: $Dashboard" -ForegroundColor Red
        Write-Host "Available: All, Visual, Performance, Monitoring, Latency, Health" -ForegroundColor Yellow
    }
}

Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
Write-Host "Dashboard Paths:" -ForegroundColor Cyan
foreach ($key in $dashboards.Keys) {
    $exists = Test-Path $dashboards[$key].File
    $color = if ($exists) { "Green" } else { "Red" }
    $status = if ($exists) { "✓" } else { "✗" }
    Write-Host "  [$status] $key : $($dashboards[$key].File)" -ForegroundColor $color
}
Write-Host ""

Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  .\open_monitoring_dashboard.ps1                 # Open all dashboards" -ForegroundColor Gray
Write-Host "  .\open_monitoring_dashboard.ps1 -Dashboard Visual -Browser" -ForegroundColor Gray
Write-Host "  .\open_monitoring_dashboard.ps1 -Refresh        # Refresh before opening" -ForegroundColor Gray
Write-Host ""