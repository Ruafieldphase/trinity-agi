#Requires -Version 5.1
<#
.SYNOPSIS
    깃코 봇의 최근 로그를 표시합니다.

.DESCRIPTION
    봇과 터널 로그를 tail 형태로 표시하거나 실시간으로 팔로우합니다.

.PARAMETER Lines
    표시할 로그 라인 수 (기본값: 50)

.PARAMETER Follow
    실시간으로 로그를 팔로우합니다.

.PARAMETER Type
    표시할 로그 타입: bot, tunnel, all (기본값: all)

.EXAMPLE
    .\show_bot_logs.ps1
    # 최근 50줄 표시

.EXAMPLE
    .\show_bot_logs.ps1 -Lines 100 -Follow
    # 100줄 표시 후 실시간 팔로우

.EXAMPLE
    .\show_bot_logs.ps1 -Type bot
    # 봇 로그만 표시
#>

[CmdletBinding()]
param(
    [int]$Lines = 50,
    [switch]$Follow,
    [ValidateSet("bot", "tunnel", "all")]
    [string]$Type = "all"
)

$ErrorActionPreference = "Stop"

$WORKSPACE_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$OUTPUTS_DIR = Join-Path $WORKSPACE_ROOT "LLM_Unified\ion-mentoring\outputs"
$LOG_DIR = Join-Path $OUTPUTS_DIR "logs"

if (-not (Test-Path $LOG_DIR)) {
    Write-Host "❌ 로그 디렉토리가 없습니다: $LOG_DIR" -ForegroundColor Red
    exit 1
}

function Get-LatestLog {
    param([string]$Pattern)
    Get-ChildItem -Path $LOG_DIR -Filter $Pattern | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1
}

function Show-Log {
    param(
        [string]$LogPath,
        [string]$Title,
        [int]$Lines
    )
    
    if (-not (Test-Path $LogPath)) {
        Write-Host "⚠️  $Title 로그를 찾을 수 없습니다." -ForegroundColor Yellow
        return
    }
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host " 📄 $Title" -ForegroundColor Green
    Write-Host " 파일: $(Split-Path -Leaf $LogPath)" -ForegroundColor Gray
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
    
    Get-Content $LogPath -Tail $Lines | ForEach-Object {
        if ($_ -match "\[ERROR\]") {
            Write-Host $_ -ForegroundColor Red
        }
        elseif ($_ -match "\[WARN\]") {
            Write-Host $_ -ForegroundColor Yellow
        }
        elseif ($_ -match "\[INFO\]") {
            Write-Host $_ -ForegroundColor White
        }
        elseif ($_ -match "✅|🎉|✨") {
            Write-Host $_ -ForegroundColor Green
        }
        elseif ($_ -match "🌐|🚀") {
            Write-Host $_ -ForegroundColor Cyan
        }
        else {
            Write-Host $_ -ForegroundColor Gray
        }
    }
}

# 최신 로그 파일 찾기
$botLog = Get-LatestLog "gitco_bot_*.log"
$tunnelLog = Get-LatestLog "localtunnel_*.log"

if ($Type -eq "all" -or $Type -eq "bot") {
    if ($botLog) {
        Show-Log -LogPath $botLog.FullName -Title "깃코 봇 로그" -Lines $Lines
    }
}

if ($Type -eq "all" -or $Type -eq "tunnel") {
    if ($tunnelLog) {
        Show-Log -LogPath $tunnelLog.FullName -Title "Localtunnel 로그" -Lines $Lines
    }
}

if ($Follow) {
    Write-Host ""
    Write-Host "👁️  실시간 로그 팔로우 중... (Ctrl+C로 종료)" -ForegroundColor Yellow
    Write-Host ""
    
    $logs = @()
    if ($Type -eq "all" -or $Type -eq "bot") {
        if ($botLog) { $logs += $botLog.FullName }
    }
    if ($Type -eq "all" -or $Type -eq "tunnel") {
        if ($tunnelLog) { $logs += $tunnelLog.FullName }
    }
    
    if ($logs.Count -gt 0) {
        Get-Content $logs -Wait -Tail 0 | ForEach-Object {
            $line = $_
            if ($line -match "\[ERROR\]") {
                Write-Host $line -ForegroundColor Red
            }
            elseif ($line -match "\[WARN\]") {
                Write-Host $line -ForegroundColor Yellow
            }
            elseif ($line -match "✅|🎉") {
                Write-Host $line -ForegroundColor Green
            }
            else {
                Write-Host $line -ForegroundColor White
            }
        }
    }
}
