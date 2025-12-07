<#
.SYNOPSIS
AGI Context Switcher - 맥락 기반 시스템 활성화/비활성화

.DESCRIPTION
인간의 뇌처럼 필요한 맥락(Context)에 따라 시스템을 선택적으로 활성화합니다.
- Core: 항상 유지 (정체성, 기억, 맥락 전환 능력)
- Learning: 학습 모드 (YouTube, BQI, RPA)
- Operations: 운영 점검 (Monitoring, Health Check)
- Development: 개발 모드 (Tests, Watchdog, Auto-Recovery)
- Sleep: 수면 모드 (최소 에너지, 백업만)

.PARAMETER To
전환할 맥락: Core, Learning, Operations, Development, Sleep

.PARAMETER Status
현재 활성 맥락 상태 출력

.PARAMETER Force
확인 없이 강제 전환

.EXAMPLE
.\switch_context.ps1 -To Learning
학습 모드로 전환

.EXAMPLE
.\switch_context.ps1 -Status
현재 맥락 확인

.EXAMPLE
.\switch_context.ps1 -To Sleep -Force
수면 모드로 강제 전환
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("Core", "Learning", "Operations", "Development", "Sleep")]
    [string]$To,

    [Parameter(Mandatory = $false)]
    [switch]$Status,

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$StateFile = Join-Path $WorkspaceRoot "outputs\active_context.json"
$LedgerFile = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\resonance_ledger.jsonl"

# UTF-8 출력 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Get-CurrentContext {
    if (Test-Path $StateFile) {
        return Get-Content $StateFile -Raw | ConvertFrom-Json
    }
    else {
        return @{
            current           = "Core"
            active_since      = (Get-Date).ToString("o")
            enabled_services  = @("ledger")
            disabled_services = @()
        }
    }
}

function Save-Context {
    param($ContextObj)
    $ContextObj | ConvertTo-Json -Depth 10 | Out-File $StateFile -Encoding UTF8 -Force
}

function Write-Ledger {
    param($EventType, $Message, $Metadata = @{})
    
    $ledgerEntry = @{
        timestamp  = (Get-Date).ToString("o")
        event_type = $EventType
        message    = $Message
        metadata   = $Metadata
    }
    
    $ledgerEntry | ConvertTo-Json -Compress | Out-File $LedgerFile -Append -Encoding UTF8 -Force
}

function Show-Status {
    $ctx = Get-CurrentContext
    $duration = (Get-Date) - [datetime]$ctx.active_since
    
    Write-Host "`n🧠 AGI Context Status`n" -ForegroundColor Cyan
    Write-Host "Current Context: " -NoNewline
    
    switch ($ctx.current) {
        "Core" { Write-Host "🧠 Core (Always On)" -ForegroundColor White }
        "Learning" { Write-Host "📚 Learning" -ForegroundColor Green }
        "Operations" { Write-Host "🔧 Operations" -ForegroundColor Yellow }
        "Development" { Write-Host "💻 Development" -ForegroundColor Magenta }
        "Sleep" { Write-Host "😴 Sleep" -ForegroundColor Blue }
    }
    
    Write-Host "Active Since: $($ctx.active_since)"
    Write-Host "Duration: $([Math]::Floor($duration.TotalHours))h $($duration.Minutes)m"
    Write-Host "`nEnabled Services:"
    foreach ($svc in $ctx.enabled_services) {
        Write-Host "  ✓ $svc" -ForegroundColor Green
    }
    
    if ($ctx.disabled_services.Count -gt 0) {
        Write-Host "`nDisabled Services:"
        foreach ($svc in $ctx.disabled_services) {
            Write-Host "  ✗ $svc" -ForegroundColor DarkGray
        }
    }
    
    Write-Host ""
}

function Stop-ContextServices {
    param($Context)
    
    Write-Host "🛑 Stopping $Context services..." -ForegroundColor Yellow
    
    switch ($Context) {
        "Learning" {
            # Stop Task Queue Server
            Get-Process -Name python, pwsh, powershell -ErrorAction SilentlyContinue | 
            Where-Object { $_.CommandLine -like '*task_queue_server*' -or 
                $_.CommandLine -like '*youtube_worker*' -or 
                $_.CommandLine -like '*rpa_worker*' } | 
            Stop-Process -Force -ErrorAction SilentlyContinue
            
            Write-Host "  ✓ Stopped workers" -ForegroundColor Green
        }
        
        "Operations" {
            # Stop Metrics Collector
            Get-Process -Name pwsh, powershell -ErrorAction SilentlyContinue | 
            Where-Object { $_.CommandLine -like '*metrics_collector*' } | 
            Stop-Process -Force -ErrorAction SilentlyContinue
            
            Write-Host "  ✓ Stopped metrics collector" -ForegroundColor Green
        }
        
        "Development" {
            # Stop Watchdog, Auto-Recover
            Get-Process -Name python, pwsh, powershell -ErrorAction SilentlyContinue | 
            Where-Object { $_.CommandLine -like '*task_watchdog*' -or 
                $_.CommandLine -like '*auto_recover*' } | 
            Stop-Process -Force -ErrorAction SilentlyContinue
            
            Write-Host "  ✓ Stopped dev tools" -ForegroundColor Green
        }
        
        "Sleep" {
            # Stop almost everything except Core
            Get-Process -Name python, pwsh, powershell -ErrorAction SilentlyContinue | 
            Where-Object { $_.CommandLine -like '*task_queue*' -or 
                $_.CommandLine -like '*worker*' -or 
                $_.CommandLine -like '*metrics*' -or
                $_.CommandLine -like '*watchdog*' } | 
            Stop-Process -Force -ErrorAction SilentlyContinue
            
            Write-Host "  ✓ Stopped all non-essential services" -ForegroundColor Green
        }
    }
    
    Start-Sleep -Seconds 2
}

function Start-ContextServices {
    param($Context)
    
    Write-Host "🚀 Starting $Context services..." -ForegroundColor Green
    
    $enabledServices = @()
    
    switch ($Context) {
        "Core" {
            # Core는 항상 유지 (프로세스 없음, on-demand만)
            $enabledServices = @("ledger", "health_gate_minimal")
            Write-Host "  ✓ Core services ready (on-demand)" -ForegroundColor Green
        }
        
        "Learning" {
            # Start Task Queue Server
            $serverScript = Join-Path $WorkspaceRoot "LLM_Unified\ion-mentoring\start_task_queue_server_background.ps1"
            if (Test-Path $serverScript) {
                & $serverScript
                $enabledServices += "task_queue_server"
            }
            
            # Workers는 필요 시 수동 시작 (자동 시작하면 idle 에너지 소비)
            $enabledServices += @("youtube_worker_ready", "rpa_worker_ready", "bqi_learner_ready")
            
            # Metrics (경량 모드)
            $metricsScript = Join-Path $WorkspaceRoot "scripts\start_metrics_collector_daemon.ps1"
            if (Test-Path $metricsScript) {
                & $metricsScript -IntervalSeconds 1800  # 30분 간격
                $enabledServices += "metrics_collector_light"
            }
            
            Write-Host "  ✓ Learning context activated" -ForegroundColor Green
            Write-Host "  ℹ Workers ready (start on-demand)" -ForegroundColor Cyan
        }
        
        "Operations" {
            # Start Metrics Collector (상세 모드)
            $metricsScript = Join-Path $WorkspaceRoot "scripts\start_metrics_collector_daemon.ps1"
            if (Test-Path $metricsScript) {
                & $metricsScript -IntervalSeconds 300  # 5분 간격
                $enabledServices += "metrics_collector_detailed"
            }
            
            # 나머지는 on-demand (보고서 생성 등)
            $enabledServices += @("monitoring_report_ready", "performance_dashboard_ready", "health_check_ready")
            
            Write-Host "  ✓ Operations context activated" -ForegroundColor Green
        }
        
        "Development" {
            # Start Task Queue Server (for testing)
            $serverScript = Join-Path $WorkspaceRoot "LLM_Unified\ion-mentoring\start_task_queue_server_background.ps1"
            if (Test-Path $serverScript) {
                & $serverScript
                $enabledServices += "task_queue_server"
            }
            
            # Watchdog, Auto-Recover는 선택적 (필요 시 수동 시작)
            $enabledServices += @("watchdog_ready", "auto_recover_ready", "tests_ready")
            
            Write-Host "  ✓ Development context activated" -ForegroundColor Green
        }
        
        "Sleep" {
            # Information-theoretic sleep: active reconstruction, not shutdown
            $enabledServices = @("ledger_append_only", "backup_scheduled")
            
            # Start Dream Mode (pattern exploration)
            $dreamScript = Join-Path $WorkspaceRoot "scripts\run_dream_mode.ps1"
            if (Test-Path $dreamScript) {
                Start-Job -ScriptBlock {
                    param($script)
                    & $script -Hours 24 -Iterations 20
                } -ArgumentList $dreamScript -Name "AGI_DreamMode" | Out-Null
                $enabledServices += "dream_mode_active"
                Write-Host "  💭 Dream Mode started (pattern exploration)" -ForegroundColor Magenta
            }
            
            # Start Unconscious Processor (background narratives)
            $venvPython = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
            $unconsciousScript = Join-Path $WorkspaceRoot "scripts\unconscious_processor.py"
            if ((Test-Path $venvPython) -and (Test-Path $unconsciousScript)) {
                Start-Job -ScriptBlock {
                    param($python, $script)
                    & $python $script
                } -ArgumentList $venvPython, $unconsciousScript -Name "AGI_Unconscious" | Out-Null
                $enabledServices += "unconscious_processor_active"
                Write-Host "  🌊 Unconscious Processor started (uncontrollable)" -ForegroundColor Blue
            }
            
            Write-Host "  ✓ Sleep mode activated (information-theoretic rest)" -ForegroundColor Blue
            Write-Host "  💤 Active: Dream Mode, Unconscious, Backup" -ForegroundColor DarkGray
            Write-Host "  💤 Wake triggers: 06:00, external event, Life Score < 30%" -ForegroundColor DarkGray
        }
    }
    
    return $enabledServices
}

function Switch-Context {
    param($NewContext)
    
    $currentCtx = Get-CurrentContext
    $currentContext = $currentCtx.current
    
    if ($currentContext -eq $NewContext) {
        Write-Host "`n✓ Already in $NewContext context" -ForegroundColor Green
        Show-Status
        return
    }
    
    if (-not $Force) {
        Write-Host "`n⚠️  Context Switch: $currentContext → $NewContext" -ForegroundColor Yellow
        Write-Host "This will stop current services and start new ones."
        $confirm = Read-Host "Continue? (y/N)"
        if ($confirm -ne 'y' -and $confirm -ne 'Y') {
            Write-Host "Cancelled." -ForegroundColor Red
            return
        }
    }
    
    Write-Host "`n🔄 Switching context: $currentContext → $NewContext`n" -ForegroundColor Cyan
    
    # 1. Ledger 기록
    Write-Ledger -EventType "context_switch" -Message "Context switching: $currentContext → $NewContext" -Metadata @{
        from      = $currentContext
        to        = $NewContext
        timestamp = (Get-Date).ToString("o")
    }
    
    # 2. 기존 맥락 서비스 정지
    if ($currentContext -ne "Core") {
        Stop-ContextServices -Context $currentContext
    }
    
    # 3. 새 맥락 서비스 시작
    $enabledServices = Start-ContextServices -Context $NewContext
    
    # 4. 상태 저장
    $newCtx = @{
        current           = $NewContext
        previous          = $currentContext
        active_since      = (Get-Date).ToString("o")
        enabled_services  = $enabledServices
        disabled_services = @()  # 나중에 추가 가능
        auto_switch_rules = @{
            "00:00-06:00"          = "Sleep"
            "life_score_below_50"  = "Operations"
            "youtube_url_detected" = "Learning"
            "code_change_detected" = "Development"
        }
    }
    
    Save-Context -ContextObj $newCtx
    
    Write-Host "`n✅ Context switched successfully!`n" -ForegroundColor Green
    
    # 5. 새 상태 출력
    Show-Status
    
    # 6. Life Check (선택적)
    $healthScript = Join-Path $WorkspaceRoot "scripts\check_life_continuity.ps1"
    if (Test-Path $healthScript) {
        Write-Host "🔬 Quick Life Check..." -ForegroundColor Cyan
        & $healthScript -OutFile (Join-Path $WorkspaceRoot "outputs\life_continuity_latest.json")
    }

    # 7. Context Anchor 업데이트 (새 세션 진입점 통합)
    $anchorScript = Join-Path $WorkspaceRoot "scripts\generate_context_anchor.py"
    if (Test-Path $anchorScript) {
        try {
            Write-Host "Updating context anchor (context_anchor_latest.md)..." -ForegroundColor Cyan
            & python $anchorScript
        }
        catch {
            Write-Host "Warning: failed to update context anchor: $_" -ForegroundColor Yellow
        }
    }
}

# Main Logic
if ($Status) {
    Show-Status
    exit 0
}

if (-not $To) {
    Write-Host "❌ Error: -To parameter required (or use -Status)" -ForegroundColor Red
    Write-Host "Usage: .\switch_context.ps1 -To [Core|Learning|Operations|Development|Sleep]"
    Write-Host "   or: .\switch_context.ps1 -Status"
    exit 1
}

Switch-Context -NewContext $To
