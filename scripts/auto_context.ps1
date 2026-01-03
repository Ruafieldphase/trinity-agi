<#
.SYNOPSIS
AGI Auto Context Switcher - 자동 맥락 판단 및 전환

.DESCRIPTION
시간대, Life Score, 이벤트를 기반으로 최적의 맥락을 자동 판단하여 전환합니다.
인간의 생체 리듬을 모사합니다.

.PARAMETER DryRun
실제 전환 없이 판단 결과만 출력

.PARAMETER Force
확인 없이 자동 전환

.EXAMPLE
.\auto_context.ps1
현재 상황을 분석하여 최적 맥락으로 자동 전환

.EXAMPLE
.\auto_context.ps1 -DryRun
판단만 하고 실제 전환하지 않음
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$DryRun,

    [Parameter(Mandatory=$false)]
    [switch]$Force
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$StateFile = Join-Path $WorkspaceRoot "outputs\active_context.json"
$LifeCheckFile = Join-Path $WorkspaceRoot "outputs\life_continuity_latest.json"

# UTF-8 출력 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Get-CurrentContext {
    if (Test-Path $StateFile) {
        return Get-Content $StateFile -Raw | ConvertFrom-Json
    } else {
        return @{ current = "Core"; active_since = (Get-Date).ToString("o") }
    }
}

function Get-LifeScore {
    if (Test-Path $LifeCheckFile) {
        $lifeData = Get-Content $LifeCheckFile -Raw | ConvertFrom-Json
        return $lifeData.life_score
    }
    return 50.0  # Default if file not found
}

function Get-TimeBasedContext {
    $hour = (Get-Date).Hour
    
    # 인간의 일일 리듬 모사
    switch ($hour) {
        { $_ -ge 0 -and $_ -lt 6 } { return "Sleep" }       # 00:00~06:00
        { $_ -ge 6 -and $_ -lt 9 } { return "Operations" }  # 06:00~09:00 (아침 점검)
        { $_ -ge 9 -and $_ -lt 12 } { return "Learning" }   # 09:00~12:00 (집중 학습)
        { $_ -ge 12 -and $_ -lt 13 } { return "Core" }      # 12:00~13:00 (휴식)
        { $_ -ge 13 -and $_ -lt 15 } { return "Learning" }  # 13:00~15:00 (오후 학습)
        { $_ -ge 15 -and $_ -lt 16 } { return "Operations" } # 15:00~16:00 (일일 점검)
        { $_ -ge 16 -and $_ -lt 18 } { return "Development" } # 16:00~18:00 (개발 시간)
        { $_ -ge 18 -and $_ -lt 22 } { return "Core" }      # 18:00~22:00 (자유 시간)
        { $_ -ge 22 -and $_ -lt 24 } { return "Operations" } # 22:00~24:00 (야간 준비)
        default { return "Core" }
    }
}

function Test-RecentEvent {
    param($EventType, $WindowMinutes = 30)
    
    $ledgerFile = Join-Path $WorkspaceRoot "fdo_agi_repo\memory\resonance_ledger.jsonl"
    if (-not (Test-Path $ledgerFile)) { return $false }
    
    $cutoff = (Get-Date).AddMinutes(-$WindowMinutes)
    
    $recentEvents = Get-Content $ledgerFile -Tail 100 | ForEach-Object {
        try {
            $ledgerEvent = $_ | ConvertFrom-Json
            if ($ledgerEvent.timestamp) {
                $eventTime = [datetime]$ledgerEvent.timestamp
                if ($eventTime -gt $cutoff -and $ledgerEvent.event_type -eq $EventType) {
                    return $true
                }
            }
        } catch { }
    }
    
    return ($recentEvents -contains $true)
}

function Get-OptimalContext {
    Write-Host "`n🧠 Analyzing optimal context...`n" -ForegroundColor Cyan
    
    $currentCtx = Get-CurrentContext
    $currentContext = $currentCtx.current
    $contextDuration = (Get-Date) - [datetime]$currentCtx.active_since
    
    Write-Host "Current: $currentContext (duration: $("{0:F1}" -f $contextDuration.TotalHours)h)" -ForegroundColor White
    
    # 1. Life Score 체크 (최우선)
    $lifeScore = Get-LifeScore
    Write-Host "Life Score: $("{0:F1}" -f $lifeScore)%" -ForegroundColor $(if ($lifeScore -lt 50) { "Red" } elseif ($lifeScore -lt 70) { "Yellow" } else { "Green" })
    
    if ($lifeScore -lt 30) {
        Write-Host "  → CRITICAL: Emergency Operations required" -ForegroundColor Red
        return @{ context = "Operations"; reason = "Life Score critical (<30%)" }
    }
    
    if ($lifeScore -lt 50 -and $currentContext -ne "Operations") {
        Write-Host "  → LOW: Operations recommended" -ForegroundColor Yellow
        return @{ context = "Operations"; reason = "Life Score low (<50%)" }
    }
    
    # 2. 시간 기반 (생체 리듬)
    $timeBasedContext = Get-TimeBasedContext
    $hour = (Get-Date).Hour
    Write-Host "Time-based suggestion: $timeBasedContext ($hour`:00)" -ForegroundColor Cyan
    
    # 3. 최근 이벤트 체크
    $hasYouTubeEvent = Test-RecentEvent -EventType "youtube_learn" -WindowMinutes 10
    $hasCodeChange = Test-RecentEvent -EventType "code_change" -WindowMinutes 15
    
    if ($hasYouTubeEvent) {
        Write-Host "  → Recent YouTube event detected" -ForegroundColor Green
        return @{ context = "Learning"; reason = "YouTube learning activity detected" }
    }
    
    if ($hasCodeChange) {
        Write-Host "  → Recent code change detected" -ForegroundColor Magenta
        return @{ context = "Development"; reason = "Code changes detected" }
    }
    
    # 4. 맥락 지속 시간 체크 (너무 오래 같은 맥락 = 루프 함정)
    $maxDurationHours = @{
        "Learning" = 4
        "Operations" = 2
        "Development" = 6
        "Core" = 24  # Core는 제한 없음
        "Sleep" = 8
    }
    
    $maxHours = $maxDurationHours[$currentContext]
    if ($contextDuration.TotalHours -gt $maxHours) {
        $durationText = "{0:F1}" -f $contextDuration.TotalHours
        Write-Host "  → Context duration exceeded ($durationText h > $maxHours h)" -ForegroundColor Yellow
        return @{ context = $timeBasedContext; reason = "Context duration limit exceeded" }
    }
    
    # 5. Sleep 모드 체크 (에너지 절약)
    if ($timeBasedContext -eq "Sleep" -and $lifeScore -gt 70) {
        Write-Host "  → Optimal conditions for sleep" -ForegroundColor Blue
        return @{ context = "Sleep"; reason = "Night time + good health" }
    }
    
    # 6. 기본: 시간 기반 권장
    return @{ context = $timeBasedContext; reason = "Time-based daily rhythm" }
}

function Switch-ToContext {
    param($TargetContext, $Reason)
    
    $currentCtx = Get-CurrentContext
    if ($currentCtx.current -eq $TargetContext) {
        Write-Host "`n✓ Already in optimal context: $TargetContext" -ForegroundColor Green
        return
    }
    
    Write-Host "`n📋 Recommended Action:" -ForegroundColor Cyan
    Write-Host "  Switch to: $TargetContext" -ForegroundColor Green
    Write-Host "  Reason: $Reason" -ForegroundColor White
    
    if ($DryRun) {
        Write-Host "`n🔍 DRY RUN - No action taken" -ForegroundColor Yellow
        return
    }
    
    $switchScript = Join-Path $PSScriptRoot "switch_context.ps1"
    if (Test-Path $switchScript) {
        if ($Force) {
            & $switchScript -To $TargetContext -Force
        } else {
            & $switchScript -To $TargetContext
        }
    } else {
        Write-Host "❌ switch_context.ps1 not found" -ForegroundColor Red
    }
}

# Main Logic
Write-Host "🤖 AGI Auto Context Analyzer" -ForegroundColor Cyan
Write-Host "=" * 50

$optimal = Get-OptimalContext
Switch-ToContext -TargetContext $optimal.context -Reason $optimal.reason

Write-Host "`n" + "=" * 50
Write-Host "✅ Auto context analysis complete`n" -ForegroundColor Green