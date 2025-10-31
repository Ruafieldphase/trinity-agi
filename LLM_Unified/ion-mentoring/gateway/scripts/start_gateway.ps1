<# 
.SYNOPSIS
    Lumen Gateway Auto-Start Script
    
.DESCRIPTION
    Automatically starts Gateway Collector and Exporter processes
    with health checks and process management.
    
.PARAMETER KillExisting
    Kill existing Collector/Exporter processes before starting
    
.PARAMETER SkipCollector
    Start only the Exporter (skip Collector)
    
.PARAMETER SkipExporter
    Start only the Collector (skip Exporter)
    
.PARAMETER CollectInterval
    Metrics collection interval in seconds (default: 20)
    
.PARAMETER ExporterPort
    Prometheus exporter port (default: 9108)
    
.EXAMPLE
    .\start_gateway.ps1
    Start both Collector and Exporter with defaults
    
.EXAMPLE
    .\start_gateway.ps1 -KillExisting
    Kill existing processes and restart
    
.EXAMPLE
    .\start_gateway.ps1 -CollectInterval 30 -ExporterPort 9109
    Start with custom intervals and port
#>

param(
    [switch]$KillExisting,
    [switch]$SkipCollector,
    [switch]$SkipExporter,
    [int]$CollectInterval = 20,
    [int]$ExporterPort = 9108
)

$ErrorActionPreference = "Stop"

# Gateway root directory
$GatewayRoot = Split-Path -Parent $PSScriptRoot
$ScriptsDir = Join-Path $GatewayRoot "scripts"
$LogsDir = Join-Path $GatewayRoot "logs"

# Python executable (venv)
$RepoRoot = Split-Path -Parent (Split-Path -Parent $GatewayRoot)
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"

# Scripts
$CollectorScript = Join-Path $ScriptsDir "ion_metrics_collector.py"
$ExporterScript = Join-Path $ScriptsDir "gateway_health_exporter.py"

Write-Host "`n========================================" -ForegroundColor Green
Write-Host " Lumen Gateway Auto-Start" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

# Validate Python executable
if (-not (Test-Path $PythonExe)) {
    Write-Host "[ERROR] Python executable not found: $PythonExe" -ForegroundColor Red
    Write-Host "   Please ensure virtual environment is set up" -ForegroundColor Yellow
    exit 1
}

# Validate scripts
if (-not (Test-Path $CollectorScript)) {
    Write-Host "[ERROR] Collector script not found: $CollectorScript" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ExporterScript)) {
    Write-Host "[ERROR] Exporter script not found: $ExporterScript" -ForegroundColor Red
    exit 1
}

# Function: Kill existing processes
function Stop-GatewayProcesses {
    Write-Host "🔪 Stopping existing Gateway processes..." -ForegroundColor Yellow
    
    # Stop by port (Exporter)
    $portProcesses = Get-NetTCPConnection -LocalPort $ExporterPort -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique
    
    if ($portProcesses) {
        foreach ($procId in $portProcesses) {
            try {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "   Stopping process on port $ExporterPort (PID: $procId)" -ForegroundColor Gray
                    Stop-Process -Id $procId -Force
                    Start-Sleep -Milliseconds 500
                }
            }
            catch {
                # Process may have already exited
            }
        }
    }
    
    # Stop by script name (Collector)
    $pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue
    foreach ($proc in $pythonProcesses) {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
        if ($cmdLine -like "*ion_metrics_collector.py*") {
            Write-Host "   Stopping Collector (PID: $($proc.Id))" -ForegroundColor Gray
            Stop-Process -Id $proc.Id -Force
            Start-Sleep -Milliseconds 500
        }
    }
    
    Write-Host "[OK] Existing processes stopped`n" -ForegroundColor Green
}

# Function: Check if process is running
function Test-ProcessRunning {
    param([string]$ScriptName)
    
    $pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue
    foreach ($proc in $pythonProcesses) {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
        if ($cmdLine -like "*$ScriptName*") {
            return $proc.Id
        }
    }
    return $null
}

# Function: Check if port is listening
function Test-PortListening {
    param([int]$Port)
    
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return ($null -ne $connection)
}

# Kill existing if requested
if ($KillExisting) {
    Stop-GatewayProcesses
}

# Start Collector
if (-not $SkipCollector) {
    Write-Host "[DEPLOY] Starting Metrics Collector..." -ForegroundColor Cyan
    Write-Host "   Interval: $CollectInterval seconds" -ForegroundColor Gray
    
    # Check if already running
    $collectorPid = Test-ProcessRunning "ion_metrics_collector.py"
    if ($collectorPid) {
        Write-Host "[WARN]  Collector already running (PID: $collectorPid)" -ForegroundColor Yellow
        Write-Host "   Use -KillExisting to restart`n" -ForegroundColor Gray
    }
    else {
        # Set environment variable
        $env:LUMEN_COLLECT_INTERVAL = $CollectInterval
        
        # Start process
        $collectorProc = Start-Process -FilePath $PythonExe -ArgumentList $CollectorScript `
            -WindowStyle Hidden -PassThru
        
        Start-Sleep -Seconds 2
        
        # Verify it's running
        if ($collectorProc.HasExited) {
            Write-Host "[ERROR] Collector failed to start" -ForegroundColor Red
            exit 1
        }
        else {
            Write-Host "[OK] Collector started (PID: $($collectorProc.Id))`n" -ForegroundColor Green
        }
    }
}

# Start Exporter
if (-not $SkipExporter) {
    Write-Host "[DEPLOY] Starting Health Exporter..." -ForegroundColor Cyan
    Write-Host "   Port: $ExporterPort" -ForegroundColor Gray
    
    # Check if port already in use
    if (Test-PortListening $ExporterPort) {
        Write-Host "[WARN]  Port $ExporterPort already in use" -ForegroundColor Yellow
        Write-Host "   Use -KillExisting to restart`n" -ForegroundColor Gray
    }
    else {
        # Set environment variable
        $env:LUMEN_EXPORTER_PORT = $ExporterPort
        
        # Start process
        $exporterProc = Start-Process -FilePath $PythonExe -ArgumentList $ExporterScript `
            -WindowStyle Hidden -PassThru
        
        Start-Sleep -Seconds 2
        
        # Verify port is listening
        if (Test-PortListening $ExporterPort) {
            Write-Host "[OK] Exporter started on port $ExporterPort (PID: $($exporterProc.Id))`n" -ForegroundColor Green
        }
        else {
            Write-Host "[ERROR] Exporter failed to bind to port $ExporterPort" -ForegroundColor Red
            exit 1
        }
    }
}

# Final status check
Write-Host "========================================" -ForegroundColor Green
Write-Host " Gateway Status Check" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

if (-not $SkipCollector) {
    $collectorRunning = Test-ProcessRunning "ion_metrics_collector.py"
    if ($collectorRunning) {
        Write-Host "🟢 Collector: Running (PID: $collectorRunning)" -ForegroundColor Green
    }
    else {
        Write-Host "🔴 Collector: Not running" -ForegroundColor Red
    }
}

if (-not $SkipExporter) {
    if (Test-PortListening $ExporterPort) {
        Write-Host "🟢 Exporter: Listening on port $ExporterPort" -ForegroundColor Green
    }
    else {
        Write-Host "🔴 Exporter: Port $ExporterPort not listening" -ForegroundColor Red
    }
}

# Test Prometheus endpoint
if (-not $SkipExporter) {
    Write-Host "`nTesting Prometheus endpoint..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$ExporterPort/metrics" -TimeoutSec 5
        if ($response -match "lumen_gateway_status") {
            Write-Host "[OK] Prometheus endpoint responding`n" -ForegroundColor Green
        }
        else {
            Write-Host "[WARN]  Prometheus endpoint up but no metrics" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "[ERROR] Prometheus endpoint not responding" -ForegroundColor Red
    }
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "[OK] Gateway startup complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "[METRICS] Next steps:" -ForegroundColor Magenta
Write-Host "  1. Check metrics CSV: $(Join-Path $LogsDir 'metrics.csv')"
Write-Host "  2. View Prometheus metrics: http://localhost:$ExporterPort/metrics"
Write-Host "  3. Tail logs: Get-Content $(Join-Path $LogsDir 'gateway_sync.log') -Wait`n"
