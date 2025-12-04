#requires -Version 5.1
param(
    [Parameter(Mandatory=$true)]
    [string]$ConflictsCsv,
    [int]$TopN = 10,
    [string]$OutMarkdown = ''
)

$ErrorActionPreference = 'Stop'

function Write-Info($m){ Write-Host $m -ForegroundColor Cyan }
function Write-Err($m){ Write-Host $m -ForegroundColor Red }

if (-not (Test-Path -LiteralPath $ConflictsCsv)) { Write-Err "❌ Conflicts CSV not found: $ConflictsCsv"; exit 1 }

$rows = Import-Csv -LiteralPath $ConflictsCsv
if (-not $rows -or $rows.Count -eq 0) { Write-Info "No conflicts to summarize."; exit 0 }

# Compute decisions and deltas
$annotated = foreach($r in $rows){
    try { $srcT = [datetime]::Parse($r.SourceTime) } catch { $srcT = $null }
    try { $dstT = [datetime]::Parse($r.TargetTime) } catch { $dstT = $null }
    $dec = if(($srcT -ne $null) -and ($dstT -ne $null)){
        if($srcT -gt $dstT){ 'PreferSource' } elseif($dstT -gt $srcT){ 'PreferTarget' } else { 'Manual' }
    } else { 'Manual' }
    $ss = [int64]$r.SourceSize
    $ts = [int64]$r.TargetSize
    $sizeDelta = [math]::Abs($ss - $ts)
    $timeDelta = if(($srcT -ne $null) -and ($dstT -ne $null)) { [math]::Abs( ($srcT - $dstT).TotalSeconds ) } else { 0 }
    [pscustomobject]@{
        Folder=$r.Folder; RelativePath=$r.RelativePath; Decision=$dec;
        SourceTime=$r.SourceTime; TargetTime=$r.TargetTime;
        SourceSize=$ss; TargetSize=$ts; SizeDelta=$sizeDelta; TimeDeltaSec=[int64]$timeDelta
    }
}

$total = $annotated.Count
$byFolder = $annotated | Group-Object Folder | ForEach-Object { [pscustomobject]@{ Folder=$_.Name; Count=$_.Count } } | Sort-Object Count -Descending
$byDecision = $annotated | Group-Object Decision | ForEach-Object { [pscustomobject]@{ Decision=$_.Name; Count=$_.Count } } | Sort-Object Decision
$topSize = $annotated | Sort-Object SizeDelta -Descending | Select-Object -First $TopN
$topTime = $annotated | Sort-Object TimeDeltaSec -Descending | Select-Object -First $TopN

if (-not $OutMarkdown -or [string]::IsNullOrWhiteSpace($OutMarkdown)) {
    $outDir = Split-Path -Path $ConflictsCsv -Parent
    $OutMarkdown = Join-Path $outDir ("conflicts_summary_" + (Get-Date -Format 'yyyyMMdd_HHmmss') + ".md")
}

$lines = @()
$lines += "# Conflicts Summary"
$lines += ("- Generated: {0}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$lines += ("- Source CSV: {0}" -f $ConflictsCsv)
$lines += ""
$lines += "## Totals"
$lines += ("- Total conflicts: {0}" -f $total)
$lines += ""
$lines += "## By Folder"
foreach($f in $byFolder){ $lines += ("- {0}: {1}" -f $f.Folder, $f.Count) }
$lines += ""
$lines += "## By Decision"
foreach($d in $byDecision){ $lines += ("- {0}: {1}" -f $d.Decision, $d.Count) }
$lines += ""
$lines += ("## Top {0} by Size Delta" -f $TopN)
foreach($x in $topSize){ $lines += ("- {0}/{1} | Δsize={2} | src={3} | dst={4}" -f $x.Folder,$x.RelativePath,$x.SizeDelta,$x.SourceTime,$x.TargetTime) }
$lines += ""
$lines += ("## Top {0} by Time Delta (sec)" -f $TopN)
foreach($x in $topTime){ $lines += ("- {0}/{1} | Δtime={2}s | src={3} | dst={4}" -f $x.Folder,$x.RelativePath,$x.TimeDeltaSec,$x.SourceTime,$x.TargetTime) }

$lines | Out-File -FilePath $OutMarkdown -Encoding UTF8
Write-Info ("🧾 Summary written: {0}" -f $OutMarkdown)
exit 0
