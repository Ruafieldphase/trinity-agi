param(
  # 기본은 "비노체가 자리를 비운 동안" 충분히 작동하도록 넉넉하게(12시간).
  [int]$Minutes = 720,
  [switch]$RunController,
  [switch]$WriteSampleTask,
  [switch]$Silent
)
. "$PSScriptRoot\..\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot

$ErrorActionPreference = "Stop"

Set-Location -Path $WorkspaceRoot

$signals = Join-Path $WorkspaceRoot "signals"
$outputs = Join-Path $WorkspaceRoot "outputs"
New-Item -ItemType Directory -Force -Path $signals | Out-Null
New-Item -ItemType Directory -Force -Path $outputs | Out-Null

$now = [DateTimeOffset]::UtcNow
$expires = $now.AddMinutes([Math]::Max(1, $Minutes)).ToUnixTimeSeconds()

$arm = @{
  armed_at   = $now.ToString("o")
  expires_at = [double]$expires
  origin     = "Binoche_Observer"
  note       = "Supervised body mode armed"
}

$armPath = Join-Path $signals "body_arm.json"
# UTF-8 without BOM (PowerShell 5.1's Set-Content -Encoding UTF8 adds BOM)
$armJson = $arm | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($armPath, $armJson, (New-Object System.Text.UTF8Encoding($false)))

# 이전 stop 요청이 남아 있으면 즉시 abort가 걸릴 수 있으니 정리
$stopPath = Join-Path $signals "body_stop.json"
Remove-Item -Force -ErrorAction SilentlyContinue $stopPath

if (-not $Silent) {
  Write-Host ("[OK] armed until (utc epoch): {0}" -f $expires)
}

if ($WriteSampleTask) {
  $taskPath = Join-Path $signals "body_task.json"
  $task = @{
    goal       = "supervised_exploration"
    created_at = $now.ToString("o")
    actions    = @(
      @{ type = "open_path"; path = "$WorkspaceRoot\outputs" },
      @{ type = "open_url"; url = "https://earth.google.com/web/" },
      @{ type = "open_url"; url = "https://www.google.com/maps" },
      @{ type = "google_search"; query = "Google 지도 로드뷰" },
      @{ type = "youtube_search"; query = "도시 배경음 ambience" },
      @{ type = "sleep"; seconds = 3 }
    )
  }
  $taskJson = $task | ConvertTo-Json -Depth 10
  [System.IO.File]::WriteAllText($taskPath, $taskJson, (New-Object System.Text.UTF8Encoding($false)))
  if (-not $Silent) {
    Write-Host "[OK] wrote signals/body_task.json"
  }
}

if ($RunController) {
  # Python EXE 탐색 (venv 우선)
  $pyw = Join-Path $WorkspaceRoot ".venv\Scripts\pythonw.exe"
  if (-not (Test-Path $pyw)) { $pyw = "pythonw.exe" }

  $script = Join-Path (Get-Location) "scripts\\windows\\supervised_body_controller.py"
  if (-not (Test-Path $script)) {
    throw "missing controller: $script"
  }

  $log = Join-Path $outputs "supervised_body_controller.log"

  $args = @(
    $script,
    "--poll-ms", "400",
    "--run-seconds", ([string](($Minutes + 5) * 60))
  )

  $p = Start-Process -FilePath $pyw -ArgumentList $args -WorkingDirectory (Get-Location) -WindowStyle Hidden -PassThru -RedirectStandardOutput $log -RedirectStandardError $log
  if (-not $Silent) {
    Write-Host ("[OK] controller started (pid={0})" -f $p.Id)
  }
}
