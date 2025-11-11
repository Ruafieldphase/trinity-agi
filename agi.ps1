<#
.SYNOPSIS
AGI 통합 제어 CLI

.DESCRIPTION
하나의 명령으로 모든 AGI 시스템을 제어합니다.

.EXAMPLE
.\agi.ps1 start     # 모든 시스템 시작
.\agi.ps1 stop      # 모든 시스템 중지
.\agi.ps1 status    # 상태 확인
.\agi.ps1 restart   # 재시작
.\agi.ps1 logs      # 로그 보기
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'logs', 'install', 'uninstall', 'migrate', 'cleanup')]
    [string]$Command = 'status',
    
    [switch]$Follow,  # logs 명령에서 tail -f 처럼 사용
    [switch]$Force    # cleanup/migrate 명령에서 확인 없이 진행
)

$ErrorActionPreference = "Stop"
$MasterDaemonScript = "$PSScriptRoot\scripts\master_daemon.ps1"

function Show-Banner {
    Write-Host @"

    ╔═══════════════════════════════════╗
    ║   AGI 통합 제어 시스템            ║
    ║   Master Control Interface        ║
    ╚═══════════════════════════════════╝

"@ -ForegroundColor Cyan
}

function Invoke-MasterCommand {
    param([string]$Cmd)
    
    $params = @{
        FilePath     = "powershell.exe"
        ArgumentList = @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", $MasterDaemonScript,
            "-$Cmd"
        )
        NoNewWindow  = $true
        Wait         = $true
    }
    
    Start-Process @params
}

Show-Banner

switch ($Command) {
    'start' {
        Write-Host "🚀 Starting AGI Master Daemon..." -ForegroundColor Yellow
        Invoke-MasterCommand -Cmd "Start"
    }
    
    'stop' {
        Write-Host "🛑 Stopping AGI Master Daemon..." -ForegroundColor Yellow
        Invoke-MasterCommand -Cmd "Stop"
    }
    
    'restart' {
        Write-Host "🔄 Restarting AGI Master Daemon..." -ForegroundColor Yellow
        Invoke-MasterCommand -Cmd "Restart"
    }
    
    'status' {
        Invoke-MasterCommand -Cmd "Status"
    }
    
    'logs' {
        $logPath = "C:\workspace\agi\outputs\master_daemon.log"
        
        if (!(Test-Path $logPath)) {
            Write-Host "✗ Log file not found: $logPath" -ForegroundColor Red
            return
        }
        
        if ($Follow) {
            Write-Host "📜 Following logs (Ctrl+C to stop)..." -ForegroundColor Cyan
            Get-Content $logPath -Tail 50 -Wait
        }
        else {
            Write-Host "📜 Last 50 log entries:" -ForegroundColor Cyan
            Get-Content $logPath -Tail 50
        }
    }
    
    'install' {
        Write-Host "📦 Installing AGI Master Daemon..." -ForegroundColor Yellow
        
        # 관리자 권한 확인
        $isAdmin = ([Security.Principal.WindowsPrincipal] `
                [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(`
                [Security.Principal.WindowsBuiltInRole]::Administrator)
        
        if (-not $isAdmin) {
            Write-Host "⚠ Elevating to Administrator..." -ForegroundColor Yellow
            $runAsAdminScript = "$PSScriptRoot\scripts\run_as_admin.ps1"
            & $runAsAdminScript $MasterDaemonScript "-Install"
        }
        else {
            Invoke-MasterCommand -Cmd "Install"
        }
        
        Write-Host "`n✓ Installation complete!" -ForegroundColor Green
        Write-Host "  The daemon will start automatically on next logon." -ForegroundColor Cyan
    }
    
    'uninstall' {
        Write-Host "🗑️  Uninstalling AGI Master Daemon..." -ForegroundColor Yellow
        Invoke-MasterCommand -Cmd "Uninstall"
        Write-Host "`n✓ Uninstallation complete!" -ForegroundColor Green
    }
    
    'cleanup' {
        Write-Host "🧹 Cleaning up old AGI tasks..." -ForegroundColor Yellow
        
        $cleanupScript = "$PSScriptRoot\scripts\cleanup_old_tasks_admin.ps1"
        $runAsAdminScript = "$PSScriptRoot\scripts\run_as_admin.ps1"
        
        if (!(Test-Path $cleanupScript)) {
            Write-Host "✗ Cleanup script not found: $cleanupScript" -ForegroundColor Red
            return
        }
        
        $args = @($cleanupScript)
        if ($Force) { $args += "-Force" }
        
        & $runAsAdminScript @args
        Write-Host "`n✓ Cleanup complete!" -ForegroundColor Green
    }
    
    'migrate' {
        Write-Host "🔄 Migrating to Master Daemon..." -ForegroundColor Yellow
        
        # 1단계: 정리
        Write-Host "`n[1/2] Cleaning old tasks..." -ForegroundColor Cyan
        & $PSScriptRoot\agi.ps1 cleanup -Force
        
        # 2단계: 설치
        Write-Host "`n[2/2] Installing Master Daemon..." -ForegroundColor Cyan
        & $PSScriptRoot\agi.ps1 install
        
        Write-Host "`n✅ Migration complete!" -ForegroundColor Green
        Write-Host "`nNext steps:" -ForegroundColor Cyan
        Write-Host "  .\agi.ps1 start     # Start the system" -ForegroundColor Gray
        Write-Host "  .\agi.ps1 status    # Check status`n" -ForegroundColor Gray
    }
}

Write-Host ""
