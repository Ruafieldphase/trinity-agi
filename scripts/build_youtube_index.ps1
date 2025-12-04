param(
    [Parameter(Mandatory = $false)][string]$Folder,
    [Parameter(Mandatory = $false)][string]$OutFile,
    [int]$Top = 20,
    [int]$SinceHours = 0,
    [switch]$IncludeKeywords,
    [switch]$GroupByDate,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'

# Resolve default folder
if (-not $Folder -or [string]::IsNullOrWhiteSpace($Folder)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    if (-not $scriptDir -or [string]::IsNullOrWhiteSpace($scriptDir)) { $scriptDir = $PSScriptRoot }
    if (-not $scriptDir -or [string]::IsNullOrWhiteSpace($scriptDir)) { $scriptDir = (Get-Location).Path }
    $rootDir = Split-Path -Parent $scriptDir
    $Folder = Join-Path $rootDir 'outputs/youtube_learner'
}

if (-not (Test-Path $Folder)) { throw "Folder not found: $Folder" }

$jsonFiles = Get-ChildItem -Path $Folder -Filter '*.json' -File -ErrorAction SilentlyContinue |
Sort-Object LastWriteTime -Descending

if ($SinceHours -gt 0) {
    $cutoff = (Get-Date).AddHours(-1 * $SinceHours)
    $jsonFiles = $jsonFiles | Where-Object { $_.LastWriteTime -ge $cutoff }
}

if (-not $jsonFiles -or $jsonFiles.Count -eq 0) { throw "No JSON files found in: $Folder" }

if ($Top -gt 0) { $jsonFiles = $jsonFiles | Select-Object -First $Top }

function Get-FirstNonNull([object[]]$values) {
    foreach ($v in $values) { if ($null -ne $v -and $v -ne '') { return $v } }
    return $null
}

$rows = @()
foreach ($f in $jsonFiles) {
    try {
        $obj = Get-Content -Raw -Path $f.FullName | ConvertFrom-Json
    }
    catch {
        Write-Host "Skip invalid JSON: $($f.FullName) ($($_.Exception.Message))" -ForegroundColor Yellow
        continue
    }

    $videoId = Get-FirstNonNull @($obj.video_id, $obj.data.video_id)
    $title = Get-FirstNonNull @($obj.title, $obj.data.title, '(untitled)')
    $analyzed = Get-FirstNonNull @($obj.analyzed_at, $obj.data.analyzed_at, $f.LastWriteTime.ToString('o'))
    $summary = Get-FirstNonNull @($obj.summary, $obj.data.summary, '')

    $jsonRel = $f.FullName
    $mdPath = [System.IO.Path]::ChangeExtension($f.FullName, '.md')
    $mdLink = if (Test-Path $mdPath) { $mdPath } else { $null }
    $ytLink = if ($videoId) { "https://www.youtube.com/watch?v=$videoId" } else { $null }

    $rows += [PSCustomObject]@{
        Title    = $title
        VideoId  = $videoId
        Analyzed = $analyzed
        Summary  = $summary
        YouTube  = $ytLink
        JSON     = $jsonRel
        Markdown = $mdLink
    }
}

# Calculate stats
$totalCount = $rows.Count
$avgDuration = 0
$allKeywords = @()
$withMarkdown = 0
$shortVideos = 0  # < 5 min
$mediumVideos = 0  # 5-30 min
$longVideos = 0  # > 30 min

if ($totalCount -gt 0) {
    $durations = @()
    foreach ($r in $rows) {
        if ($r.Markdown) { $withMarkdown++ }
        
        if ($r.JSON) {
            try {
                $o = Get-Content -Raw -Path $r.JSON | ConvertFrom-Json
                $dur = $o.duration
                if (-not $dur) { $dur = $o.data.duration }
                if ($dur -and $dur -gt 0) { 
                    $durations += [int]$dur 
                    
                    # Categorize by length
                    if ($dur -lt 300) { $shortVideos++ }
                    elseif ($dur -lt 1800) { $mediumVideos++ }
                    else { $longVideos++ }
                }
                $kw = $o.keywords
                if (-not $kw) { $kw = $o.data.keywords }
                if ($kw -and ($kw -is [System.Array])) { $allKeywords += $kw }
            }
            catch { }
        }
    }
    if ($durations.Count -gt 0) { $avgDuration = [int](($durations | Measure-Object -Average).Average) }
}
$topKeywords = @()
if ($allKeywords.Count -gt 0) {
    $kwFreq = $allKeywords | Group-Object | Sort-Object Count -Descending | Select-Object -First 5
    $topKeywords = $kwFreq | ForEach-Object { "$($_.Name) ($($_.Count))" }
}

# Build Markdown index
$md = @()
$md += '# YouTube Analysis Index'
$md += ''
$md += "**Generated At:** $(Get-Date -Format o)"
$md += "**Source Folder:** $Folder"
$md += ''
$md += '## 📊 Quick Stats'
$md += ''
$md += "- **Total Analyses:** $totalCount"
$md += "- **With Markdown:** $withMarkdown / $totalCount"
if ($avgDuration -gt 0) { $md += "- **Avg Duration:** ${avgDuration}s (~$([int]($avgDuration/60))m)" }
if ($shortVideos + $mediumVideos + $longVideos -gt 0) {
    $md += "- **Length Distribution:** Short (<5m): $shortVideos | Medium (5-30m): $mediumVideos | Long (>30m): $longVideos"
}
if ($topKeywords.Count -gt 0) { $md += "- **Top Keywords:** $($topKeywords -join ', ')" }
$md += ''
$md += '## � Quick Navigation'
$md += ''
$md += '**Filter Tips:**'
$md += '- Use Ctrl+F (or Cmd+F) to search by keyword, title, or video ID'
$md += '- Look for 🔵 (short), 🟡 (medium), or 🔴 (long) to filter by length'
$md += '- Check Summary column for topic overview before opening files'
$md += ''
$md += '## �� Analysis List'
$md += ''
$md += "Showing Top $($rows.Count) most recent analyses."
$md += ''

# Table header
if ($IncludeKeywords) {
    $md += '| Title | Video | Analyzed At | Summary | Keywords | JSON | Markdown |'
    $md += '|---|---|---|---|---|---|---|'
}
else {
    $md += '| Title | Video | Analyzed At | Summary | JSON | Markdown |'
    $md += '|---|---|---|---|---|---|'
}

# Group by date if requested
if ($GroupByDate) {
    $grouped = $rows | Group-Object { 
        try { 
            ([datetime]$_.Analyzed).ToString('yyyy-MM-dd') 
        }
        catch { 
            'Unknown' 
        } 
    } | Sort-Object Name -Descending
    
    foreach ($group in $grouped) {
        $md += ''
        $md += "### 📅 $($group.Name)"
        $md += ''
        
        # Table header for this group
        if ($IncludeKeywords) {
            $md += '| Title | Video | Analyzed At | Summary | Keywords | JSON | Markdown |'
            $md += '|---|---|---|---|---|---|---|'
        }
        else {
            $md += '| Title | Video | Analyzed At | Summary | JSON | Markdown |'
            $md += '|---|---|---|---|---|---|'
        }
        
        foreach ($r in $group.Group) {
            $t = ($r.Title -replace '[|]', '-')
            $yt = if ($r.YouTube) { "[link]($($r.YouTube))" } else { '' }
            $jsonLink = if ($r.JSON) { "[json]($($r.JSON))" } else { '' }
            $mdLink = if ($r.Markdown) { "[md]($($r.Markdown))" } else { '' }

            # Get duration for emoji indicator
            $lengthEmoji = ''
            if ($r.JSON) {
                try {
                    $o = Get-Content -Raw -Path $r.JSON | ConvertFrom-Json
                    $dur = $o.duration
                    if (-not $dur) { $dur = $o.data.duration }
                    if ($dur -and $dur -gt 0) {
                        if ($dur -lt 300) { $lengthEmoji = '🔵' }
                        elseif ($dur -lt 1800) { $lengthEmoji = '🟡' }
                        else { $lengthEmoji = '🔴' }
                    }
                }
                catch { }
            }

            if ($lengthEmoji) { $t = "$lengthEmoji $t" }

            # Summary preview
            $summaryText = ''
            if ($r.Summary -and $r.Summary.Length -gt 0) {
                $summaryText = [string]$r.Summary
                if ($summaryText.Length -gt 120) { $summaryText = $summaryText.Substring(0, 120) + '...' }
                $summaryText = ($summaryText -replace '[|]', '-') -replace "`n", ' ' -replace "`r", ''
            }

            $kwText = ''
            if ($IncludeKeywords -and $r.JSON) {
                try {
                    $o = Get-Content -Raw -Path $r.JSON | ConvertFrom-Json
                    $k = $o.keywords
                    if (-not $k) { $k = $o.data.keywords }
                    if ($k) {
                        if ($k -is [System.Array]) { $k = ($k | Select-Object -First 5) -join ', ' }
                        $kwText = [string]$k
                        if ($kwText.Length -gt 80) { $kwText = $kwText.Substring(0, 80) + '...' }
                        $kwText = ($kwText -replace '[|]', '-')
                    }
                }
                catch { $kwText = '' }
            }

            if ($IncludeKeywords) {
                $md += "| $t | $yt | $($r.Analyzed) | $summaryText | $kwText | $jsonLink | $mdLink |"
            }
            else {
                $md += "| $t | $yt | $($r.Analyzed) | $summaryText | $jsonLink | $mdLink |"
            }
        }
    }
}
else {
    # Original non-grouped table
    foreach ($r in $rows) {
        $t = ($r.Title -replace '[|]', '-')
        $yt = if ($r.YouTube) { "[link]($($r.YouTube))" } else { '' }
        $jsonLink = if ($r.JSON) { "[json]($($r.JSON))" } else { '' }
        $mdLink = if ($r.Markdown) { "[md]($($r.Markdown))" } else { '' }

        # Get duration for emoji indicator
        $lengthEmoji = ''
        if ($r.JSON) {
            try {
                $o = Get-Content -Raw -Path $r.JSON | ConvertFrom-Json
                $dur = $o.duration
                if (-not $dur) { $dur = $o.data.duration }
                if ($dur -and $dur -gt 0) {
                    if ($dur -lt 300) { $lengthEmoji = '🔵' }        # Short <5m
                    elseif ($dur -lt 1800) { $lengthEmoji = '🟡' }   # Medium 5-30m
                    else { $lengthEmoji = '🔴' }                      # Long >30m
                }
            }
            catch { }
        }

        # Add emoji to title
        if ($lengthEmoji) {
            $t = "$lengthEmoji $t"
        }

        # Summary preview (first 120 chars)
        $summaryText = ''
        if ($r.Summary -and $r.Summary.Length -gt 0) {
            $summaryText = [string]$r.Summary
            if ($summaryText.Length -gt 120) { $summaryText = $summaryText.Substring(0, 120) + '...' }
            $summaryText = ($summaryText -replace '[|]', '-') -replace "`n", ' ' -replace "`r", ''
        }

        $kwText = ''
        if ($IncludeKeywords -and $r.JSON) {
            try {
                $o = Get-Content -Raw -Path $r.JSON | ConvertFrom-Json
                $k = $o.keywords
                if (-not $k) { $k = $o.data.keywords }
                if ($k) {
                    if ($k -is [System.Array]) { $k = ($k | Select-Object -First 5) -join ', ' }
                    $kwText = [string]$k
                    if ($kwText.Length -gt 80) { $kwText = $kwText.Substring(0, 80) + '...' }
                    $kwText = ($kwText -replace '[|]', '-')
                }
            }
            catch { $kwText = '' }
        }

        if ($IncludeKeywords) {
            $md += "| $t | $yt | $($r.Analyzed) | $summaryText | $kwText | $jsonLink | $mdLink |"
        }
        else {
            $md += "| $t | $yt | $($r.Analyzed) | $summaryText | $jsonLink | $mdLink |"
        }
    }
}

if (-not $OutFile -or [string]::IsNullOrWhiteSpace($OutFile)) {
    $folderParent = Split-Path -Parent $Folder
    $OutFile = Join-Path $folderParent 'youtube_learner_index.md'
    if (-not (Test-Path $folderParent)) { New-Item -ItemType Directory -Force -Path $folderParent | Out-Null }
}

$mdText = $md -join "`n"
Set-Content -Path $OutFile -Value $mdText -Encoding UTF8
Write-Host "Index written: $OutFile" -ForegroundColor Green

if (-not $NoOpen) {
    try { Start-Process code $OutFile | Out-Null } catch { Write-Host "Note: Unable to open index: $($_.Exception.Message)" -ForegroundColor Yellow }
}
