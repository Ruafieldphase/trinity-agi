param(
    [switch] $OnlyTerminal,
    [switch] $FixFiles,
    [string] $ScanRoot = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs",
    [int] $ModifiedWithinHours = 48,
    [switch] $WhatIf
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


# Ensure script runs from its location
Set-Location -Path $PSScriptRoot

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host $msg -ForegroundColor Red }

function Set-Utf8Console {
    Write-Info "[UTF-8] Applying UTF-8 settings to this PowerShell session..."
    try {
        # Set process-wide output encoding to UTF-8 without BOM
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [Console]::OutputEncoding = $utf8NoBom
        $global:OutputEncoding = $utf8NoBom
        Write-Ok "[UTF-8] Console OutputEncoding set to: $([Console]::OutputEncoding.EncodingName) (CodePage=$([Console]::OutputEncoding.CodePage))"
    }
    catch {
        Write-Warn "[UTF-8] Failed to set [Console]::OutputEncoding: $_"
    }

    try {
        # Also switch Windows code page to UTF-8
        $null = chcp 65001
        Write-Ok "[UTF-8] Active code page switched to 65001"
    }
    catch {
        Write-Warn "[UTF-8] chcp 65001 failed (non-fatal): $_"
    }

    # Common environment variables to enforce UTF-8 across tooling
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONUTF8 = '1'
    $env:LC_ALL = 'C.UTF-8'
    $env:LANG = 'C.UTF-8'

    # Improve file system default encoding behavior for some cmdlets
    if ($PSVersionTable.PSVersion.Major -ge 7) {
        # In PS7+, Out-File -Encoding utf8 uses no BOM by default
        Write-Ok "[UTF-8] PowerShell $($PSVersionTable.PSVersion) detected. UTF-8 (no BOM) is default for Out-File."
    }
    else {
        Write-Warn "[UTF-8] PowerShell $($PSVersionTable.PSVersion) detected. Out-File -Encoding utf8 writes BOM in PS5.1. Using .NET writer for no BOM where needed."
    }
}

function Get-FileEncodingGuess {
    param([string] $Path)
    # Heuristic: detect BOM, else assume ANSI (system default). Return: utf8, utf8bom, utf16le, utf16be, ansi
    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { return 'utf8bom' }
    if ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) { return 'utf16le' }
    if ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) { return 'utf16be' }
    # No BOM: try UTF-8 decode; if fails, assume ANSI
    try {
        $null = [System.Text.Encoding]::UTF8.GetString($bytes) | Out-Null
        return 'utf8'
    }
    catch {
        return 'ansi'
    }
}

function Convert-ToUtf8NoBom {
    param(
        [string] $Path,
        [switch] $WhatIf
    )
    $encGuess = Get-FileEncodingGuess -Path $Path
    if ($encGuess -in @('utf8', 'utf8bom')) {
        if ($encGuess -eq 'utf8bom') {
            Write-Info "[Fix] Removing BOM: $Path"
            if (-not $WhatIf) {
                $text = Get-Content -Path $Path -Raw -Encoding Byte
                # Strip BOM
                $text = $text[3..($text.Length - 1)]
                # Write without BOM
                [System.IO.File]::WriteAllBytes($Path, $text)
            }
        }
        else {
            Write-Info "[Skip] Already UTF-8 (no BOM): $Path"
        }
        return
    }
    Write-Info "[Fix] Converting $Path ($encGuess -> utf8 no BOM)"
    if ($WhatIf) { return }

    # Backup
    $backup = "$Path.bak_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item -Path $Path -Destination $backup -Force

    # Read as fallback encoding then write UTF-8 (no BOM)
    try {
        # Try ANSI (system default)
        $content = Get-Content -Path $Path -Raw -Encoding Default
    }
    catch {
        # Fallback: attempt Unicode
        try {
            $content = Get-Content -Path $Path -Raw -Encoding Unicode
        }
        catch {
            Write-Err "[Fix] Failed to read $Path in known encodings: $_"
            return
        }
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $content, $utf8NoBom)
}

function Convert-RecentFilesToUtf8 {
    param(
        [string] $Root,
        [int] $WithinHours = 48,
        [switch] $WhatIf
    )
    if (-not (Test-Path $Root)) {
        Write-Warn "[Scan] Root not found: $Root"
        return
    }
    $since = (Get-Date).AddHours(-1 * $WithinHours)
    $targets = Get-ChildItem -Path $Root -Recurse -File -Include *.md, *.txt, *.csv, *.json | Where-Object { $_.LastWriteTime -ge $since }
    if (-not $targets) {
        Write-Info "[Scan] No recent text files found under $Root within $WithinHours hours."
        return
    }
    foreach ($f in $targets) {
        try {
            Convert-ToUtf8NoBom -Path $f.FullName -WhatIf:$WhatIf
        }
        catch {
            Write-Warn "[Scan] Failed to process $($f.FullName): $_"
        }
    }
}

# 1) Always fix current terminal encoding
Set-Utf8Console

# 2) Optionally sanitize recent files (outputs by default)
if ($FixFiles) {
    Write-Info "[Scan] Sanitizing recent files under: $ScanRoot (Within: ${ModifiedWithinHours}h)"
    Convert-RecentFilesToUtf8 -Root (Resolve-Path $ScanRoot) -WithinHours $ModifiedWithinHours -WhatIf:$WhatIf
}

# 3) Quick test output
Write-Host "한글 출력 테스트: 정상이라면 글자가 깨지지 않습니다." -ForegroundColor Green
Write-Ok   "PYTHONIOENCODING=$env:PYTHONIOENCODING, PYTHONUTF8=$env:PYTHONUTF8, CodePage=$([Console]::OutputEncoding.CodePage)"