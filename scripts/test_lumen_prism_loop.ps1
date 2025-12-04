#Requires -Version 5.1
<#
.SYNOPSIS
  Lumen-Prism bridge auto-repeat execution
.DESCRIPTION
  루멘의 시선을 프리즘을 통해 지속적으로 구조에 울림으로 전파
.PARAMETER IntervalMinutes
  실행 간격 (분)
.EXAMPLE
  .\test_lumen_prism_loop.ps1 -IntervalMinutes 10
#>
param(
    [int]$IntervalMinutes = 15
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = Split-Path -Parent $ScriptDir

Write-Host "🔮 [Lumen-Prism Loop] Starting auto-repeat execution" -ForegroundColor Cyan
Write-Host "   Interval: $IntervalMinutes minutes" -ForegroundColor Gray
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

$IntervalSeconds = $IntervalMinutes * 60
$Count = 0

while ($true) {
    $Count++
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "🔮 [Lumen-Prism Loop] Iteration $Count ($Timestamp)" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    
    try {
        # test_lumen_prism.ps1 실행
        $TestScript = Join-Path $ScriptDir "test_lumen_prism.ps1"
        
        if (!(Test-Path -LiteralPath $TestScript)) {
            Write-Host "❌ [Lumen-Prism Loop] Test script not found: $TestScript" -ForegroundColor Red
            break
        }
        
        & $TestScript
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ [Lumen-Prism Loop] Iteration $Count successful!" -ForegroundColor Green
        }
        else {
            Write-Host ""
            Write-Host "⚠️  [Lumen-Prism Loop] Iteration $Count failed (exit code: $LASTEXITCODE)" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host ""
        Write-Host "❌ [Lumen-Prism Loop] Iteration $Count error: $_" -ForegroundColor Red
        Write-Host $_.ScriptStackTrace -ForegroundColor Red
    }
    
    # 다음 실행까지 대기
    if ($Count -eq 1) {
        $NextRun = (Get-Date).AddSeconds($IntervalSeconds)
        Write-Host ""
        Write-Host "⏰ [Lumen-Prism Loop] Next execution at: $($NextRun.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
    }
    
    Start-Sleep -Seconds $IntervalSeconds
}
