# AI Agent Quick Status - Summarize latest AI agent output

param(
    [switch]$Json,
    [switch]$FailOnEscalation,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputDir = Join-Path (Split-Path -Parent $scriptDir) "outputs"

$latestDataPath = Join-Path $outputDir "ai_agent_data_latest.json"
$latestReportPath = Join-Path $outputDir "ai_agent_report_latest.md"

function Write-Info($msg, $color = 'Gray') {
    if (-not $Quiet -and -not $Json) { Write-Host $msg -ForegroundColor $color }
}

if (-not (Test-Path $latestDataPath)) {
    Write-Info "Latest AI agent data not found: $latestDataPath" 'Yellow'
    exit 2
}

try {
    $data = Get-Content $latestDataPath -Raw | ConvertFrom-Json
}
catch {
    Write-Info "Failed to parse latest AI agent data: $($_.Exception.Message)" 'Red'
    exit 3
}

$criticalCount = ($data.Analysis.Critical | Measure-Object).Count
$warningCount = ($data.Analysis.Warning  | Measure-Object).Count
$healthyCount = ($data.Analysis.Healthy  | Measure-Object).Count
$noDataCount = ($data.Analysis.NoData   | Measure-Object).Count
$actionsCount = ($data.Analysis.Actions  | Measure-Object).Count
$confidence = $data.Confidence
$escalation = [bool]$data.Escalation
$timestamp = $data.Timestamp

if (-not (Test-Path $latestReportPath)) {
    # Best-effort lookup for latest report
    $latestReport = Get-ChildItem -Path $outputDir -Filter 'ai_agent_report_*.md' -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
    if ($latestReport) { $latestReportPath = $latestReport.FullName }
}

$summary = [ordered]@{
    timestamp  = $timestamp
    critical   = $criticalCount
    warning    = $warningCount
    healthy    = $healthyCount
    noData     = $noDataCount
    actions    = $actionsCount
    confidence = $confidence
    escalation = $escalation
    report     = $latestReportPath
    data       = $latestDataPath
}

if ($Json) {
    $summary | ConvertTo-Json -Depth 6 | Write-Output
}
else {
    Write-Info "\n================= AI Agent Quick Status =================" 'Cyan'
    Write-Info ("Timestamp : {0}" -f $timestamp) 'Gray'
    Write-Info ("Critical  : {0}" -f $criticalCount)  (if ($criticalCount -gt 0) { 'Red' } else { 'Green' })
    Write-Info ("Warning   : {0}" -f $warningCount)   (if ($warningCount -gt 0) { 'Yellow' } else { 'Green' })
    Write-Info ("Healthy   : {0}" -f $healthyCount)   'Green'
    Write-Info ("No Data   : {0}" -f $noDataCount)    'DarkGray'
    Write-Info ("Actions   : {0}" -f $actionsCount)   'Gray'
    $confColor = switch ($confidence) { 'HIGH' { 'Green' } 'MEDIUM' { 'Yellow' } Default { 'Red' } }
    Write-Info ("Confidence: {0}" -f $confidence)     $confColor
    Write-Info ("Escalation: {0}" -f (if ($escalation) { 'REQUIRED' } else { 'NOT REQUIRED' })) (if ($escalation) { 'Red' } else { 'Green' })
    if ($latestReportPath) { Write-Info ("Report    : {0}" -f $latestReportPath) 'Gray' }
    Write-Info "========================================================\n" 'Cyan'
}

if ($FailOnEscalation -and $escalation) { exit 1 } else { exit 0 }