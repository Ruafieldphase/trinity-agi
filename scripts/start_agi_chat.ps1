param(
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-PythonPath {
  param([string]$WorkspaceRoot)

  $candidates = @(
    (Join-Path $WorkspaceRoot ".venv\\Scripts\\pythonw.exe"),
    (Join-Path $WorkspaceRoot ".venv\\Scripts\\python.exe"),
    (Join-Path $WorkspaceRoot "venv\\Scripts\\pythonw.exe"),
    (Join-Path $WorkspaceRoot "venv\\Scripts\\python.exe")
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
  $workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  $py = Resolve-PythonPath -WorkspaceRoot $workspaceRoot
  $chatScript = Join-Path $workspaceRoot "scripts\\agi_chat_window.py"

  if (-not $py) {
    throw "Python을 찾지 못했습니다. (python 또는 .venv\\Scripts\\python.exe 필요)"
  }
  if (-not (Test-Path -LiteralPath $chatScript)) {
    throw "대화창 스크립트를 찾지 못했습니다: $chatScript"
  }

  if ($DryRun) {
    Write-Output ("python=" + $py)
    Write-Output ("script=" + $chatScript)
    exit 0
  }

  # pythonw.exe면 콘솔이 없고, python.exe면 콘솔이 뜰 수 있어 Hidden으로 실행
  $isPythonW = ($py.ToLower().EndsWith("pythonw.exe"))
  if ($isPythonW) {
    Start-Process -FilePath $py -ArgumentList @($chatScript) -WorkingDirectory $workspaceRoot | Out-Null
  } else {
    Start-Process -FilePath $py -ArgumentList @($chatScript) -WorkingDirectory $workspaceRoot -WindowStyle Hidden | Out-Null
  }

  exit 0
} catch {
  # 실패해도 사용자에게는 최소 힌트만 남긴다(키/PII 출력 금지).
  try {
    $workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    $out = Join-Path $workspaceRoot "outputs\\bridge\\agi_chat_window_last_error.txt"
    New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
    Set-Content -LiteralPath $out -Value ($_.Exception.Message) -Encoding UTF8
  } catch {}
  exit 1
}

