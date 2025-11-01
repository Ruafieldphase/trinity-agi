param(
    [Parameter(Mandatory=$true)][string[]]$Paths,
    [string]$SourceEncoding = 'euc-kr',
    [switch]$NoBackup,
    [switch]$AutoDetect
)

$ErrorActionPreference = 'Stop'

try { chcp 65001 > $null 2> $null } catch {}

function Get-EncodingObject($name){
    try { return [System.Text.Encoding]::GetEncoding($name) } catch { return $null }
}

$candidateNames = @('utf-8','euc-kr','x-cp20949','iso-2022-kr','x-mac-korean','windows-1252','us-ascii')
$candidates = @{}
foreach($n in $candidateNames){ $enc = Get-EncodingObject $n; if($enc){ $candidates[$n] = $enc } }

if(-not $AutoDetect){
    $srcEnc = Get-EncodingObject $SourceEncoding
    if(-not $srcEnc){ throw "Unsupported encoding: $SourceEncoding" }
}
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$results = @()

function Score-Text([string]$text){
    $hangul = ([regex]::Matches($text,'[\uAC00-\uD7A3]')).Count
    $bad = ([regex]::Matches($text,'[\uFFFD]|\?\?')).Count
    $ctrl = ([regex]::Matches($text,'[\x00-\x08\x0B\x0C\x0E-\x1F]')).Count
    return ($hangul * 10) - ($bad * 5) - ($ctrl * 2)
}
foreach($p in $Paths){
    if(-not (Test-Path $p)){
        $results += [pscustomobject]@{ Path=$p; Status='Missing'; Bytes=0 }
        continue
    }
    try{
        $bytes = [System.IO.File]::ReadAllBytes($p)
        $text  = $null
        if($AutoDetect){
            $bestScore = [int]::MinValue
            $bestText  = $null
            $bestName  = ''
            foreach($kv in $candidates.GetEnumerator()){
                try{
                    $t = $kv.Value.GetString($bytes)
                    $s = Score-Text $t
                    if($s -gt $bestScore){ $bestScore = $s; $bestText = $t; $bestName = $kv.Key }
                } catch {}
            }
            if(-not $bestText){ $bestText = [System.Text.Encoding]::UTF8.GetString($bytes); $bestName = 'utf-8(fallback)' }
            $text = $bestText
            $detected = $bestName
        } else {
            $text = $srcEnc.GetString($bytes)
            $detected = $SourceEncoding
        }
        if(-not $NoBackup){ Copy-Item -Path $p -Destination ($p + '.bak') -Force }
        [System.IO.File]::WriteAllText($p, $text, $utf8NoBom)
        $results += [pscustomobject]@{ Path=$p; Status=('Converted from ' + $detected); Bytes=$bytes.Length }
    } catch {
        $results += [pscustomobject]@{ Path=$p; Status=('Error: ' + $_.Exception.Message); Bytes=0 }
    }
}

$results | Format-Table -AutoSize | Out-String | Write-Host

try{
    $outDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs'
    if(-not (Test-Path $outDir)){ New-Item -ItemType Directory -Path $outDir | Out-Null }
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $summary = @()
    $summary += "# UTF-8 Encoding Conversion Summary ($stamp)"
    $summary += "Source encoding: $SourceEncoding"
    $summary += ""
    foreach($r in $results){ $summary += "- ${($r.Path)} => ${($r.Status)} (${($r.Bytes)} bytes)" }
    $summary -join "`n" | Out-File -FilePath (Join-Path $outDir "encoding_fix_summary_${stamp}.md") -Encoding utf8
} catch {}
