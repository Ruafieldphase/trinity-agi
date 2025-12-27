<#
 .SYNOPSIS
   Utilities to sanitize text/files for Copilot: strip emojis, non-BMP chars, and unsafe control/zero-width chars.

 .DESCRIPTION
   - Sanitize-Text: cleans a string
   - Sanitize-File: cleans a file and writes a .safe copy (or in-place)
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Sanitize-Text {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [string]$Text
    )
    begin {
        # Regexes prepared once
        $script:rxSurrogatePair = New-Object System.Text.RegularExpressions.Regex("[\uD800-\uDBFF][\uDC00-\uDFFF]", 'Compiled')
        $script:rxSurrogates = New-Object System.Text.RegularExpressions.Regex("[\uD800-\uDFFF]", 'Compiled')
        $script:rxVarSelectors = New-Object System.Text.RegularExpressions.Regex("[\uFE00-\uFE0F]", 'Compiled')
        $script:rxZeroWidth = New-Object System.Text.RegularExpressions.Regex("[\u200B-\u200D\u2060\uFEFF]", 'Compiled')
    }
    process {
        $t = $Text
        if ([string]::IsNullOrEmpty($t)) { return $t }

        # 1) Remove non-BMP chars (surrogate pairs) → most emoji and uncommon symbols
        $t = $script:rxSurrogatePair.Replace($t, '')
        # 2) Remove any remaining surrogate halves (defensive)
        $t = $script:rxSurrogates.Replace($t, '')
        # 3) Remove emoji variation selectors and zero-width characters
        $t = $script:rxVarSelectors.Replace($t, '')
        $t = $script:rxZeroWidth.Replace($t, '')
        
        # 4) Remove control chars except CR/LF/TAB
        $sb = New-Object System.Text.StringBuilder ($t.Length)
        foreach ($ch in $t.ToCharArray()) {
            $code = [int][char]$ch
            if ([char]::IsControl($ch)) {
                if ($code -eq 10 -or $code -eq 13 -or $code -eq 9) {
                    [void]$sb.Append($ch)
                }
                else { continue }
            }
            else {
                [void]$sb.Append($ch)
            }
        }
        $sb.ToString()
    }
}

function Sanitize-File {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$Path,
        [switch]$InPlace
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "File not found: $Path"
    }

    $content = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $clean = ($content | Sanitize-Text)

    if ($InPlace) {
        # Write back
        $clean | Out-File -FilePath $Path -Encoding UTF8 -Force
        return $Path
    }
    else {
        $dir = Split-Path -Parent $Path
        $base = [System.IO.Path]::GetFileNameWithoutExtension($Path)
        $ext = [System.IO.Path]::GetExtension($Path)
        if ([string]::IsNullOrEmpty($ext)) { $ext = '.md' }
        $safeExt = if ($ext -ieq '.md') { '.safe.md' } else { ".safe$ext" }
        $safePath = Join-Path $dir ("$base$safeExt")
        $clean | Out-File -FilePath $safePath -Encoding UTF8 -Force
        return $safePath
    }
}

Export-ModuleMember -Function Sanitize-Text, Sanitize-File
# PowerShell module: Sanitize
# Utilities to strip problematic characters (emoji/non-BMP, variation selectors, control chars)

function Remove-EmojiAndNonBmp {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline = $true)]
        [AllowNull()]
        [string]$Text
    )
    process {
        if ($null -eq $Text -or $Text.Length -eq 0) { return $Text }
        # Remove surrogate pairs (non-BMP code points; most emoji)
        $clean = [System.Text.RegularExpressions.Regex]::Replace($Text, "[\uD800-\uDBFF][\uDC00-\uDFFF]", "")
        # Remove emoji variation selectors (FE0E/FE0F)
        $clean = $clean -replace "[\uFE0E\uFE0F]", ""
        return $clean
    }
}

function Remove-DisallowedControls {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromPipeline = $true)]
        [AllowNull()]
        [string]$Text
    )
    process {
        if ($null -eq $Text -or $Text.Length -eq 0) { return $Text }
        # Remove all C0 control chars except TAB (0x09), LF (0x0A), CR (0x0D)
        return [System.Text.RegularExpressions.Regex]::Replace($Text, "[\x00-\x08\x0B\x0C\x0E-\x1F]", "")
    }
}

function Sanitize-Text {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, ValueFromPipeline = $true)]
        [AllowNull()]
        [string]$Text
    )
    process {
        $t = $Text | Remove-EmojiAndNonBmp | Remove-DisallowedControls
        # Normalize to Form C (composed)
        $t = [System.Text.NormalizationForm]::FormC
        $t = ($t -as [string]) # no-op to keep type consistent
        return $Text | Remove-EmojiAndNonBmp | Remove-DisallowedControls
    }
}

function Write-FileUtf8NoBom {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Content
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Sanitize-File {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [string]$OutFile,
        [switch]$InPlace
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "File not found: $Path"
    }
    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    $clean = $raw | Sanitize-Text
    if ($InPlace) {
        Write-FileUtf8NoBom -Path $Path -Content $clean
        return $Path
    }
    if (-not $OutFile) {
        $dir = Split-Path -Parent $Path
        $name = Split-Path -Leaf $Path
        $OutFile = Join-Path $dir ("$name.sanitized")
    }
    Write-FileUtf8NoBom -Path $OutFile -Content $clean
    return $OutFile
}

Export-ModuleMember -Function Remove-EmojiAndNonBmp, Remove-DisallowedControls, Sanitize-Text, Write-FileUtf8NoBom, Sanitize-File
