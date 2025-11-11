<#
.SYNOPSIS
AGI Core System Manager - 중추신경계 (생명 유지)

.DESCRIPTION
생명 유지에 필수적인 Core 시스템을 관리합니다.
- Task Queue Server (심장)
- System Watchdog (뇌간)

이 시스템들은 항상 실행되어야 하며, 중단시 AGI 시스템이 작동 불가능합니다.
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'status', 'health')]
    [string]$Command = 'status'
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path $PSScriptRoot -Parent
$ConfigPath = Join-Path $WorkspaceRoot "config\core_system_config.json"
$LogPath = Join-Path $WorkspaceRoot "outputs\core_system.log"

function Write-CoreLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogPath -Value $entry
    
    $color = switch ($Level) {
        "SUCCESS" { "Green" }
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        default { "Cyan" }
    }
    Write-Host $entry -ForegroundColor $color
}

function Start-CoreComponent {
    param(
        [string]$Name,
        [hashtable]$Config
    )
    
    Write-CoreLog "Starting $Name ($($Config.role))..." "INFO"
    
    $workDir = Join-Path $WorkspaceRoot $Config.working_dir
    $scriptPath = Join-Path $WorkspaceRoot $Config.script
    
    if (!(Test-Path $scriptPath)) {
        Write-CoreLog "Script not found: $scriptPath" "ERROR"
        return $false
    }
    
    try {
        # Python 스크립트
        if ($scriptPath -like "*.py") {
            $venvPython = Join-Path $workDir ".venv\Scripts\python.exe"
            if (!(Test-Path $venvPython)) {
                $venvPython = "python"
            }
            
            $allArgs = @($scriptPath) + $Config.args
            $process = Start-Process -FilePath $venvPython `
                -ArgumentList $allArgs `
                -WorkingDirectory $workDir `
                -WindowStyle Hidden `
                -PassThru
        }
        # PowerShell 스크립트
        else {
            $allArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $scriptPath) + $Config.args
            $process = Start-Process -FilePath "powershell.exe" `
                -ArgumentList $allArgs `
                -WorkingDirectory $workDir `
                -WindowStyle Hidden `
                -PassThru
        }
        
        Start-Sleep -Seconds 2
        
        if (!$process.HasExited) {
            Write-CoreLog "$Name started (PID: $($process.Id))" "SUCCESS"
            return $true
        }
        else {
            Write-CoreLog "$Name failed to start" "ERROR"
            return $false
        }
    }
    catch {
        Write-CoreLog "Failed to start $Name : $_" "ERROR"
        return $false
    }
}

function Get-CoreComponentStatus {
    param(
        [string]$Name,
        [hashtable]$Config
    )
    
    $scriptName = Split-Path $Config.script -Leaf
    
    if ($scriptName -like "*.py") {
        $proc = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*$scriptName*" } |
        Select-Object -First 1
    }
    else {
        $proc = Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*$scriptName*" } |
        Select-Object -First 1
    }
    
    if ($proc) {
        $process = Get-Process -Id $proc.ProcessId -ErrorAction SilentlyContinue
        if ($process) {
            $runtime = (Get-Date) - $process.StartTime
            return @{
                Running = $true
                PID     = $process.Id
                Runtime = $runtime.ToString('hh\:mm\:ss')
                CPU     = [math]::Round($process.CPU, 2)
                Memory  = [math]::Round($process.WorkingSet64 / 1MB, 2)
            }
        }
    }
    
    return @{ Running = $false }
}

function Stop-CoreComponent {
    param(
        [string]$Name,
        [hashtable]$Config
    )
    
    Write-CoreLog "Stopping $Name..." "WARNING"
    
    $status = Get-CoreComponentStatus -Name $Name -Config $Config
    if ($status.Running) {
        Stop-Process -Id $status.PID -Force -ErrorAction SilentlyContinue
        Write-CoreLog "$Name stopped (PID: $($status.PID))" "SUCCESS"
    }
    else {
        Write-CoreLog "$Name was not running" "INFO"
    }
}

# Main
if (!(Test-Path $ConfigPath)) {
    Write-Host "Config not found: $ConfigPath" -ForegroundColor Red
    exit 1
}

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

switch ($Command) {
    'start' {
        Write-Host "`n💓 Starting Core System (중추신경계)..." -ForegroundColor Yellow
        Write-Host "   Essential for life - Do not stop unless necessary`n" -ForegroundColor Red
        
        $allStarted = $true
        foreach ($component in $config.components.PSObject.Properties) {
            $name = $component.Name
            $cfg = @{}
            $component.Value.PSObject.Properties | ForEach-Object { $cfg[$_.Name] = $_.Value }
            
            if ($cfg.enabled) {
                $started = Start-CoreComponent -Name $name -Config $cfg
                if (!$started -and $cfg.critical) {
                    $allStarted = $false
                }
            }
        }
        
        if ($allStarted) {
            Write-Host "`n✓ Core System is ALIVE" -ForegroundColor Green
        }
        else {
            Write-Host "`n⚠ Core System started with warnings" -ForegroundColor Yellow
        }
    }
    
    'stop' {
        Write-Host "`n⚠ STOPPING Core System (중추신경계)..." -ForegroundColor Red
        Write-Host "   This will cause system death - Are you sure? (Ctrl+C to cancel)`n" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        
        foreach ($component in $config.components.PSObject.Properties) {
            $name = $component.Name
            $cfg = @{}
            $component.Value.PSObject.Properties | ForEach-Object { $cfg[$_.Name] = $_.Value }
            
            Stop-CoreComponent -Name $name -Config $cfg
        }
        
        Write-Host "`n✗ Core System is DEAD" -ForegroundColor Red
    }
    
    'status' {
        Write-Host "`n=== Core System Status (중추신경계) ===" -ForegroundColor Cyan
        
        $allHealthy = $true
        foreach ($component in $config.components.PSObject.Properties) {
            $name = $component.Name
            $cfg = @{}
            $component.Value.PSObject.Properties | ForEach-Object { $cfg[$_.Name] = $_.Value }
            
            $status = Get-CoreComponentStatus -Name $name -Config $cfg
            
            Write-Host "`n$name ($($cfg.role)):" -ForegroundColor White
            if ($status.Running) {
                Write-Host "  ✓ ALIVE" -ForegroundColor Green -NoNewline
                Write-Host " (PID: $($status.PID), Runtime: $($status.Runtime))" -ForegroundColor Gray
                Write-Host "  CPU: $($status.CPU)s, Memory: $($status.Memory) MB" -ForegroundColor Gray
            }
            else {
                Write-Host "  ✗ DEAD" -ForegroundColor Red
                if ($cfg.critical) {
                    $allHealthy = $false
                }
            }
        }
        
        Write-Host "`n=== Overall Status ===" -ForegroundColor Cyan
        if ($allHealthy) {
            Write-Host "💓 Core System is HEALTHY" -ForegroundColor Green
        }
        else {
            Write-Host "💀 Core System is CRITICAL" -ForegroundColor Red
            Write-Host "   Immediate attention required!" -ForegroundColor Yellow
        }
    }
    
    'health' {
        # JSON 형식으로 상태 반환 (다른 스크립트에서 사용)
        $result = @{
            timestamp  = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
            healthy    = $true
            components = @{}
        }
        
        foreach ($component in $config.components.PSObject.Properties) {
            $name = $component.Name
            $cfg = @{}
            $component.Value.PSObject.Properties | ForEach-Object { $cfg[$_.Name] = $_.Value }
            
            $status = Get-CoreComponentStatus -Name $name -Config $cfg
            $result.components[$name] = $status
            
            if (!$status.Running -and $cfg.critical) {
                $result.healthy = $false
            }
        }
        
        $result | ConvertTo-Json -Depth 10
    }
}

Write-Host ""
