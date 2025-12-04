#Requires -Version 5.1
<#
.SYNOPSIS
    Lightning-fast grep using Everything CLI + StreamReader
.DESCRIPTION
    초고속 grep 시스템
    - Everything으로 파일 순간 검색
    - StreamReader로 대용량 파일 빠른 읽기
    - 정규식 매칭 지원
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Pattern,
    
    [Parameter(Mandatory = $false)]
    [string]$FilePattern = "*",
    
    [Parameter(Mandatory = $false)]
    [string]$Extension = "",
    
    [Parameter(Mandatory = $false)]
    [switch]$Regex,
    
    [Parameter(Mandatory = $false)]
    [switch]$IgnoreCase,
    
    [Parameter(Mandatory = $false)]
    [int]$Context = 2,
    
    [Parameter(Mandatory = $false)]
    [int]$MaxMatches = 100,
    
    [Parameter(Mandatory = $false)]
    [switch]$CountOnly,
    
    [Parameter(Mandatory = $false)]
    [string]$OutJson
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# Everything CLI
$EsExe = Join-Path $PSScriptRoot "es.exe"
if (-not (Test-Path -LiteralPath $EsExe)) {
    Write-Warning "Everything CLI not found at: $EsExe"
    exit 1
}

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot

# Search files
Write-Host "🔍 Finding files..." -ForegroundColor Cyan
$EsArgs = @($FilePattern)
if ($Extension) {
    if (-not $Extension.StartsWith('.')) { $Extension = ".$Extension" }
    $EsArgs += "ext:$Extension"
}
$EsArgs += "-path", $WorkspaceRoot

$Files = & $EsExe $EsArgs 2>$null | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf }

if (-not $Files) {
    Write-Host "❌ No files found" -ForegroundColor Yellow
    exit 0
}

Write-Host "✅ Found $($Files.Count) files" -ForegroundColor Green

# Prepare regex
$RegexOptions = [System.Text.RegularExpressions.RegexOptions]::Compiled
if ($IgnoreCase) {
    $RegexOptions = $RegexOptions -bor [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
}

if ($Regex) {
    $RegexPattern = [regex]::new($Pattern, $RegexOptions)
} else {
    $EscapedPattern = [regex]::Escape($Pattern)
    $RegexPattern = [regex]::new($EscapedPattern, $RegexOptions)
}

# Search in files
Write-Host "🔎 Searching in files..." -ForegroundColor Cyan
$StartTime = Get-Date
$TotalMatches = 0
$Results = @()

foreach ($FilePath in $Files) {
    try {
        $Reader = [System.IO.StreamReader]::new($FilePath, [System.Text.Encoding]::UTF8)
        $LineNum = 0
        $FileMatches = @()
        
        while ($null -ne ($Line = $Reader.ReadLine())) {
            $LineNum++
            
            if ($RegexPattern.IsMatch($Line)) {
                $TotalMatches++
                
                if (-not $CountOnly) {
                    $FileMatches += [PSCustomObject]@{
                        File = $FilePath
                        Line = $LineNum
                        Content = $Line
                    }
                }
                
                if ($TotalMatches -ge $MaxMatches) {
                    break
                }
            }
        }
        
        $Reader.Close()
        
        if ($FileMatches.Count -gt 0) {
            $Results += $FileMatches
        }
        
        if ($TotalMatches -ge $MaxMatches) {
            break
        }
    } catch {
        Write-Warning "Error reading $FilePath : $_"
    }
}

$EndTime = Get-Date
$Duration = ($EndTime - $StartTime).TotalMilliseconds

# Output
if ($CountOnly) {
    Write-Host ""
    Write-Host "✅ Found $TotalMatches matches in ${Duration}ms" -ForegroundColor Green
} elseif ($OutJson) {
    $Output = @{
        Pattern = $Pattern
        TotalMatches = $TotalMatches
        DurationMs = [Math]::Round($Duration, 2)
        Files = ($Results | Group-Object File).Count
        Results = $Results
    }
    $Output | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutJson -Encoding UTF8
    Write-Host "✅ Results saved to: $OutJson" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚡ Found $TotalMatches matches in ${Duration}ms" -ForegroundColor Green
    Write-Host ""
    
    foreach ($Match in $Results) {
        $RelPath = $Match.File.Replace($WorkspaceRoot, "").TrimStart('\', '/')
        Write-Host "$RelPath`:$($Match.Line)" -ForegroundColor Cyan
        Write-Host "  $($Match.Content)" -ForegroundColor White
    }
}
