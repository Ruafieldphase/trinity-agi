# lumen_prism_loop.ps1
# 루멘의 시선을 주기적으로 프리즘으로 굴절 → 울림으로 전파

param(
    [Parameter(HelpMessage = "반복 간격 (분)")]
    [int]$IntervalMinutes = 5,

    [Parameter(HelpMessage = "테스트 신호 생성 모드")]
    [switch]$TestSignal,

    [Parameter(HelpMessage = "상세 출력 (캐시/이벤트)")]
    [switch]$ShowDetails
)

$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path -Parent $PSScriptRoot

Write-Host "🔁 [Lumen-Prism] Auto loop starting... (Interval: $IntervalMinutes min)" -ForegroundColor Cyan
Write-Host "    Stop with Ctrl+C" -ForegroundColor DarkGray

function Invoke-LumenPrismOnce {
    param(
        [switch]$TestSignal,
        [switch]$ShowDetails
    )
    try {
        $scriptPath = Join-Path $PSScriptRoot 'test_lumen_prism.ps1'
        if ($TestSignal -and $ShowDetails) {
            & $scriptPath -TestSignal -ShowDetails
        }
        elseif ($TestSignal) {
            & $scriptPath -TestSignal
        }
        elseif ($ShowDetails) {
            & $scriptPath -ShowDetails
        }
        else {
            & $scriptPath
        }
        return $LASTEXITCODE
    }
    catch {
        Write-Host "❌ [Lumen-Prism] Error in iteration: $_" -ForegroundColor Red
        return 1
    }
}

# 최초 1회 즉시 실행
$exit = Invoke-LumenPrismOnce -TestSignal:$TestSignal -ShowDetails:$ShowDetails
$ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
Write-Host "⏱️  [Lumen-Prism] Iteration finished at $ts (exit=$exit)" -ForegroundColor Gray

# 반복 루프
while ($true) {
    Start-Sleep -Seconds ([Math]::Max(1, $IntervalMinutes) * 60)
    $exit = Invoke-LumenPrismOnce -TestSignal:$TestSignal -ShowDetails:$ShowDetails
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Write-Host "⏱️  [Lumen-Prism] Iteration finished at $ts (exit=$exit)" -ForegroundColor Gray
}
