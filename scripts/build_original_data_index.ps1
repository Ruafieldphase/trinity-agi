param(
    [string]$Root = "C:\\workspace\\original_data",
    [string]$OutDir = "$PSScriptRoot/../outputs",
    [int]$MaxFiles = 10000,
    [string[]]$IncludeExt = @('.md', '.txt', '.json', '.csv', '.yaml', '.yml', '.pdf', '.docx', '.xlsx', '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mov'),
    [switch]$ComputeHash,
    [int]$MaxHashMB = 5,
    [switch]$AllowEmpty,
    [switch]$OpenMd,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'

function Normalize-Path([string]$p) {
    return [System.IO.Path]::GetFullPath($p)
}

function Ensure-Directory([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
    }
}

function Get-FileHashSafe([System.IO.FileInfo]$file) {
    try {
        $maxBytes = $MaxHashMB * 1MB
        if ($file.Length -le $maxBytes) {
            return (Get-FileHash -Algorithm SHA1 -LiteralPath $file.FullName).Hash
        }
        else {
            return $null
        }
    }
    catch {
        return $null
    }
}

function Get-TitleAndTags([System.IO.FileInfo]$file) {
    $title = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
    $tags = @()
    try {
        if ($file.Extension -in @('.md', '.txt', '.json', '.yaml', '.yml')) {
            $lines = Get-Content -LiteralPath $file.FullName -TotalCount 50 -ErrorAction Stop
            if ($file.Extension -eq '.md') {
                $h1 = $lines | Where-Object { $_ -match '^#\s+' } | Select-Object -First 1
                if ($h1) { $title = ($h1 -replace '^#\s+', '').Trim() }
            }
            # crude YAML front matter tags
            if ($lines.Length -gt 0 -and $lines[0].Trim() -eq '---') {
                $endIdx = ($lines | Select-String -Pattern '^---\s*$' -SimpleMatch:$false | Select-Object -Skip 1 -First 1).LineNumber
                if ($endIdx) {
                    $frontMatter = $lines[0..($endIdx - 1)]
                    $tagLine = $frontMatter | Where-Object { $_ -match '^tags\s*:' } | Select-Object -First 1
                    if ($tagLine) {
                        $tagText = ($tagLine -split ':', 2)[1]
                        # simple split and trim; avoid complex quote trimming for PS5 compat
                        $tags = ($tagText -split '[,\[\]]') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
                    }
                }
            }
        }
    }
    catch {
        # ignore parsing errors
    }
    return @{ Title = $title; Tags = $tags }
}

try {
    $rootPath = Normalize-Path $Root
}
catch {
    Write-Warning "Invalid Root path: $Root"
    $rootPath = $Root
}

Ensure-Directory (Normalize-Path $OutDir)
$outJson = (Normalize-Path (Join-Path $OutDir "original_data_index.json"))
$outMd = (Normalize-Path (Join-Path $OutDir "original_data_index.md"))

$results = @()
$scanned = 0
$start = Get-Date

if (-not (Test-Path -LiteralPath $rootPath)) {
    Write-Warning "Root folder not found: $rootPath"
    if ($AllowEmpty) {
        $empty = @{ root = $rootPath; generated_utc = (Get-Date).ToUniversalTime().ToString('o'); total = 0; files = @() }
        $empty | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $outJson -Encoding UTF8
        @(
            "# Original Data Index",
            "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')",
            "- Root: $rootPath",
            "- Total files: 0",
            "",
            "> Note: Root folder not found. Created an empty index.") | Set-Content -LiteralPath $outMd -Encoding UTF8
        if ($OpenMd -and -not $NoOpen) { try { code $outMd } catch { Start-Process $outMd } }
        exit 0
    }
    else {
        Write-Error "Root folder missing and AllowEmpty not set. Aborting."
        exit 1
    }
}

Write-Host "Scanning: $rootPath" -ForegroundColor Cyan

# Build extension filter
$extSet = @{}
foreach ($e in $IncludeExt) { $extSet[$e.ToLowerInvariant()] = $true }

Get-ChildItem -LiteralPath $rootPath -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
    if ($scanned -ge $MaxFiles) { return }
    $fi = $_
    $ext = $fi.Extension.ToLowerInvariant()
    if ($IncludeExt.Count -gt 0 -and -not $extSet.ContainsKey($ext)) { return }

    $meta = Get-TitleAndTags $fi
    $hash = if ($ComputeHash) { Get-FileHashSafe $fi } else { $null }

    # Compute relative path (compatible with PS5/.NET Fx)
    $relPath = $fi.Name
    try {
        $uriRoot = [System.Uri]::new((Join-Path $rootPath [IO.Path]::DirectorySeparatorChar))
        $uriFile = [System.Uri]::new($fi.FullName)
        $relPath = $uriRoot.MakeRelativeUri($uriFile).ToString()
        $relPath = $relPath.Replace('%20', ' ')
    }
    catch {
        $relPath = $fi.Name
    }

    $obj = [PSCustomObject]@{
        path          = $fi.FullName
        relative_path = $relPath
        name          = $fi.Name
        ext           = $ext
        size_bytes    = [int64]$fi.Length
        created_utc   = $fi.CreationTimeUtc.ToString('o')
        modified_utc  = $fi.LastWriteTimeUtc.ToString('o')
        title         = $meta.Title
        tags          = $meta.Tags
        sha1          = $hash
    }
    $results += $obj
    $scanned++
} | Out-Null

$summary = [PSCustomObject]@{
    root          = $rootPath
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    total         = $results.Count
    files         = $results
}

$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $outJson -Encoding UTF8

# Markdown render (top 200 rows)
$top = $results | Sort-Object -Property modified_utc -Descending | Select-Object -First 200
$md = @()
$md += "# Original Data Index"
$md += "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')"
$md += "- Root: $rootPath"
$md += "- Total files: $($results.Count)"
$md += "- Saved: $(Split-Path -Leaf $outJson), $(Split-Path -Leaf $outMd)"
$md += ""
$md += "| Title | Relative Path | Ext | Size (KB) | Modified | Tags |"
$md += "|---|---|---:|---:|---:|---|"
foreach ($f in $top) {
    $sizeKB = [math]::Round($f.size_bytes / 1KB, 1)
    $tagsStr = if ($f.tags) { ($f.tags -join ', ') } else { '' }
    $rel = $f.relative_path.Replace('\\', '/')
    $title = if ($f.title) { $f.title } else { [System.IO.Path]::GetFileNameWithoutExtension($f.name) }
    $md += "| $title | $rel | $($f.ext) | $sizeKB | $($f.modified_utc) | $tagsStr |"
}
$md | Set-Content -LiteralPath $outMd -Encoding UTF8

$elapsed = (Get-Date) - $start
Write-Host ("Index built. {0} files, {1:N1}s" -f $results.Count, $elapsed.TotalSeconds) -ForegroundColor Green

if ($OpenMd -and -not $NoOpen) {
    try { code $outMd } catch { Start-Process $outMd }
}
