param(
  [string[]]$Dirs = @(
    "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\ai_binoche_conversation_origin\perple_comet_cople_eru",
    "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\ai_binoche_conversation_origin\sena",
    "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\ai_binoche_conversation_origin\rio",
    "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\ai_binoche_conversation_origin\ari"
  ),
  [string]$OutMd = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\other_ai_index.md",
  [int]$MaxFiles = 60,
  [int]$PreviewLines = 40
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



function SanitizeText([string]$text) {
  $t = $text
  # User
  $t = $t -replace 'ü', '[User A]'
  $t = $t -replace '', '[User A]'
  $t = $t -replace '\\bBinoche\\b', '[User A]'
  $t = $t -replace '????', '[User A]'
  $t = $t -replace '???u', '[User A]'
  # Sena
  $t = $t -replace '', '[Agent S]'
  $t = $t -replace '\\bSena\\b', '[Agent S]'
  $t = $t -replace '????', '[Agent S]'
  # Analyst L
  $t = $t -replace '', '[Analyst L]'
  $t = $t -replace '', '[Analyst L]'
  $t = $t -replace '\\bLubit\\b', '[Analyst L]'
  $t = $t -replace '???', '[Analyst L]'
  # Core
  $t = $t -replace '', '[Agent Core]'
  $t = $t -replace '\\bCore\\b', '[Agent Core]'
  $t = $t -replace '???', '[Agent Core]'
  # Perple
  $t = $t -replace '(?!Ƽ)', '[Agent P]'
  $t = $t -replace 'Perple(?!x)', '[Agent P]'
  $t = $t -replace '????', '[Agent P]'
  # Comet
  $t = $t -replace 'ڸ', '[Agent C]'
  $t = $t -replace '\\bComet\\b', '[Agent C]'
  $t = $t -replace '???', '[Agent C]'
  # Cople
  $t = $t -replace '', '[Agent CP]'
  $t = $t -replace '\\bCople\\b', '[Agent CP]'
  $t = $t -replace '????', '[Agent CP]'
  # Eru
  $t = $t -replace '', '[Agent E]'
  $t = $t -replace '\\bEru\\b', '[Agent E]'
  $t = $t -replace '????', '[Agent E]'
  # Rio
  $t = $t -replace '', '[Agent R]'
  $t = $t -replace '\\bRio\\b', '[Agent R]'
  $t = $t -replace '????', '[Agent R]'
  # Ari
  $t = $t -replace 'Ƹ', '[Agent Ari]'
  $t = $t -replace '\\bAri\\b', '[Agent Ari]'
  $t = $t -replace '???', '[Agent Ari]'
  return $t
}

$files = @()
foreach ($dir in $Dirs) {
  if (Test-Path $dir) {
    $files += Get-ChildItem -Path $dir -Recurse -File -Filter *.md -ErrorAction SilentlyContinue
  }
}

if (-not $files) {
  Set-Content -Path $OutMd -Value "# Other AI Conversation Index`n`n(??? ???????? .md ?????? a?? ????????)" -Encoding UTF8
  exit 0
}

$selected = $files | Sort-Object LastWriteTime -Descending | Select-Object -First $MaxFiles

$lines = @()
$lines += '# Other AI Conversation Index'
$lines += ''
foreach ($f in $selected) {
  $raw = try { Get-Content -Raw -Encoding UTF8 -Path $f.FullName } catch { try { Get-Content -Raw -Path $f.FullName } catch { '' } }
  if (-not $raw) { continue }
  $rawSan = SanitizeText $raw
  $title = ''
  $date = ''
  if ($rawSan.TrimStart().StartsWith('---')) {
    $parts = $rawSan -split "\n---\n", 3
    if ($parts.Length -ge 2) {
      $front = $parts[1]
      foreach ($ln in ($front -split "\r?\n")) {
        if ($ln -match '^title:\s*(.+)$') { $title = $matches[1].Trim('"'' ') }
        if ($ln -match '^date:\s*(.+)$') { $date = $matches[1].Trim() }
      }
    }
  }
  if (-not $title) {
    $firstHeader = ($rawSan -split "\r?\n") | Where-Object { $_ -match '^#\s+' } | Select-Object -First 1
    if ($firstHeader) { $title = $firstHeader -replace '^#\s+', '' } else { $title = $f.Name }
  }
  $preview = ($rawSan -split "\r?\n") | Select-Object -First $PreviewLines | Out-String
  $preview = $preview.TrimEnd()

  $lines += "## $title"
  $lines += "- Path: ``$($f.FullName)``"
  if ($date) { $lines += "- Date: $date" }
  $lines += "- Last Modified: $($f.LastWriteTime)"
  $lines += ''
  $lines += '```'
  $lines += $preview
  $lines += '```'
  $lines += ''
  $lines += '---'
  $lines += ''
}

$null = New-Item -ItemType Directory -Path ([System.IO.Path]::GetDirectoryName($OutMd)) -Force
Set-Content -Path $OutMd -Value ($lines -join "`n") -Encoding UTF8