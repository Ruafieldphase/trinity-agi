<#
Ensure Rubit Local Dashboard Server

목표:
- 로컬 HTML 대시보드가 JSON/JSONL을 fetch할 때 CORS/파일제약 없이 열리도록
  `python -m http.server`를 127.0.0.1에 고정하여 백그라운드로 유지한다.

기본 포트: 3031
PID 파일: outputs/rubit_dashboard_server.pid

주의:
- 실패해도 0 종료 (부팅/로그온 방해 금지)
#>

param(
    [int]$Port = 3031,
    [switch]$Silent
)

try {
    $ErrorActionPreference = 'Continue'
    $WorkspaceRoot = Split-Path -Parent $PSScriptRoot
    $Outputs = Join-Path $WorkspaceRoot 'outputs'
    if (-not (Test-Path $Outputs)) { New-Item -ItemType Directory -Path $Outputs -Force | Out-Null }
    $PidFile = Join-Path $Outputs 'rubit_dashboard_server.pid'
    $OutLog = Join-Path $Outputs 'rubit_dashboard_server.out.log'
    $ErrLog = Join-Path $Outputs 'rubit_dashboard_server.err.log'

    function Test-Listening {
        param([int]$PortToCheck)
        try {
            $hit = (netstat -ano | findstr (":{0} " -f $PortToCheck)) 2>$null
            if (-not $hit) { return $false }
            return ($hit -match 'LISTENING')
        } catch { return $false }
    }

    # 이미 서버가 살아있는지(health check)
    $online = $false
    try {
        if (Test-Listening -PortToCheck $Port) { $online = $true }
    } catch { }
    if ($online) { if (-not $Silent) { Write-Host "Dashboard server online :$Port" -ForegroundColor Green }; exit 0 }

    # PID로 살아있는 프로세스인지 확인
    if (Test-Path $PidFile) {
        try {
            $pid = [int](Get-Content $PidFile -Raw).Trim()
            if ($pid -gt 0) {
                $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($p) { if (-not $Silent) { Write-Host "Dashboard server running (pid=$pid)" -ForegroundColor Green }; exit 0 }
            }
        } catch { }
    }

    # Python 선택
    $py = Join-Path $WorkspaceRoot '.venv\Scripts\python.exe'
    $usePyLauncher = $false
    if (-not (Test-Path $py)) { $usePyLauncher = $true }

    $args = @('-m','http.server',"$Port",'--bind','127.0.0.1')

    $proc = $null
    if ($usePyLauncher) {
        $proc = Start-Process -FilePath 'py' -ArgumentList (@('-3') + $args) -WorkingDirectory $WorkspaceRoot -WindowStyle Hidden -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -PassThru
    } else {
        $proc = Start-Process -FilePath $py -ArgumentList $args -WorkingDirectory $WorkspaceRoot -WindowStyle Hidden -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -PassThru
    }

    if ($proc -and $proc.Id) {
        # 최대 3초까지 리슨 확인
        $ok = $false
        for ($i=0; $i -lt 6; $i++) {
            Start-Sleep -Milliseconds 500
            try {
                if (Test-Listening -PortToCheck $Port) { $ok = $true; break }
            } catch { }
        }
        if ($ok) {
            Set-Content -Path $PidFile -Value $proc.Id -Encoding ASCII
            if (-not $Silent) { Write-Host "Started dashboard server :$Port (pid=$($proc.Id))" -ForegroundColor Green }
        } else {
            try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch { }
            if (-not $Silent) {
                Write-Host "Failed to start dashboard server :$Port (see logs in outputs/)" -ForegroundColor Yellow
            }
        }
    }
}
catch {
    if (-not $Silent) { Write-Host ("ensure dashboard server error: " + $_.Exception.Message) -ForegroundColor Yellow }
}
finally {
    try { [Environment]::Exit(0) } catch { exit 0 }
}
