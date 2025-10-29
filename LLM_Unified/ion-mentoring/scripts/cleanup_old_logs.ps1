# 오래된 모니터링 로그 정리 스크립트
# 목적: 디스크 공간 관리 및 로그 디렉터리 정리

param(
    [int]$KeepDays = 7,
    [switch]$DryRun,
    [switch]$Verbose
)

$ErrorActionPreference = 'Continue'

$logsDir = Join-Path $PSScriptRoot '..\logs'
if (-not (Test-Path $logsDir)) {
    Write-Host "[cleanup] Logs directory not found: $logsDir" -ForegroundColor Yellow
    exit 0
}

$cutoffDate = (Get-Date).AddDays(-$KeepDays)
Write-Host "[cleanup] Cleaning logs older than: $($cutoffDate.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Cyan
if ($DryRun) { Write-Host "[cleanup] DRY RUN - no files will be deleted" -ForegroundColor Yellow }

# 정리 대상 파일 패턴
$patterns = @(
    "monitor_loop_*.log",
    "status_iter_*.json",
    "auto_remediation_*.json",
    "rate_limit_probe_*.json"
)

$totalSize = 0
$totalCount = 0

foreach ($pattern in $patterns) {
    $files = Get-ChildItem $logsDir -Filter $pattern -ErrorAction SilentlyContinue | 
    Where-Object { $_.LastWriteTime -lt $cutoffDate }
    
    if ($files) {
        $patternSize = ($files | Measure-Object -Property Length -Sum).Sum
        $patternCount = $files.Count
        $totalSize += $patternSize
        $totalCount += $patternCount
        
        Write-Host "`n[cleanup] Pattern: $pattern" -ForegroundColor Gray
        Write-Host "  Files to remove: $patternCount ($([math]::Round($patternSize/1KB, 2)) KB)" -ForegroundColor White
        
        if ($Verbose -and $patternCount -le 20) {
            $files | ForEach-Object {
                Write-Host ("    - {0} ({1:yyyy-MM-dd HH:mm})" -f $_.Name, $_.LastWriteTime) -ForegroundColor DarkGray
            }
        }
        
        if (-not $DryRun) {
            $files | Remove-Item -Force -ErrorAction Continue
            Write-Host "  ✓ Removed" -ForegroundColor Green
        }
    }
    else {
        if ($Verbose) {
            Write-Host "`n[cleanup] Pattern: $pattern - no old files" -ForegroundColor DarkGray
        }
    }
}

Write-Host "`n[cleanup] Summary:" -ForegroundColor Cyan
Write-Host "  Total files: $totalCount" -ForegroundColor White
Write-Host "  Total size: $([math]::Round($totalSize/1MB, 2)) MB" -ForegroundColor White
if ($DryRun) {
    Write-Host "  Status: DRY RUN (no changes made)" -ForegroundColor Yellow
}
else {
    Write-Host "  Status: Cleanup completed" -ForegroundColor Green
}

exit 0
