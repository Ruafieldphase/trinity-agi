# Filter monitoring logs by time range
# Usage: .\filter_logs_by_time.ps1 -StartTime "2025-01-20 08:00" -EndTime "2025-01-20 12:00"
# Usage: .\filter_logs_by_time.ps1 -Last 1h
# Usage: .\filter_logs_by_time.ps1 -Last 30m -OutJson filtered_logs.json

param(
    [Parameter(Mandatory = $false)]
    [datetime]$StartTime,
    [Parameter(Mandatory = $false)]
    [datetime]$EndTime,
    [Parameter(Mandatory = $false)]
    [string]$Last,  # e.g., "1h", "30m", "2d"
    [Parameter(Mandatory = $false)]
    [string]$LogDir = "d:\nas_backup\LLM_Unified\ion-mentoring\logs",
    [Parameter(Mandatory = $false)]
    [string]$OutJson,
    [Parameter(Mandatory = $false)]
    [switch]$ShowSummary
)

$ErrorActionPreference = 'Stop'

function ConvertFrom-Duration {
    param([string]$duration)
    if ($duration -match '^(\d+)([mhd])$') {
        $value = [int]$matches[1]
        $unit = $matches[2]
        switch ($unit) {
            'm' { return [TimeSpan]::FromMinutes($value) }
            'h' { return [TimeSpan]::FromHours($value) }
            'd' { return [TimeSpan]::FromDays($value) }
        }
    }
    throw "Invalid duration format: $duration. Use format like '30m', '2h', '1d'"
}

# Determine time range
if ($Last) {
    $duration = ConvertFrom-Duration $Last
    $EndTime = Get-Date
    $StartTime = $EndTime - $duration
    Write-Host "Filtering logs from last $Last ($StartTime to $EndTime)" -ForegroundColor Cyan
}
elseif (-not $StartTime -or -not $EndTime) {
    # Default: last 24 hours
    $EndTime = Get-Date
    $StartTime = $EndTime.AddHours(-24)
    Write-Host "No time range specified. Using default: last 24 hours" -ForegroundColor Yellow
    Write-Host "Time range: $StartTime to $EndTime" -ForegroundColor Gray
}
else {
    Write-Host "Filtering logs from $StartTime to $EndTime" -ForegroundColor Cyan
}

# Find all JSON log files
if (-not (Test-Path $LogDir)) {
    Write-Host "Log directory not found: $LogDir" -ForegroundColor Red
    exit 1
}

$logFiles = Get-ChildItem "$LogDir\monitoring_results_*.json" -ErrorAction SilentlyContinue

if (-not $logFiles) {
    Write-Host "No log files found in $LogDir" -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($logFiles.Count) log file(s)" -ForegroundColor Gray

# Parse and filter
$allChecks = @()
foreach ($file in $logFiles) {
    try {
        $checks = Get-Content $file.FullName -Raw | ConvertFrom-Json
        if ($checks -is [array]) {
            $allChecks += $checks
        }
        else {
            $allChecks += @($checks)
        }
    }
    catch {
        Write-Host "Warning: Could not parse $($file.Name): $($_.Exception.Message)" -ForegroundColor DarkYellow
    }
}

Write-Host "Total checks loaded: $($allChecks.Count)" -ForegroundColor Gray

# Filter by time
$filtered = $allChecks | Where-Object {
    try {
        $checkTime = [datetime]::Parse($_.timestamp)
        return ($checkTime -ge $StartTime) -and ($checkTime -le $EndTime)
    }
    catch {
        return $false
    }
}

Write-Host "`nFiltered checks: $($filtered.Count)" -ForegroundColor Cyan

if ($filtered.Count -eq 0) {
    Write-Host "No checks found in the specified time range." -ForegroundColor Yellow
    exit 0
}

# Output
if ($OutJson) {
    $filtered | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutJson -Encoding UTF8
    Write-Host "Filtered logs written to: $OutJson" -ForegroundColor Green
}
else {
    $filtered | ConvertTo-Json -Depth 10
}

# Optional summary
if ($ShowSummary) {
    Write-Host "`n=== Summary ===" -ForegroundColor Cyan
    $passed = ($filtered | Where-Object { $_.overall_pass }).Count
    $failed = $filtered.Count - $passed
    
    Write-Host "Total Checks: $($filtered.Count)" -ForegroundColor White
    Write-Host "Passed: $passed" -ForegroundColor Green
    Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { 'Green' } else { 'Red' })
    
    # Average metrics
    $avgP95 = ($filtered | Measure-Object -Property p95_ms -Average).Average
    $avgError = ($filtered | Measure-Object -Property error_rate_percent -Average).Average
    
    Write-Host "`nAverage Metrics:" -ForegroundColor Cyan
    Write-Host "  P95: $([math]::Round($avgP95, 2))ms" -ForegroundColor Gray
    Write-Host "  Error Rate: $([math]::Round($avgError, 4))%" -ForegroundColor Gray
    
    # Time series view (simplified)
    Write-Host "`nTime Series (last 10):" -ForegroundColor Cyan
    $filtered | Select-Object -Last 10 | ForEach-Object {
        $status = if ($_.overall_pass) { "OK" } else { "FAIL" }
        $color = if ($_.overall_pass) { "Green" } else { "Red" }
        Write-Host "  $($_.timestamp) | $status | P95: $($_.p95_ms)ms | Err: $($_.error_rate_percent)%" -ForegroundColor $color
    }
}
