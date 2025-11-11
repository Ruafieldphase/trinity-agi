# Everything Search Integration
# Fast file/folder search using Everything HTTP API
# Requires: Everything with HTTP Server enabled (default port 8080)

param(
    [Parameter(Mandatory = $true)]
    [string]$Query,
    
    [Parameter(Mandatory = $false)]
    [int]$MaxResults = 50,
    
    [Parameter(Mandatory = $false)]
    [string]$Path = "",
    
    [Parameter(Mandatory = $false)]
    [string]$Extension = "",
    
    [Parameter(Mandatory = $false)]
    [int]$Port = 8080,
    
    [Parameter(Mandatory = $false)]
    [switch]$JsonOutput,
    
    [Parameter(Mandatory = $false)]
    [switch]$OpenFirst
)

$ErrorActionPreference = "Stop"

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

# URL encode the query
Add-Type -AssemblyName System.Web
$encodedQuery = [System.Web.HttpUtility]::UrlEncode($searchQuery)

# Build Everything HTTP API URL
$url = "http://localhost:$Port/?search=$encodedQuery&count=$MaxResults&json=1"

try {
    # Query Everything
    Write-Host "Searching Everything: $searchQuery" -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri $url -TimeoutSec 5 -ErrorAction Stop
    
    if ($response.results.Count -eq 0) {
        Write-Host "No results found for: $searchQuery" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Found $($response.totalResults) total results (showing $($response.results.Count))" -ForegroundColor Green
    Write-Host ""
    
    # Process results
    $results = @()
    foreach ($item in $response.results) {
        $fullPath = Join-Path $item.path $item.name
        
        # Get file info if exists
        $info = $null
        if (Test-Path -LiteralPath $fullPath -ErrorAction SilentlyContinue) {
            $info = Get-Item -LiteralPath $fullPath -ErrorAction SilentlyContinue
        }
        
        $result = [PSCustomObject]@{
            Name      = $item.name
            Path      = $item.path
            FullPath  = $fullPath
            Type      = if ($item.type -eq "folder") { "Folder" } else { "File" }
            Size      = if ($info -and !$info.PSIsContainer) { $info.Length } else { $null }
            Modified  = if ($info) { $info.LastWriteTime } else { $null }
            Extension = if ($item.type -ne "folder") { [System.IO.Path]::GetExtension($item.name) } else { "" }
        }
        
        $results += $result
    }
    
    # Output results
    if ($JsonOutput) {
        $results | ConvertTo-Json -Depth 10
    }
    else {
        $results | Format-Table -AutoSize Name, Type, 
        @{N = 'Size(KB)'; E = { if ($_.Size) { [math]::Round($_.Size / 1KB, 1) } else { "-" } } }, 
        @{N = 'Modified'; E = { if ($_.Modified) { $_.Modified.ToString("yyyy-MM-dd HH:mm") } else { "-" } } },
        @{N = 'Path'; E = { $_.Path } }
        
        Write-Host ""
        Write-Host "Tip: Use -OpenFirst to open the first result" -ForegroundColor DarkGray
        Write-Host "Tip: Use -JsonOutput for machine-readable output" -ForegroundColor DarkGray
    }
    
    # Open first result if requested
    if ($OpenFirst -and $results.Count -gt 0) {
        $firstResult = $results[0]
        Write-Host ""
        Write-Host "Opening: $($firstResult.FullPath)" -ForegroundColor Green
        
        if ($firstResult.Type -eq "Folder") {
            Invoke-Item -LiteralPath $firstResult.FullPath
        }
        else {
            code $firstResult.FullPath
        }
    }
    
}
catch {
    Write-Host "Error querying Everything HTTP server on port $Port" -ForegroundColor Red
    Write-Host "Make sure Everything is running and HTTP server is enabled." -ForegroundColor Yellow
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
