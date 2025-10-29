# Simple Monitoring Dashboard
# UTF-8 encoded PowerShell script

param(
    [int]$RefreshInterval = 5,
    [switch]$ShowDetails
)

function Write-ColorText {
    param($Text, $Color = "White", [switch]$NoNewline)
    if ($NoNewline) {
        Write-Host $Text -ForegroundColor $Color -NoNewline
    }
    else {
        Write-Host $Text -ForegroundColor $Color
    }
}

function Get-PortStatus {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($connection) {
        $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
        return @{
            Status      = "Running"
            ProcessName = $process.ProcessName
            ProcessId   = $connection.OwningProcess
            Memory      = [math]::Round($process.WorkingSet64 / 1MB, 2)
        }
    }
    return @{ Status = "Stopped" }
}

function Get-MetricsStats {
    $csvPath = "D:\nas_backup\LLM_Unified\ion-mentoring\gateway\logs\metrics.csv"
    if (Test-Path $csvPath) {
        $lines = Get-Content $csvPath -Tail 11
        $records = $lines | Select-Object -Skip 1 | ForEach-Object {
            $parts = $_ -split ','
            [PSCustomObject]@{
                Timestamp    = $parts[0]
                ION          = if ($parts[1] -eq "1") { "UP" } else { "DOWN" }
                Mock         = $parts[2]
                ResponseTime = [double]$parts[3]
            }
        }
        
        $totalRecords = (Get-Content $csvPath | Measure-Object -Line).Lines - 1
        $avgResponseTime = ($records | Measure-Object -Property ResponseTime -Average).Average
        $lastResponseTime = $records[-1].ResponseTime
        $upCount = ($records | Where-Object { $_.ION -eq "UP" }).Count
        $mockCount = ($records | Where-Object { $_.Mock -eq "1" }).Count
        
        return @{
            TotalRecords     = $totalRecords
            AvgResponseTime  = [math]::Round($avgResponseTime, 2)
            LastResponseTime = [math]::Round($lastResponseTime, 2)
            RecentUpCount    = $upCount
            RecentMockCount  = $mockCount
            TotalRecent      = $records.Count
        }
    }
    return $null
}

function Test-CloudRunHealth {
    try {
        $response = Invoke-RestMethod -Uri "https://ion-api-64076350717.us-central1.run.app/health" -TimeoutSec 5 -ErrorAction Stop
        return @{
            Status        = "Healthy"
            Version       = $response.version
            PipelineReady = $response.pipeline_ready
            CacheEnabled  = $response.redis_cache.enabled
        }
    }
    catch {
        return @{ Status = "Error"; Message = $_.Exception.Message }
    }
}

function Get-PrometheusStats {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/targets" -ErrorAction Stop
        $activeTargets = $response.data.activeTargets
        $upCount = ($activeTargets | Where-Object { $_.health -eq "up" }).Count
        return @{
            TotalTargets = $activeTargets.Count
            UpTargets    = $upCount
        }
    }
    catch {
        return $null
    }
}

function Get-AlertmanagerStats {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9093/api/v1/alerts" -ErrorAction Stop
        $alerts = $response.data
        $activeAlerts = ($alerts | Where-Object { $_.status.state -eq "active" }).Count
        return @{
            TotalAlerts  = $alerts.Count
            ActiveAlerts = $activeAlerts
        }
    }
    catch {
        return $null
    }
}

function Show-Dashboard {
    Clear-Host
    
    # Header
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "                    Lumen Gateway Monitoring Dashboard                         " -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "  Refresh: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')                           " -ForegroundColor Gray
    Write-Host ""
    
    # Local Services
    Write-Host "[Local Services]" -ForegroundColor Yellow
    Write-Host ""
    
    $gatewayStatus = Get-PortStatus -Port 9108
    $prometheusStatus = Get-PortStatus -Port 9090
    $alertmanagerStatus = Get-PortStatus -Port 9093
    
    Write-Host "  Gateway Exporter (9108): " -NoNewline
    if ($gatewayStatus.Status -eq "Running") {
        Write-ColorText "[OK] " -Color Green -NoNewline
        Write-ColorText "PID: $($gatewayStatus.ProcessId), Memory: $($gatewayStatus.Memory) MB" -Color Gray
    }
    else {
        Write-ColorText "[STOPPED]" -Color Red
    }
    
    Write-Host "  Prometheus (9090):       " -NoNewline
    if ($prometheusStatus.Status -eq "Running") {
        Write-ColorText "[OK] " -Color Green -NoNewline
        Write-ColorText "PID: $($prometheusStatus.ProcessId), Memory: $($prometheusStatus.Memory) MB" -Color Gray
    }
    else {
        Write-ColorText "[STOPPED]" -Color Red
    }
    
    Write-Host "  Alertmanager (9093):     " -NoNewline
    if ($alertmanagerStatus.Status -eq "Running") {
        Write-ColorText "[OK] " -Color Green -NoNewline
        Write-ColorText "PID: $($alertmanagerStatus.ProcessId), Memory: $($alertmanagerStatus.Memory) MB" -Color Gray
    }
    else {
        Write-ColorText "[STOPPED]" -Color Red
    }
    
    Write-Host ""
    
    # Prometheus Stats
    Write-Host "[Prometheus]" -ForegroundColor Yellow
    Write-Host ""
    
    $promStats = Get-PrometheusStats
    if ($promStats) {
        Write-Host "  Targets: " -NoNewline
        if ($promStats.UpTargets -eq $promStats.TotalTargets) {
            Write-ColorText "$($promStats.UpTargets)/$($promStats.TotalTargets) UP" -Color Green
        }
        else {
            Write-ColorText "$($promStats.UpTargets)/$($promStats.TotalTargets) UP" -Color Yellow
        }
        if ($ShowDetails) {
            Write-Host "    URL: http://localhost:9090" -ForegroundColor DarkGray
        }
    }
    else {
        Write-ColorText "  Not responding" -Color Red
    }
    
    Write-Host ""
    
    # Alertmanager Stats
    Write-Host "[Alertmanager]" -ForegroundColor Yellow
    Write-Host ""
    
    $alertStats = Get-AlertmanagerStats
    if ($alertStats) {
        Write-Host "  Active Alerts: " -NoNewline
        if ($alertStats.ActiveAlerts -eq 0) {
            Write-ColorText "0 (No Active Alerts)" -Color Green
        }
        else {
            Write-ColorText "$($alertStats.ActiveAlerts)" -Color Red
        }
        if ($ShowDetails) {
            Write-Host "    URL: http://localhost:9093" -ForegroundColor DarkGray
        }
    }
    else {
        Write-ColorText "  Not responding" -Color Red
    }
    
    Write-Host ""
    
    # Gateway Metrics
    Write-Host "[Gateway Metrics]" -ForegroundColor Yellow
    Write-Host ""
    
    $metrics = Get-MetricsStats
    if ($metrics) {
        Write-Host "  Total Records:     $($metrics.TotalRecords)"
        
        Write-Host "  Avg Response Time: " -NoNewline
        if ($metrics.AvgResponseTime -lt 300) {
            Write-ColorText "$($metrics.AvgResponseTime) ms" -Color Green
        }
        elseif ($metrics.AvgResponseTime -lt 500) {
            Write-ColorText "$($metrics.AvgResponseTime) ms" -Color Yellow
        }
        else {
            Write-ColorText "$($metrics.AvgResponseTime) ms" -Color Red
        }
        
        Write-Host "  Last Response Time:" -NoNewline
        if ($metrics.LastResponseTime -lt 300) {
            Write-ColorText "$($metrics.LastResponseTime) ms" -Color Green
        }
        elseif ($metrics.LastResponseTime -lt 500) {
            Write-ColorText "$($metrics.LastResponseTime) ms" -Color Yellow
        }
        else {
            Write-ColorText "$($metrics.LastResponseTime) ms" -Color Red
        }
        
        Write-Host "  Recent Health:     " -NoNewline
        if ($metrics.RecentUpCount -eq $metrics.TotalRecent) {
            Write-ColorText "$($metrics.RecentUpCount)/$($metrics.TotalRecent) UP" -Color Green
        }
        else {
            Write-ColorText "$($metrics.RecentUpCount)/$($metrics.TotalRecent) UP" -Color Yellow
        }
        
        Write-Host "  Mock Mode:         " -NoNewline
        if ($metrics.RecentMockCount -eq 0) {
            Write-ColorText "Real AI Mode" -Color Green
        }
        else {
            Write-ColorText "$($metrics.RecentMockCount)/$($metrics.TotalRecent) Mock" -Color Yellow
        }
    }
    else {
        Write-ColorText "  No metrics available" -Color Red
    }
    
    Write-Host ""
    
    # Cloud Run Status
    Write-Host "[Cloud Run Status]" -ForegroundColor Yellow
    Write-Host ""
    
    $cloudRun = Test-CloudRunHealth
    if ($cloudRun.Status -eq "Healthy") {
        Write-Host "  Service:       " -NoNewline
        Write-ColorText "Healthy" -Color Green
        Write-Host "  Version:       $($cloudRun.Version)"
        Write-Host "  Pipeline:      " -NoNewline
        if ($cloudRun.PipelineReady) {
            Write-ColorText "Ready" -Color Green
        }
        else {
            Write-ColorText "Not Ready" -Color Red
        }
        Write-Host "  Cache:         " -NoNewline
        if ($cloudRun.CacheEnabled) {
            Write-ColorText "Enabled" -Color Green
        }
        else {
            Write-ColorText "Disabled" -Color Yellow
        }
        if ($ShowDetails) {
            Write-Host "    URL: https://ion-api-64076350717.us-central1.run.app" -ForegroundColor DarkGray
        }
    }
    else {
        Write-ColorText "  Service: Unhealthy" -Color Red
        Write-Host "  Error: $($cloudRun.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "  Press Ctrl+C to exit | Refresh: $RefreshInterval seconds | Details: $ShowDetails" -ForegroundColor Gray
    Write-Host "================================================================================" -ForegroundColor Cyan
}

# Main Loop
while ($true) {
    Show-Dashboard
    Start-Sleep -Seconds $RefreshInterval
}
