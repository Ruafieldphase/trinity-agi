#Requires -Version 5.1
<#
.SYNOPSIS
    VS Code 성능 baseline을 수집하여 대시보드에 사용합니다.

.DESCRIPTION
    실시간으로 다음 메트릭을 수집:
    - Python 프로세스 개수 및 메모리
    - Extension 개수
    - 파일 감시 개수 (추정)
    - Task Queue 통계
    - Copilot 반응성 (주관적)
#>

param(
    [string]$OutJson = "outputs\performance_baseline.json",
    [switch]$Append
)

$ErrorActionPreference = "Continue"
$workspaceRoot = Split-Path -Parent $PSScriptRoot

# Ensure output directory
$outDir = Split-Path -Parent (Join-Path $workspaceRoot $OutJson)
if (-not (Test-Path $outDir)) {
    New-Item -Path $outDir -ItemType Directory -Force | Out-Null
}

Write-Host "`n=== 📊 Collecting Performance Metrics ===" -ForegroundColor Cyan
Write-Host ""

$metrics = @{
    timestamp       = (Get-Date).ToString("o")
    collection_time = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

# 1. Python processes
Write-Host "1. Python processes..." -ForegroundColor Yellow
$pyProcs = Get-Process python* -ErrorAction SilentlyContinue
$metrics.python_process_count = $pyProcs.Count
$metrics.python_memory_mb = [math]::Round(($pyProcs | Measure-Object WorkingSet64 -Sum).Sum / 1MB, 1)

Write-Host "   Processes: $($metrics.python_process_count)" -ForegroundColor White
Write-Host "   Memory: $($metrics.python_memory_mb)MB" -ForegroundColor White

# 2. VS Code extensions
Write-Host "`n2. VS Code extensions..." -ForegroundColor Yellow
$extDir = "$env:USERPROFILE\.vscode\extensions"
if (Test-Path $extDir) {
    $extCount = (Get-ChildItem $extDir -Directory | Measure-Object).Count
    $metrics.extension_count = $extCount
    Write-Host "   Extensions: $extCount" -ForegroundColor White
}
else {
    $metrics.extension_count = 0
    Write-Host "   Extensions: Unknown" -ForegroundColor Gray
}

# 3. File watchers (estimated from settings)
Write-Host "`n3. File watchers..." -ForegroundColor Yellow
$settingsPath = "$workspaceRoot\.vscode\settings.json"
if (Test-Path $settingsPath) {
    $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
    $excludeCount = 0
    if ($settings.'files.watcherExclude') {
        $excludeCount = ($settings.'files.watcherExclude'.PSObject.Properties | Measure-Object).Count
    }
    $metrics.file_watcher_excludes = $excludeCount
    Write-Host "   Excludes: $excludeCount patterns" -ForegroundColor White
}
else {
    $metrics.file_watcher_excludes = 0
}

# 4. Task Queue stats
Write-Host "`n4. Task Queue..." -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "http://127.0.0.1:8091/api/stats" -TimeoutSec 2 -ErrorAction Stop
    $metrics.queue_pending = $stats.pending
    $metrics.queue_completed = $stats.completed
    $metrics.queue_failed = $stats.failed
    $metrics.queue_online = $true
    Write-Host "   Status: Online" -ForegroundColor Green
    Write-Host "   Pending: $($stats.pending)" -ForegroundColor White
}
catch {
    $metrics.queue_online = $false
    Write-Host "   Status: Offline" -ForegroundColor Red
}

# 5. System memory
Write-Host "`n5. System memory..." -ForegroundColor Yellow
$os = Get-CimInstance Win32_OperatingSystem
$totalMemGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
$freeMemGB = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
$usedMemGB = $totalMemGB - $freeMemGB
$memUsagePercent = [math]::Round(($usedMemGB / $totalMemGB) * 100, 1)

$metrics.system_total_memory_gb = $totalMemGB
$metrics.system_used_memory_gb = $usedMemGB
$metrics.system_memory_usage_percent = $memUsagePercent

Write-Host "   Total: ${totalMemGB}GB" -ForegroundColor White
Write-Host "   Used: ${usedMemGB}GB (${memUsagePercent}%)" -ForegroundColor White

# 6. VS Code process
Write-Host "`n6. VS Code process..." -ForegroundColor Yellow
$vscodeProcs = Get-Process Code -ErrorAction SilentlyContinue
if ($vscodeProcs) {
    $vscodeMemMB = [math]::Round(($vscodeProcs | Measure-Object WorkingSet64 -Sum).Sum / 1MB, 1)
    $metrics.vscode_process_count = $vscodeProcs.Count
    $metrics.vscode_memory_mb = $vscodeMemMB
    Write-Host "   Processes: $($vscodeProcs.Count)" -ForegroundColor White
    Write-Host "   Memory: ${vscodeMemMB}MB" -ForegroundColor White
}
else {
    $metrics.vscode_process_count = 0
    $metrics.vscode_memory_mb = 0
}

# Save to JSON
$outPath = Join-Path $workspaceRoot $OutJson
$existingData = @()

if ($Append -and (Test-Path $outPath)) {
    try {
        $existingData = Get-Content $outPath -Raw | ConvertFrom-Json
        if ($existingData -isnot [array]) {
            $existingData = @($existingData)
        }
    }
    catch {
        $existingData = @()
    }
}

$existingData += $metrics

$existingData | ConvertTo-Json -Depth 10 | Set-Content $outPath -Encoding UTF8

Write-Host "`n✅ Metrics saved to: $OutJson" -ForegroundColor Green
Write-Host ""

# Display summary
Write-Host "=== 📈 Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Python: $($metrics.python_process_count) processes, $($metrics.python_memory_mb)MB" -ForegroundColor White
Write-Host "VS Code: $($metrics.vscode_process_count) processes, $($metrics.vscode_memory_mb)MB" -ForegroundColor White
Write-Host "Extensions: $($metrics.extension_count)" -ForegroundColor White
Write-Host "System Memory: $($metrics.system_memory_usage_percent)%" -ForegroundColor White
Write-Host ""