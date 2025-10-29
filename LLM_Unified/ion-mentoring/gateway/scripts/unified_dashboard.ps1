<#
.SYNOPSIS
    Lumen Gateway ?듯빀 ?곹깭 ??쒕낫??
    
.DESCRIPTION
    Gateway, Prometheus, Alertmanager, Cloud Run ?곹깭瑜?
    ?ㅼ떆媛꾩쑝濡?紐⑤땲?곕쭅?섍퀬 ?쒖떆?⑸땲??
    
.PARAMETER RefreshInterval
    ?덈줈怨좎묠 媛꾧꺽 (珥? 湲곕낯媛? 5)
    
.PARAMETER ShowDetails
    ?곸꽭 ?뺣낫 ?쒖떆 ?щ?
    
.EXAMPLE
    .\unified_dashboard.ps1
    湲곕낯 ?ㅼ젙?쇰줈 ??쒕낫???ㅽ뻾
    
.EXAMPLE
    .\unified_dashboard.ps1 -RefreshInterval 10 -ShowDetails
    10珥덈쭏???덈줈怨좎묠, ?곸꽭 ?뺣낫 ?쒖떆
#>

[CmdletBinding()]
param(
    [int]$RefreshInterval = 5,
    [switch]$ShowDetails
)

$ErrorActionPreference = "SilentlyContinue"

# ?됱긽 ?뺤쓽
function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    
    if ($NoNewline) {
        Write-Host $Text -ForegroundColor $Color -NoNewline
    }
    else {
        Write-Host $Text -ForegroundColor $Color
    }
}

function Get-PortStatus {
    param([int]$Port)
    
    $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($conn) {
        $proc = Get-Process -Id $conn.OwningProcess[0] -ErrorAction SilentlyContinue
        return @{
            Active      = $true
            ProcessName = $proc.ProcessName
            PID         = $proc.Id
            Memory      = [math]::Round($proc.WorkingSet64 / 1MB, 1)
        }
    }
    return @{ Active = $false }
}

function Get-MetricsStats {
    $csvPath = "D:\nas_backup\LLM_Unified\ion-mentoring\gateway\logs\metrics.csv"
    
    if (-not (Test-Path $csvPath)) {
        return $null
    }
    
    $lines = Get-Content $csvPath
    $totalRecords = $lines.Count - 1
    
    if ($totalRecords -lt 1) {
        return $null
    }
    
    # 理쒓렐 10媛??덉퐫??遺꾩꽍
    $recentLines = $lines | Select-Object -Last 11 | Select-Object -Skip 1
    $downCount = 0
    $mockCount = 0
    $responseTimes = @()
    
    foreach ($line in $recentLines) {
        $fields = $line -split ','
        if ($fields[1] -eq '0') { $downCount++ }
        if ($fields[3] -eq '1') { $mockCount++ }
        $responseTimes += [double]$fields[2]
    }
    
    return @{
        TotalRecords     = $totalRecords
        RecentDown       = $downCount
        RecentMock       = $mockCount
        AvgResponseTime  = [math]::Round(($responseTimes | Measure-Object -Average).Average, 2)
        LastResponseTime = $responseTimes[-1]
    }
}

function Test-CloudRunHealth {
    try {
        $url = "https://ion-api-64076350717.us-central1.run.app/health"
        $response = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 5 -ErrorAction Stop
        return @{
            Healthy       = ($response.status -eq "healthy")
            Version       = $response.version
            PipelineReady = $response.pipeline_ready
            CacheEnabled  = $response.redis_cache.enabled
        }
    }
    catch {
        return @{
            Healthy = $false
            Error   = $_.Exception.Message
        }
    }
}

function Get-PrometheusStats {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/targets" -TimeoutSec 3
        if ($response.status -eq "success") {
            $targets = $response.data.activeTargets
            $upCount = ($targets | Where-Object { $_.health -eq "up" }).Count
            $totalCount = $targets.Count
            return @{
                Active       = $true
                TargetsUp    = $upCount
                TargetsTotal = $totalCount
            }
        }
    }
    catch {}
    
    return @{ Active = $false }
}

function Get-AlertmanagerStats {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9093/api/v1/alerts" -TimeoutSec 3
        if ($response.status -eq "success") {
            $alerts = $response.data
            $activeCount = ($alerts | Where-Object { $_.status.state -eq "active" }).Count
            return @{
                Active       = $true
                TotalAlerts  = $alerts.Count
                ActiveAlerts = $activeCount
            }
        }
    }
    catch {}
    
    return @{ Active = $false }
}

function Show-Dashboard {
    Clear-Host
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "`n?붴븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?? -ForegroundColor Cyan
    Write-Host "??          " -NoNewline -ForegroundColor Cyan
    Write-Host "?뙚 Lumen Gateway v1.0 - Unified Dashboard ?뙚" -NoNewline -ForegroundColor Yellow
    Write-Host "           ?? -ForegroundColor Cyan
    Write-Host "?졻븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?? -ForegroundColor Cyan
    Write-Host "?? Last Update: $timestamp                               ?? -ForegroundColor Cyan
    Write-Host "?싢븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧??n" -ForegroundColor Cyan
    
    # === Local Services ===
    Write-Host "?뚢??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    Write-Host "???뼢截? LOCAL SERVICES                                              ?? -ForegroundColor White
    Write-Host "?붴??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    
    $services = @(
        @{ Name = "Gateway Exporter"; Port = 9108 },
        @{ Name = "Prometheus"; Port = 9090 },
        @{ Name = "Alertmanager"; Port = 9093 }
    )
    
    foreach ($svc in $services) {
        $status = Get-PortStatus -Port $svc.Port
        
        Write-Host "  " -NoNewline
        if ($status.Active) {
            Write-ColorText "??" -Color Green -NoNewline
            Write-ColorText "$($svc.Name) " -Color White -NoNewline
            Write-ColorText "(Port $($svc.Port))" -Color Gray
            if ($ShowDetails) {
                Write-Host "     ?붴? PID: $($status.PID) | Memory: $($status.Memory)MB | Process: $($status.ProcessName)" -ForegroundColor DarkGray
            }
        }
        else {
            Write-ColorText "??" -Color Red -NoNewline
            Write-ColorText "$($svc.Name) " -Color White -NoNewline
            Write-ColorText "(Port $($svc.Port) - Not Running)" -Color DarkRed
        }
    }
    
    # === Prometheus Stats ===
    Write-Host "`n?뚢??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    Write-Host "???뱤 PROMETHEUS                                                    ?? -ForegroundColor White
    Write-Host "?붴??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    
    $promStats = Get-PrometheusStats
    if ($promStats.Active) {
        Write-Host "  " -NoNewline
        Write-ColorText "??Targets: " -Color Green -NoNewline
        Write-ColorText "$($promStats.TargetsUp)/$($promStats.TargetsTotal) UP" -Color $(if ($promStats.TargetsUp -eq $promStats.TargetsTotal) { "Green" } else { "Yellow" })
        
        if ($ShowDetails) {
            Write-Host "     ?붴? UI: http://localhost:9090" -ForegroundColor DarkGray
        }
    }
    else {
        Write-Host "  ??Prometheus not responding" -ForegroundColor Red
    }
    
    # === Alertmanager Stats ===
    Write-Host "`n?뚢??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    Write-Host "???뵒 ALERTMANAGER                                                  ?? -ForegroundColor White
    Write-Host "?붴??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    
    $alertStats = Get-AlertmanagerStats
    if ($alertStats.Active) {
        Write-Host "  " -NoNewline
        if ($alertStats.ActiveAlerts -gt 0) {
            Write-ColorText "?좑툘  Active Alerts: " -Color Yellow -NoNewline
            Write-ColorText "$($alertStats.ActiveAlerts)/$($alertStats.TotalAlerts)" -Color Red
        }
        else {
            Write-ColorText "??No Active Alerts " -Color Green -NoNewline
            Write-ColorText "($($alertStats.TotalAlerts) total)" -Color Gray
        }
        
        if ($ShowDetails) {
            Write-Host "     | -- UI: http://localhost:9093" -ForegroundColor DarkGray
        }
    }
    else {
        Write-Host "  ??Alertmanager not responding" -ForegroundColor Red
    }
    
    # === Gateway Metrics ===
    Write-Host "`n?뚢??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    Write-Host "???뱢 GATEWAY METRICS                                               ?? -ForegroundColor White
    Write-Host "?붴??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    
    $metrics = Get-MetricsStats
    if ($metrics) {
        Write-Host "  Total Records:     " -NoNewline -ForegroundColor Gray
        Write-Host $metrics.TotalRecords -ForegroundColor White
        
        Write-Host "  Avg Response Time: " -NoNewline -ForegroundColor Gray
        $rtColor = if ($metrics.AvgResponseTime -lt 300) { "Green" } elseif ($metrics.AvgResponseTime -lt 500) { "Yellow" } else { "Red" }
        Write-Host "$($metrics.AvgResponseTime)ms" -ForegroundColor $rtColor
        
        Write-Host "  Last Response:     " -NoNewline -ForegroundColor Gray
        Write-Host "$($metrics.LastResponseTime)ms" -ForegroundColor $rtColor
        
        Write-Host "  Recent Health:     " -NoNewline -ForegroundColor Gray
        if ($metrics.RecentDown -eq 0) {
            Write-Host "??100% UP (10/10)" -ForegroundColor Green
        }
        else {
            Write-Host "?좑툘  $(10 - $metrics.RecentDown)/10 UP" -ForegroundColor Yellow
        }
        
        Write-Host "  Mock Mode:         " -NoNewline -ForegroundColor Gray
        if ($metrics.RecentMock -eq 0) {
            Write-Host "??Real AI (0/10)" -ForegroundColor Green
        }
        else {
            Write-Host "?좑툘  Mock detected ($($metrics.RecentMock)/10)" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  ?좑툘  No metrics data available" -ForegroundColor Yellow
    }
    
    # === Cloud Run Status ===
    Write-Host "`n?뚢??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    Write-Host "???곻툘  CLOUD RUN (ION API)                                         ?? -ForegroundColor White
    Write-Host "?붴??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    
    $cloudRun = Test-CloudRunHealth
    if ($cloudRun.Healthy) {
        Write-Host "  " -NoNewline
        Write-ColorText "??Service Healthy" -Color Green
        
        Write-Host "  Version:           " -NoNewline -ForegroundColor Gray
        Write-Host $cloudRun.Version -ForegroundColor White
        
        Write-Host "  Pipeline Ready:    " -NoNewline -ForegroundColor Gray
        Write-Host $(if ($cloudRun.PipelineReady) { "??Yes" } else { "??No" }) -ForegroundColor $(if ($cloudRun.PipelineReady) { "Green" } else { "Red" })
        
        Write-Host "  Cache:             " -NoNewline -ForegroundColor Gray
        Write-Host $(if ($cloudRun.CacheEnabled) { "??Enabled" } else { "?좑툘  Disabled" }) -ForegroundColor $(if ($cloudRun.CacheEnabled) { "Green" } else { "Yellow" })
        
        if ($ShowDetails) {
            Write-Host "     ?붴? URL: https://ion-api-64076350717.us-central1.run.app" -ForegroundColor DarkGray
        }
    }
    else {
        Write-Host "  ??Service Unhealthy or Unreachable" -ForegroundColor Red
        if ($cloudRun.Error) {
            Write-Host "     ?붴? Error: $($cloudRun.Error)" -ForegroundColor DarkRed
        }
    }
    
    # === Footer ===
    Write-Host "`n?뚢??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
    Write-Host "??Press Ctrl+C to exit | Refresh: ${RefreshInterval}s | Details: $ShowDetails        ?? -ForegroundColor DarkGray
    Write-Host "?붴??????????????????????????????????????????????????????????????????? -ForegroundColor Gray
}

# 硫붿씤 猷⑦봽
Write-Host "`nStarting Unified Dashboard..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow
Start-Sleep -Seconds 2

while ($true) {
    Show-Dashboard
    Start-Sleep -Seconds $RefreshInterval
}

