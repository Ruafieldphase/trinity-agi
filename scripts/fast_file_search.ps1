<#
.SYNOPSIS
    Ultra-fast file search using Everything + memory-mapped reading

.DESCRIPTION
    Combines Everything's instant search with memory-mapped file reading
    for maximum performance on large files

.EXAMPLE
    .\fast_file_search.ps1 -Query "AGI" -Extension "md" -Top 10
    .\fast_file_search.ps1 -Query "error" -Extension "log" -ReadContent
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Query,
    
    [string]$Extension = "",
    
    [int]$Top = 20,
    
    [switch]$ReadContent,
    
    [int]$MaxLinesPerFile = 100,
    
    [switch]$AsJson,
    
    [string]$Path = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = 'Stop'

# Everything CLI path
$esPath = "$PSScriptRoot\es.exe"
if (-not (Test-Path -LiteralPath $esPath)) {
    Write-Host "⚠️  Everything CLI not found at: $esPath" -ForegroundColor Yellow
    Write-Host "💡 Falling back to standard search..." -ForegroundColor Yellow
    $useEverything = $false
}
else {
    $useEverything = $true
}

function Search-WithEverything {
    param(
        [string]$SearchQuery,
        [string]$FileExt,
        [string]$BasePath,
        [int]$Limit
    )
    
    $esArgs = @()
    
    # Build search query
    if ($FileExt) {
        $esArgs += "ext:$FileExt"
    }
    
    if ($BasePath) {
        $esArgs += "path:$BasePath"
    }
    
    $esArgs += $SearchQuery
    $esArgs += "-n", $Limit
    $esArgs += "-fullpath"
    $esArgs += "-sort", "dm"  # Sort by date modified
    
    Write-Host "🔍 Searching with Everything: $($esArgs -join ' ')" -ForegroundColor Cyan
    
    $output = & $esPath @esArgs 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  Everything search failed" -ForegroundColor Yellow
        return @()
    }
    
    return $output | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
}

function Search-Fallback {
    param(
        [string]$SearchQuery,
        [string]$FileExt,
        [string]$BasePath,
        [int]$Limit
    )
    
    Write-Host "🔍 Standard search in: $BasePath" -ForegroundColor Cyan
    
    $filter = if ($FileExt) { "*.$FileExt" } else { "*" }
    
    Get-ChildItem -Path $BasePath -Filter $filter -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "*$SearchQuery*" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First $Limit -ExpandProperty FullName
}

function Read-FileFast {
    param(
        [string]$FilePath,
        [int]$MaxLines
    )
    
    $readerScript = Join-Path $PSScriptRoot "fast_file_reader.ps1"
    
    if (Test-Path -LiteralPath $readerScript) {
        $output = & $readerScript -Path $FilePath -MaxLines $MaxLines -AsJson 2>&1 | Out-String
        try {
            return ($output | ConvertFrom-Json).lines
        }
        catch {
            Write-Host "⚠️  Fast reader failed, using standard read" -ForegroundColor Yellow
            return Get-Content -LiteralPath $FilePath -TotalCount $MaxLines
        }
    }
    else {
        return Get-Content -LiteralPath $FilePath -TotalCount $MaxLines
    }
}

# Main execution
try {
    $startTime = Get-Date
    
    # Search for files
    if ($useEverything) {
        $files = Search-WithEverything -SearchQuery $Query -FileExt $Extension -BasePath $Path -Limit $Top
    }
    else {
        $files = Search-Fallback -SearchQuery $Query -FileExt $Extension -BasePath $Path -Limit $Top
    }
    
    if (-not $files) {
        Write-Host "❌ No files found matching query: $Query" -ForegroundColor Red
        exit 1
    }
    
    $searchElapsed = (Get-Date) - $startTime
    Write-Host "✅ Found $($files.Count) files in $($searchElapsed.TotalMilliseconds)ms" -ForegroundColor Green
    
    # Read content if requested
    $results = @()
    
    foreach ($file in $files) {
        $fileInfo = Get-Item -LiteralPath $file
        
        $entry = @{
            path       = $file
            name       = $fileInfo.Name
            size_bytes = $fileInfo.Length
            modified   = $fileInfo.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        }
        
        if ($ReadContent) {
            Write-Host "📖 Reading: $($fileInfo.Name)" -ForegroundColor Cyan
            $readStart = Get-Date
            
            $content = Read-FileFast -FilePath $file -MaxLines $MaxLinesPerFile
            
            $readElapsed = (Get-Date) - $readStart
            
            $entry.content = $content
            $entry.lines_read = $content.Count
            $entry.read_time_ms = $readElapsed.TotalMilliseconds
            
            Write-Host "  ✅ Read $($content.Count) lines in $($readElapsed.TotalMilliseconds)ms" -ForegroundColor Green
        }
        
        $results += $entry
    }
    
    $totalElapsed = (Get-Date) - $startTime
    
    # Output
    if ($AsJson) {
        @{
            query          = $Query
            extension      = $Extension
            file_count     = $results.Count
            total_time_ms  = $totalElapsed.TotalMilliseconds
            search_time_ms = $searchElapsed.TotalMilliseconds
            files          = $results
        } | ConvertTo-Json -Depth 10
    }
    else {
        Write-Host "`n📊 Search Results:" -ForegroundColor Cyan
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        
        foreach ($result in $results) {
            Write-Host "`n📄 $($result.name)" -ForegroundColor Yellow
            Write-Host "   Path: $($result.path)" -ForegroundColor Gray
            Write-Host "   Size: $([math]::Round($result.size_bytes / 1KB, 2)) KB" -ForegroundColor Gray
            Write-Host "   Modified: $($result.modified)" -ForegroundColor Gray
            
            if ($result.content) {
                Write-Host "   Lines: $($result.lines_read)" -ForegroundColor Gray
                Write-Host "   Read time: $($result.read_time_ms)ms" -ForegroundColor Gray
                
                Write-Host "`n   Content preview:" -ForegroundColor Cyan
                $result.content | Select-Object -First 5 | ForEach-Object {
                    Write-Host "   │ $_" -ForegroundColor White
                }
                
                if ($result.content.Count -gt 5) {
                    Write-Host "   │ ... ($($result.content.Count - 5) more lines)" -ForegroundColor DarkGray
                }
            }
        }
        
        Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
        Write-Host "⚡ Total time: $($totalElapsed.TotalMilliseconds)ms" -ForegroundColor Green
    }
    
    exit 0
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}