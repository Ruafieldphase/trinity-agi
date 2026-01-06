# Everything Setup Helper
# Helps configure Everything for workspace integration

param(
    [Parameter(Mandatory = $false)]
    [switch]$CheckStatus,
    
    [Parameter(Mandatory = $false)]
    [switch]$DownloadCLI,
    
    [Parameter(Mandatory = $false)]
    [switch]$AddWorkspaceToIndex,
    
    [Parameter(Mandatory = $false)]
    [string]$WorkspaceFolder = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )"
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$ErrorActionPreference = "Stop"

function Test-EverythingHttpServer {
    param([int]$Port = 8080)
    
    try {
        $null = Invoke-RestMethod -Uri "http://localhost:$Port/?search=test&count=1&json=1" -TimeoutSec 2
        return $true
    }
    catch {
        return $false
    }
}

function Get-EverythingInstallPath {
    $process = Get-Process -Name "Everything" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($process -and $process.Path) {
        return Split-Path $process.Path -Parent
    }
    
    # Check common locations
    $commonPaths = @(
        "$env:ProgramFiles\Everything",
        "${env:ProgramFiles(x86)}\Everything"
    )
    
    foreach ($path in $commonPaths) {
        if (Test-Path "$path\Everything.exe") {
            return $path
        }
    }
    
    return $null
}

# Check Status
if ($CheckStatus) {
    Write-Host "=== Everything Status Check ===" -ForegroundColor Cyan
    Write-Host ""
    
    # Check if Everything is running
    $process = Get-Process -Name "Everything" -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "✅ Everything is running" -ForegroundColor Green
        Write-Host "   Path: $($process[0].Path)" -ForegroundColor Gray
    }
    else {
        Write-Host "❌ Everything is NOT running" -ForegroundColor Red
        Write-Host "   Please start Everything first" -ForegroundColor Yellow
        exit 1
    }
    
    # Check HTTP server
    Write-Host ""
    if (Test-EverythingHttpServer -Port 8080) {
        Write-Host "✅ HTTP Server is active on port 8080" -ForegroundColor Green
    }
    else {
        Write-Host "❌ HTTP Server is NOT active on port 8080" -ForegroundColor Red
        Write-Host "   Enable it in: Everything → Tools → Options → HTTP Server" -ForegroundColor Yellow
    }
    
    # Check indexed files
    Write-Host ""
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8080/?search=*&count=1&json=1" -TimeoutSec 3
        Write-Host "📊 Indexed files: $($response.totalResults | Format-Number)" -ForegroundColor Green
        
        # Check workspace
        $wsResponse = Invoke-RestMethod -Uri "http://localhost:8080/?search=path:""$WorkspaceFolder""&count=1&json=1" -TimeoutSec 3
        if ($wsResponse.totalResults -gt 0) {
            Write-Host "✅ Workspace is indexed: $($wsResponse.totalResults) files in $WorkspaceFolder" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Workspace NOT indexed: $WorkspaceFolder" -ForegroundColor Yellow
            Write-Host "   Run with -AddWorkspaceToIndex to fix" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "❌ Could not query indexed files" -ForegroundColor Red
    }
    
    # Check CLI
    Write-Host ""
    $localCliPath = Join-Path $PSScriptRoot "es.exe"
    if (Test-Path $localCliPath) {
        Write-Host "✅ Everything CLI (es.exe) is available" -ForegroundColor Green
        Write-Host "   Path: $localCliPath" -ForegroundColor Gray
    }
    else {
        # Also check system-wide
        $installPath = Get-EverythingInstallPath
        if ($installPath) {
            $systemCliPath = Join-Path $installPath "es.exe"
            if (Test-Path $systemCliPath) {
                Write-Host "✅ Everything CLI (es.exe) is available (system-wide)" -ForegroundColor Green
                Write-Host "   Path: $systemCliPath" -ForegroundColor Gray
            }
            else {
                Write-Host "⚠️  Everything CLI (es.exe) is NOT installed" -ForegroundColor Yellow
                Write-Host "   Run with -DownloadCLI to install" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "⚠️  Everything CLI (es.exe) is NOT installed" -ForegroundColor Yellow
            Write-Host "   Run with -DownloadCLI to install" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
    Write-Host "=== Quick Actions ===" -ForegroundColor Cyan
    Write-Host "  Add workspace to index: .\scripts\everything_setup.ps1 -AddWorkspaceToIndex" -ForegroundColor Gray
    Write-Host "  Download CLI tool:      .\scripts\everything_setup.ps1 -DownloadCLI" -ForegroundColor Gray
    
    exit 0
}

# Download CLI
if ($DownloadCLI) {
    Write-Host "=== Download Everything CLI ===" -ForegroundColor Cyan
    Write-Host ""
    
    # Use local scripts folder instead of Program Files (no admin required)
    $localCliPath = Join-Path $PSScriptRoot "es.exe"
    
    if (Test-Path $localCliPath) {
        Write-Host "✅ CLI already exists: $localCliPath" -ForegroundColor Green
        exit 0
    }
    
    Write-Host "Downloading Everything CLI to: $localCliPath" -ForegroundColor Yellow
    Write-Host "URL: https://www.voidtools.com/ES-1.1.0.30.x64.zip" -ForegroundColor Gray
    
    $tempZip = Join-Path $env:TEMP "everything_cli.zip"
    $tempDir = Join-Path $env:TEMP "everything_cli_extract"
    
    try {
        # Download
        Invoke-WebRequest -Uri "https://www.voidtools.com/ES-1.1.0.30.x64.zip" -OutFile $tempZip -UseBasicParsing
        
        # Extract
        if (Test-Path $tempDir) {
            Remove-Item $tempDir -Recurse -Force
        }
        Expand-Archive -Path $tempZip -DestinationPath $tempDir -Force
        
        # Copy to scripts folder (no admin needed)
        $esExe = Get-ChildItem -Path $tempDir -Filter "es.exe" -Recurse | Select-Object -First 1
        if ($esExe) {
            Copy-Item $esExe.FullName -Destination $localCliPath -Force
            Write-Host "✅ CLI installed: $localCliPath" -ForegroundColor Green
            Write-Host ""
            Write-Host "💡 Tip: You can now use .\scripts\es.exe for searches" -ForegroundColor Cyan
        }
        else {
            Write-Host "❌ Could not find es.exe in downloaded archive" -ForegroundColor Red
            exit 1
        }
        
        # Cleanup
        Remove-Item $tempZip -Force -ErrorAction SilentlyContinue
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        
    }
    catch {
        Write-Host "❌ Download failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    
    exit 0
}

# Add workspace to index
if ($AddWorkspaceToIndex) {
    Write-Host "=== Add Workspace to Everything Index ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Workspace: $WorkspaceFolder" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "📋 Manual Steps Required:" -ForegroundColor Yellow
    Write-Host "1. Open Everything" -ForegroundColor White
    Write-Host "2. Go to: Tools → Options → Indexes → Folders" -ForegroundColor White
    Write-Host "3. Click 'Add...' and browse to: $WorkspaceFolder" -ForegroundColor White
    Write-Host "4. Click OK to save and start indexing" -ForegroundColor White
    Write-Host ""
    Write-Host "⏱️  Indexing usually takes a few seconds" -ForegroundColor Gray
    Write-Host ""
    
    # Open Everything options (if supported)
    $installPath = Get-EverythingInstallPath
    if ($installPath) {
        $everythingExe = Join-Path $installPath "Everything.exe"
        if (Test-Path $everythingExe) {
            $response = Read-Host "Open Everything now? (Y/n)"
            if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
                Start-Process $everythingExe -ArgumentList "-options"
            }
        }
    }
    
    exit 0
}

# Default: show help
Write-Host "Everything Setup Helper" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usage:" -ForegroundColor Yellow
Write-Host "  -CheckStatus           Check Everything installation and configuration"
Write-Host "  -DownloadCLI           Download and install Everything CLI (es.exe)"
Write-Host "  -AddWorkspaceToIndex   Instructions to add workspace to index"
Write-Host ""
Write-Host "Examples:" -ForegroundColor Yellow
Write-Host "  .\scripts\everything_setup.ps1 -CheckStatus"
Write-Host "  .\scripts\everything_setup.ps1 -DownloadCLI"
Write-Host "  .\scripts\everything_setup.ps1 -AddWorkspaceToIndex -WorkspaceFolder "$WorkspaceRoot""