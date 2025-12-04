# Everything Quick Search (CLI-based)
# Ultra-fast file search using Everything Command Line Interface
# Requires: Everything running + es.exe in scripts folder

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Query,
    
    [Parameter(Mandatory = $false)]
    [int]$MaxResults = 20,
    
    [Parameter(Mandatory = $false)]
    [string]$Path = "",
    
    [Parameter(Mandatory = $false)]
    [string]$Extension = "",
    
    [Parameter(Mandatory = $false)]
    [switch]$OpenFirst,
    
    [Parameter(Mandatory = $false)]
    [switch]$JsonOutput
)

$ErrorActionPreference = "Stop"

# Locate es.exe
$esPath = Join-Path $PSScriptRoot "es.exe"
if (!(Test-Path $esPath)) {
    Write-Host "❌ Everything CLI (es.exe) not found" -ForegroundColor Red
    Write-Host "   Run: .\scripts\everything_setup.ps1 -DownloadCLI" -ForegroundColor Yellow
    exit 1
}

# Build search query
$searchQuery = $Query

if ($Path) {
    $searchQuery = "path:""$Path"" $searchQuery"
}

if ($Extension) {
    if (!$Extension.StartsWith(".")) {
        $Extension = ".$Extension"
    }
    $searchQuery = "ext:$Extension $searchQuery"
}

# Execute search
try {
    Write-Host "🔍 Searching: $searchQuery" -ForegroundColor Cyan
    
    # Run es.exe with parameters
    $results = & $esPath -n $MaxResults $searchQuery 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Search failed" -ForegroundColor Red
        Write-Host "   Make sure Everything is running" -ForegroundColor Yellow
        exit 1
    }
    
    # Parse results
    if (!$results -or $results.Count -eq 0) {
        Write-Host "No results found for: $searchQuery" -ForegroundColor Yellow
        exit 0
    }
    
    Write-Host "Found $($results.Count) results`n" -ForegroundColor Green
    
    # Process and display results
    $processedResults = @()
    foreach ($filePath in $results) {
        if (Test-Path -LiteralPath $filePath -ErrorAction SilentlyContinue) {
            $item = Get-Item -LiteralPath $filePath -ErrorAction SilentlyContinue
            
            if ($item) {
                $result = [PSCustomObject]@{
                    Name      = $item.Name
                    FullPath  = $item.FullName
                    Directory = $item.DirectoryName
                    Type      = if ($item.PSIsContainer) { "Folder" } else { "File" }
                    Size      = if (!$item.PSIsContainer) { $item.Length } else { $null }
                    Modified  = $item.LastWriteTime
                    Extension = $item.Extension
                }
                
                $processedResults += $result
            }
        }
    }
    
    # Output
    if ($JsonOutput) {
        $processedResults | ConvertTo-Json -Depth 10
    }
    else {
        $processedResults | Format-Table -AutoSize Name, Type, 
        @{N = 'Size(KB)'; E = { if ($_.Size) { [math]::Round($_.Size / 1KB, 1) } else { "-" } } }, 
        @{N = 'Modified'; E = { $_.Modified.ToString("yyyy-MM-dd HH:mm") } },
        @{N = 'Directory'; E = { $_.Directory } }
        
        Write-Host "`n💡 Tips:" -ForegroundColor DarkGray
        Write-Host "   -OpenFirst    Open first result in VS Code" -ForegroundColor DarkGray
        Write-Host "   -JsonOutput   Machine-readable JSON output" -ForegroundColor DarkGray
        Write-Host "   -Path 'dir'   Search only in specific directory" -ForegroundColor DarkGray
        Write-Host "   -Extension py Search only Python files" -ForegroundColor DarkGray
    }
    
    # Open first result if requested
    if ($OpenFirst -and $processedResults.Count -gt 0) {
        $first = $processedResults[0]
        Write-Host "`n📂 Opening: $($first.FullPath)" -ForegroundColor Green
        
        if ($first.Type -eq "Folder") {
            Invoke-Item -LiteralPath $first.FullPath
        }
        else {
            code $first.FullPath
        }
    }
    
}
catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
