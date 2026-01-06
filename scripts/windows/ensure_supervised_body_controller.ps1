<#
Ensure Supervised Body Controller (Windowless)

목표:
- supervised_body_controller를 백그라운드로 상시 실행해,
  `signals/body_task.json`이 생성되면(그리고 `signals/body_arm.json`이 유효하면) 즉시 처리할 수 있게 한다.

원칙:
- 창 없음: pythonw.exe 사용
- 중복 프로세스 방지
- 실패해도 0 종료 (부팅/로그온 방해 금지)
#>

param(
  [switch]$ForceRestart,
  [switch]$Silent
)
. "$PSScriptRoot\..\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot

$ErrorActionPreference = "SilentlyContinue"

try {
  $ws = $WorkspaceRoot
  $script = Join-Path $ws "scripts\\windows\\supervised_body_controller.py"
  if (-not (Test-Path $script)) { exit 0 }

  $outputs = Join-Path $ws "outputs"
  if (-not (Test-Path $outputs)) { New-Item -ItemType Directory -Force -Path $outputs | Out-Null }
  $pidFile = Join-Path $outputs "supervised_body_controller.pid"

  # venv의 pythonw.exe는 환경에 따라 중복 프로세스를 만들 수 있어,
  # 시스템 pythonw를 우선 사용한다.
  $pyw = "C:\\Python313\\pythonw.exe"
  if (-not (Test-Path $pyw)) {
    $pyw = Join-Path $ws ".venv\\Scripts\\pythonw.exe"
    if (-not (Test-Path $pyw)) { $pyw = "pythonw.exe" }
  }

  $running = $false
  $needRestart = $false
  $proc = $null

  if (Test-Path $pidFile) {
    try {
      $pid = [int](Get-Content $pidFile -Raw).Trim()
      if ($pid -gt 0) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) { $running = $true }
      }
    } catch { }
  }

  # Script updated? restart
  try {
    if ($running -and $proc) {
      $scriptTime = (Get-Item $script).LastWriteTime
      if ($scriptTime -gt $proc.StartTime) { $needRestart = $true }
    }
  } catch { }

  if ($ForceRestart) { $needRestart = $true }

  # Always de-duplicate: keep at most one controller process.
  try {
    $procs = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -and $_.CommandLine -like "*supervised_body_controller.py*" }
    $procList = @($procs)

    if ($needRestart -and $procList.Count -gt 0) {
      foreach ($d in $procList) {
        try { Stop-Process -Id $d.ProcessId -Force -ErrorAction SilentlyContinue } catch { }
      }
      Start-Sleep -Milliseconds 400
      $procList = @()
    } elseif ($procList.Count -gt 1) {
      # 여러 개면 모두 정리 후 1개만 재기동(안정성 우선)
      foreach ($d in $procList) {
        try { Stop-Process -Id $d.ProcessId -Force -ErrorAction SilentlyContinue } catch { }
      }
      Start-Sleep -Milliseconds 400
      $procList = @()
    }

    if ($procList.Count -eq 1) {
      $procList[0].ProcessId | Out-File $pidFile -Encoding ascii -Force
      exit 0
    }
  } catch { }

  # Start new controller (none running)
  $args = @(
    $script,
    "--poll-ms", "400",
    "--run-seconds", "0"
  )

  $p = Start-Process -FilePath $pyw -ArgumentList $args -WorkingDirectory $ws -WindowStyle Hidden -PassThru
  if ($p -and $p.Id) {
    $p.Id | Out-File $pidFile -Encoding ascii -Force
  }
}
catch {
  if (-not $Silent) { Write-Host ("ensure supervised body error: " + $_.Exception.Message) -ForegroundColor Yellow }
}
finally {
  try { [Environment]::Exit(0) } catch { exit 0 }
}
