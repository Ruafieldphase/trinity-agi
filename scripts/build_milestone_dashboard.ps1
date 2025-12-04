param(
    [switch]$Open,
    [switch]$NoJson
)

$ErrorActionPreference = 'Stop'
$middayPath = "C:\workspace\agi\outputs\midday_milestone_snapshot.json"
$eveningPath = "C:\workspace\agi\outputs\evening_milestone_snapshot.json"
$outMd = "C:\workspace\agi\outputs\milestone_dashboard_latest.md"
$outJson = "C:\workspace\agi\outputs\milestone_dashboard_latest.json"

function Get-JsonSafe {
    param([string]$path)
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    try { return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json }
    catch { return $null }
}

$midday = Get-JsonSafe -path $middayPath
$evening = Get-JsonSafe -path $eveningPath

# Overall status
$statuses = @()
if ($midday) { $statuses += $midday.status }
if ($evening) { $statuses += $evening.status }

function Get-StatusRank {
    param([string]$s)
    switch ($s) {
        'on_track' { return 0 }
        'partial' { return 1 }
        'below_target' { return 2 }
        default { return 3 }
    }
}

$overall = if ($statuses.Count -gt 0) {
    ($statuses | Sort-Object { Get-StatusRank $_ } | Select-Object -First 1)
}
else { 'unknown' }

# Compose MD
$nl = "`r`n"
$md = @()
$md += "# Milestone Dashboard (latest)"
$md += ""
$md += "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$md += "- Overall status: **$overall**"
$md += ""

function Get-SectionLines {
    param([string]$title, $obj)
    if (-not $obj) {
        return @("## $title", "_No snapshot found._", "")
    }
    $lines = @()
    $lines += "## $title"
    $lines += "- Timestamp: $($obj.timestamp)"
    $lines += "- Status: **$($obj.status)**"
    if ($obj.targets) {
        $t = $obj.targets
        $lines += "- Targets: cycles=$($t.cycles), events=$($t.events_min)-$($t.events_max)"
    }
    if ($obj.metrics) {
        $m = $obj.metrics
        $lines += "- Metrics: cycles=$($m.learning_cycles), events=$($m.events_processed), progress=$($m.progress_percent)%"
    }
    if ($obj.projections) {
        $p = $obj.projections
        $lines += "- Projection(24h): cycles=$($p.cycles_24h), events=$($p.events_24h)"
    }
    $lines += ""
    return $lines
}

$md += Get-SectionLines -title 'Midday (12:00 KST)' -obj $midday
$md += Get-SectionLines -title 'Evening (20:00 KST)' -obj $evening

$mdText = ($md -join $nl) + $nl
$mdText | Out-File -LiteralPath $outMd -Encoding UTF8
Write-Host "✅ Milestone dashboard generated: $outMd" -ForegroundColor Green

if (-not $NoJson) {
    $out = [ordered]@{
        generated_at = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        overall      = $overall
        midday       = $midday
        evening      = $evening
    }
    ($out | ConvertTo-Json -Depth 8) | Out-File -LiteralPath $outJson -Encoding UTF8
    Write-Host "✅ JSON saved: $outJson" -ForegroundColor Green
}

if ($Open) {
    try { code $outMd | Out-Null } catch { Start-Process $outMd }
}