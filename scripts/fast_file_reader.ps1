# fast_file_reader.ps1
# Ultra-fast file reading using memory-mapped files and streaming

param(
    [Parameter(Mandatory=$false)]
    [string]$FilePath = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Pattern = "",
    
    [Parameter(Mandatory=$false)]
    [int]$MaxLines = 1000,
    
    [Parameter(Mandatory=$false)]
    [switch]$UseMemoryMap,
    
    [Parameter(Mandatory=$false)]
    [switch]$StreamMode,
    
    [Parameter(Mandatory=$false)]
    [switch]$Benchmark
)

$ErrorActionPreference = "Stop"

# Performance timer
$sw = [System.Diagnostics.Stopwatch]::StartNew()

function Read-FileMemoryMapped {
    param([string]$Path)
    
    try {
        $fileStream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
        $length = $fileStream.Length
        
        if ($length -eq 0) {
            $fileStream.Close()
            return @()
        }
        
        # Memory-mapped file for ultra-fast access
        $mmf = [System.IO.MemoryMappedFiles.MemoryMappedFile]::CreateFromFile(
            $fileStream,
            $null,
            0,
            [System.IO.MemoryMappedFiles.MemoryMappedFileAccess]::Read,
            $null,
            [System.IO.HandleInheritability]::None,
            $false
        )
        
        $accessor = $mmf.CreateViewAccessor(0, 0, [System.IO.MemoryMappedFiles.MemoryMappedFileAccess]::Read)
        $buffer = New-Object byte[] $length
        $accessor.ReadArray(0, $buffer, 0, $length) | Out-Null
        
        $text = [System.Text.Encoding]::UTF8.GetString($buffer)
        $lines = $text -split "`r?`n"
        
        $accessor.Dispose()
        $mmf.Dispose()
        $fileStream.Close()
        
        return $lines
    }
    catch {
        Write-Host "Memory-mapped read failed: $_" -ForegroundColor Red
        return @()
    }
}

function Read-FileStreaming {
    param([string]$Path, [int]$MaxLines, [string]$Pattern)
    
    $lines = @()
    $count = 0
    
    try {
        $reader = [System.IO.StreamReader]::new($Path, [System.Text.Encoding]::UTF8)
        
        while (($line = $reader.ReadLine()) -ne $null) {
            if ($Pattern -and $line -notmatch $Pattern) {
                continue
            }
            
            $lines += $line
            $count++
            
            if ($count -ge $MaxLines) {
                break
            }
        }
        
        $reader.Close()
        return $lines
    }
    catch {
        Write-Host "Streaming read failed: $_" -ForegroundColor Red
        return @()
    }
}

function Read-FileFast {
    param([string]$Path, [int]$MaxLines, [string]$Pattern)
    
    try {
        # Use .NET StreamReader for best performance
        $allLines = [System.IO.File]::ReadAllLines($Path, [System.Text.Encoding]::UTF8)
        
        if ($Pattern) {
            $filtered = $allLines | Where-Object { $_ -match $Pattern }
            return $filtered | Select-Object -First $MaxLines
        }
        
        return $allLines | Select-Object -First $MaxLines
    }
    catch {
        Write-Host "Fast read failed: $_" -ForegroundColor Red
        return @()
    }
}

# Main execution
if (-not $FilePath) {
    Write-Host "❌ No file path specified" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $FilePath)) {
    Write-Host "❌ File not found: $FilePath" -ForegroundColor Red
    exit 1
}

$fileInfo = Get-Item -LiteralPath $FilePath
$fileSizeMB = [math]::Round($fileInfo.Length / 1MB, 2)

Write-Host "📂 Reading: $($fileInfo.Name)" -ForegroundColor Cyan
Write-Host "📊 Size: $fileSizeMB MB" -ForegroundColor Gray

# Choose best method based on file size and options
$lines = @()

if ($UseMemoryMap -and $fileSizeMB -lt 100) {
    Write-Host "🚀 Using memory-mapped file..." -ForegroundColor Yellow
    $lines = Read-FileMemoryMapped -Path $FilePath
}
elseif ($StreamMode -or $MaxLines -lt 10000) {
    Write-Host "⚡ Using streaming mode..." -ForegroundColor Yellow
    $lines = Read-FileStreaming -Path $FilePath -MaxLines $MaxLines -Pattern $Pattern
}
else {
    Write-Host "💨 Using fast batch read..." -ForegroundColor Yellow
    $lines = Read-FileFast -Path $FilePath -MaxLines $MaxLines -Pattern $Pattern
}

$sw.Stop()
$elapsed = $sw.Elapsed.TotalSeconds

Write-Host ""
Write-Host "✅ Read $($lines.Count) lines in ${elapsed}s" -ForegroundColor Green
Write-Host "⚡ Speed: $([math]::Round($lines.Count / $elapsed, 0)) lines/sec" -ForegroundColor Cyan

if ($Benchmark) {
    $throughputMBs = [math]::Round($fileSizeMB / $elapsed, 2)
    Write-Host "📈 Throughput: $throughputMBs MB/s" -ForegroundColor Magenta
}

# Output lines
$lines | ForEach-Object { Write-Output $_ }

Write-Host ""
Write-Host "⏱️ Total time: ${elapsed}s" -ForegroundColor Gray