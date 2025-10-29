<#
.SYNOPSIS
    ION API 시스템 상태 대시보드
    
.DESCRIPTION
    Prometheus, Alertmanager, Gateway, Cloud Run 서비스 상태를 한눈에 확인합니다.
    
.PARAMETER Watch
    실시간 모니터링 모드 (자동 새로고침)
    
.PARAMETER RefreshSeconds
    새로고침 간격 (기본값: 5초)
    
.EXAMPLE
    .\system_dashboard.ps1
    현재 상태를 1회 표시
    
.EXAMPLE
    .\system_dashboard.ps1 -Watch -RefreshSeconds 10
    10초마다 자동 새로고침
#>

[CmdletBinding()]
param(
    [switch]$Watch,
    [int]$RefreshSeconds = 5
)

$ErrorActionPreference = "SilentlyContinue"

function Get-ProcessStatus {
    param(
        [string]$ProcessName
    )
    
    $process = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if ($process) {
        return @{
            Running    = $true
            PID        = $process.Id
            MemoryMB   = [math]::Round($process.WorkingSet64 / 1MB, 2)
            CPUSeconds = [math]::Round($process.TotalProcessorTime.TotalSeconds, 1)
        }
    }
    return @{ Running = $false }
}

function Get-PortStatus {
    param(
        [int]$Port
    )
    
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $connection
}

function Test-CloudRunService {
    param(
        [string]$Url
    )
    
    try {
        $response = Invoke-RestMethod -Uri "$Url/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
        return @{
            Healthy      = $true
            Status       = $response.status
            Version      = $response.version
            ResponseTime = 0
        }
    }
    catch {
        return @{ Healthy = $false; Error = $_.Exception.Message }
    }
}

function Show-Dashboard {
    Clear-Host
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host "  ION API System Dashboard" -ForegroundColor White
    Write-Host "  Last Update: $timestamp" -ForegroundColor Gray
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host ""
    
    # Prometheus
    Write-Host " Prometheus" -ForegroundColor Cyan -NoNewline
    $prometheus = Get-ProcessStatus -ProcessName "prometheus"
    if ($prometheus.Running) {
        Write-Host " [RUNNING]" -ForegroundColor Green
        Write-Host "    PID: $($prometheus.PID) | Memory: $($prometheus.MemoryMB) MB | Port: 9090" -ForegroundColor Gray
    }
    else {
        Write-Host " [STOPPED]" -ForegroundColor Red
    }
    Write-Host ""
    
    # Alertmanager
    Write-Host " Alertmanager" -ForegroundColor Cyan -NoNewline
    $alertmanager = Get-ProcessStatus -ProcessName "alertmanager"
    if ($alertmanager.Running) {
        Write-Host " [RUNNING]" -ForegroundColor Green
        Write-Host "    PID: $($alertmanager.PID) | Memory: $($alertmanager.MemoryMB) MB | Port: 9093" -ForegroundColor Gray
    }
    else {
        Write-Host " [STOPPED]" -ForegroundColor Red
    }
    Write-Host ""
    
    # Gateway Exporter
    Write-Host " Gateway Exporter" -ForegroundColor Cyan -NoNewline
    $gatewayPort = Get-PortStatus -Port 9108
    if ($gatewayPort) {
        Write-Host " [RUNNING]" -ForegroundColor Green
        Write-Host "    Port: 9108 | Metrics: http://localhost:9108/metrics" -ForegroundColor Gray
    }
    else {
        Write-Host " [STOPPED]" -ForegroundColor Red
    }
    Write-Host ""
    
    Write-Host ("-" * 80) -ForegroundColor DarkGray
    Write-Host ""
    
    # Cloud Run Services
    Write-Host " Cloud Run Services" -ForegroundColor Cyan
    Write-Host ""
    
    # ION API (Main)
    Write-Host "  ion-api (Main)" -ForegroundColor White -NoNewline
    $mainService = Test-CloudRunService -Url "https://ion-api-64076350717.us-central1.run.app"
    if ($mainService.Healthy) {
        Write-Host " [HEALTHY]" -ForegroundColor Green
        Write-Host "    Status: $($mainService.Status) | Version: $($mainService.Version)" -ForegroundColor Gray
    }
    else {
        Write-Host " [UNHEALTHY]" -ForegroundColor Red
        Write-Host "    Error: $($mainService.Error)" -ForegroundColor Red
    }
    Write-Host ""
    
    # ION API Canary
    Write-Host "  ion-api-canary" -ForegroundColor White -NoNewline
    $canaryService = Test-CloudRunService -Url "https://ion-api-canary-64076350717.us-central1.run.app"
    if ($canaryService.Healthy) {
        Write-Host " [HEALTHY]" -ForegroundColor Green
        Write-Host "    Status: $($canaryService.Status) | Version: $($canaryService.Version)" -ForegroundColor Gray
    }
    else {
        Write-Host " [UNHEALTHY]" -ForegroundColor Red
        Write-Host "    Error: $($canaryService.Error)" -ForegroundColor Red
    }
    Write-Host ""
    
    Write-Host ("-" * 80) -ForegroundColor DarkGray
    Write-Host ""
    
    # Quick Links
    Write-Host " Quick Links" -ForegroundColor Cyan
    Write-Host "  Prometheus:   http://localhost:9090" -ForegroundColor Gray
    Write-Host "  Alertmanager: http://localhost:9093" -ForegroundColor Gray
    Write-Host "  Gateway:      http://localhost:9108/metrics" -ForegroundColor Gray
    Write-Host "  ION API:      https://ion-api-64076350717.us-central1.run.app" -ForegroundColor Gray
    Write-Host "  Canary API:   https://ion-api-canary-64076350717.us-central1.run.app" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host ""
    
    # Summary
    $totalServices = 5
    $healthyServices = 0
    if ($prometheus.Running) { $healthyServices++ }
    if ($alertmanager.Running) { $healthyServices++ }
    if ($gatewayPort) { $healthyServices++ }
    if ($mainService.Healthy) { $healthyServices++ }
    if ($canaryService.Healthy) { $healthyServices++ }
    
    $healthPercent = [math]::Round($healthyServices / $totalServices * 100, 0)
    
    Write-Host " System Health: $healthyServices/$totalServices services operational ($healthPercent%)" -NoNewline
    if ($healthPercent -eq 100) {
        Write-Host " [EXCELLENT]" -ForegroundColor Green
    }
    elseif ($healthPercent -ge 80) {
        Write-Host " [GOOD]" -ForegroundColor Yellow
    }
    else {
        Write-Host " [DEGRADED]" -ForegroundColor Red
    }
    Write-Host ""
    
    if ($Watch) {
        Write-Host " Press Ctrl+C to exit..." -ForegroundColor DarkGray
    }
}

# Main
if ($Watch) {
    Write-Host "Starting watch mode (refresh every $RefreshSeconds seconds)..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to exit" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    while ($true) {
        Show-Dashboard
        Start-Sleep -Seconds $RefreshSeconds
    }
}
else {
    Show-Dashboard
}
