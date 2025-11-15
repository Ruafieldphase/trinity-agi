#Requires -Version 5.1
<#
.SYNOPSIS
    Fast File Reader - PowerShell Wrapper
.DESCRIPTION
    Everything 검색 + 초고속 파일 읽기
.EXAMPLE
    .\fast_read.ps1 -Pattern "*.md" -MaxFiles 5
.EXAMPLE
    .\fast_read.ps1 -Pattern "session_continuity" -NoCache
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Pattern,
    
    [int]$MaxFiles = 10,
    
    [int]$MaxWorkers = 4,
    
    [int]$MaxSizeMB = 100,
    
    [switch]$NoCache,
    
    [string]$Output
)

$ErrorActionPreference = "Stop"
$ws = Split-Path -Parent $PSScriptRoot
$py = Join-Path $ws "fdo_agi_repo\.venv\Scripts\python.exe"

if (!(Test-Path -LiteralPath $py)) {
    $py = "python"
}

$script = Join-Path $ws "scripts\fast_file_reader.py"

$args = @(
    $script,
    $Pattern,
    "--max-files", $MaxFiles,
    "--max-workers", $MaxWorkers,
    "--max-size-mb", $MaxSizeMB
)

if ($NoCache) {
    $args += "--no-cache"
}

if ($Output) {
    $args += "--output", $Output
}

Write-Host "🚀 Fast File Reader" -ForegroundColor Cyan
Write-Host ""

& $py @args

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Error occurred" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Complete!" -ForegroundColor Green
