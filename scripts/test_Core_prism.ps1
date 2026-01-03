# Core-Prism Integration Test Script
# Core-비노체 프리즘 통합 테스트

param(
    [Parameter(HelpMessage = "Test signal를 생성하여 처리")]
    [switch]$TestSignal,
    
    [Parameter(HelpMessage = "요약 통계 조회 시간 (hours)")]
    [int]$SummaryHours = 24,
    
    [Parameter(HelpMessage = "출력 JSON 저장 경로")]
    [string]$OutJson = "",
    
    [Parameter(HelpMessage = "캐시/이벤트 JSON 전체 출력")]
    [switch]$ShowDetails,
    
    [Parameter(HelpMessage = "자동 반복 실행")]
    [switch]$AutoRepeat,
    
    [Parameter(HelpMessage = "반복 간격 (분)")]
    [int]$IntervalMinutes = 30
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"
$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Python 경로 결정
$PythonExe = Join-Path $WorkspaceRoot "fdo_agi_repo\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$PrismScript = Join-Path $WorkspaceRoot "fdo_agi_repo\orchestrator\core_prism_bridge.py"

Write-Host "🔮 [Core-Prism] Starting integration test..." -ForegroundColor Cyan
Write-Host "   Python: $PythonExe" -ForegroundColor Gray
Write-Host "   Script: $PrismScript" -ForegroundColor Gray

# 필수 파일 확인
$RequiredFiles = @(
    (Join-Path $WorkspaceRoot "fdo_agi_repo\outputs\binoche_persona.json"),
    (Join-Path $WorkspaceRoot "outputs\core_latency_latest.json")
)

foreach ($file in $RequiredFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "⚠️  [Core-Prism] Required file not found: $file" -ForegroundColor Yellow
        Write-Host "   Run these commands first:" -ForegroundColor Yellow
        Write-Host "   1. python fdo_agi_repo\scripts\rune\binoche_persona_learner.py" -ForegroundColor Yellow
        Write-Host "   2. .\scripts\core_quick_probe.ps1" -ForegroundColor Yellow
    }
}

# 인자 구성
$PythonArgs = @(
    $PrismScript,
    "--summary", $SummaryHours
)

if ($TestSignal) {
    $PythonArgs += "--test-signal"
}

if ($OutJson -ne "") {
    $PythonArgs += "--out-json", $OutJson
}

# 실행
Write-Host ""
Write-Host "🔮 [Core-Prism] Executing bridge..." -ForegroundColor Cyan

try {
    & $PythonExe @PythonArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ [Core-Prism] Integration test successful!" -ForegroundColor Green
        
        # Prism cache 확인
        $CachePath = Join-Path $WorkspaceRoot "outputs\core_prism_cache.json"
        if (Test-Path $CachePath) {
            Write-Host "📦 [Core-Prism] Prism cache saved: $CachePath" -ForegroundColor Cyan
            
            if ($ShowDetails) {
                Write-Host ""
                Write-Host "📊 [Core-Prism] Cache content:" -ForegroundColor Cyan
                Get-Content $CachePath | ConvertFrom-Json | ConvertTo-Json -Depth 5
            }
        }
        
        # Resonance events 확인
        $ResonancePath = Join-Path $WorkspaceRoot "outputs\orchestrator_resonance_events.jsonl"
        if (Test-Path $ResonancePath) {
            $EventCount = (Get-Content $ResonancePath).Count
            Write-Host "🌊 [Core-Prism] Resonance events recorded: $EventCount" -ForegroundColor Cyan
            
            if ($ShowDetails) {
                Write-Host ""
                Write-Host "📝 [Core-Prism] Latest resonance event:" -ForegroundColor Cyan
                Get-Content $ResonancePath -Tail 1 | ConvertFrom-Json | ConvertTo-Json -Depth 5
            }
        }
    }
    else {
        Write-Host "❌ [Core-Prism] Integration test failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}
catch {
    Write-Host "❌ [Core-Prism] Error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎯 [Core-Prism] Next steps:" -ForegroundColor Magenta
Write-Host "   • Check prism cache: outputs\core_prism_cache.json" -ForegroundColor Gray
Write-Host "   • View resonance events: outputs\orchestrator_resonance_events.jsonl" -ForegroundColor Gray
Write-Host "   • Update persona: python fdo_agi_repo\scripts\rune\binoche_persona_learner.py" -ForegroundColor Gray
Write-Host "   • Monitor Core: .\scripts\core_quick_probe.ps1" -ForegroundColor Gray

if ($AutoRepeat) {
    Write-Host "" 
    Write-Host "🔁 [Core-Prism] AutoRepeat enabled. Interval: $IntervalMinutes min (Ctrl+C to stop)" -ForegroundColor Cyan
    while ($true) {
        try {
            $argsList = @()
            if ($TestSignal) { $argsList += '-TestSignal' }
            if ($OutJson -ne "") { $argsList += @('-OutJson', $OutJson) }
            if ($ShowDetails) { $argsList += '-ShowDetails' }
            & (Join-Path $PSScriptRoot 'test_core_prism.ps1') @argsList
            $code = $LASTEXITCODE
            $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
            Write-Host "⏱️  [Core-Prism] Iteration finished at $ts (exit=$code)" -ForegroundColor Gray
        }
        catch {
            Write-Host "❌ [Core-Prism] Error in AutoRepeat iteration: $_" -ForegroundColor Red
        }
        Start-Sleep -Seconds ([Math]::Max(1, $IntervalMinutes) * 60)
    }
}

exit 0