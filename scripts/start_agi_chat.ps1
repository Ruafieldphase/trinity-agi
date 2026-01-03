param(
  [switch]$DryRun
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot


$ErrorActionPreference = "Stop"

function Resolve-PythonPath {
  param([string]$WorkspaceRoot)

  $candidates = @(
    (Join-Path $WorkspaceRoot ".venv\Scripts\pythonw.exe"),
    (Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"),
    (Join-Path $WorkspaceRoot "venv\Scripts\pythonw.exe"),
    (Join-Path $WorkspaceRoot "venv\Scripts\python.exe")
  )

  foreach ($p in $candidates) {
    if (Test-Path -LiteralPath $p) { return $p }
  }

  $cmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Path) { return $cmd.Path }

  $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Path) { return $cmd.Path }

  return $null
}

try {
  $resolvedWorkspace = (Resolve-Path ($WorkspaceRoot)).Path
  $py = Resolve-PythonPath -WorkspaceRoot $resolvedWorkspace
  $chatScript = Join-Path $resolvedWorkspace "scripts\agi_chat_window.py"

  Write-Host "Workspace: $resolvedWorkspace"
  Write-Host "Python: $py"
  Write-Host "Script: $chatScript"

  if (-not $py) {
    throw "Python interpreter not found."
  }
  if (-not (Test-Path -LiteralPath $chatScript)) {
    throw "Script not found at: $chatScript"
  }

  if ($DryRun) {
    exit 0
  }

  # Launch the process. No Hidden window style to ensure visibility.
  # Start-Process -FilePath $py -ArgumentList @($chatScript) -WorkingDirectory $resolvedWorkspace
  
  # Try launching with & instead to see if it makes a difference in visibility
  & $py $chatScript

  exit 0
}
catch {
  Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
  try {
    $resolvedWorkspace = (Resolve-Path ($WorkspaceRoot)).Path
    $errorLog = "$resolvedWorkspace\outputs\bridge\agi_chat_power_error.txt"
    New-Item -ItemType Directory -Force -Path (Split-Path $errorLog) | Out-Null
    $_.Exception.Message | Out-File -FilePath $errorLog -Encoding utf8
  }
  catch {}
  exit 1
}