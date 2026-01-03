param(
    [int]$IntervalSeconds = 60,
    [int]$WorkerIntervalSeconds = 300,
    [switch]$KillExisting
)

$ErrorActionPreference = 'SilentlyContinue'

$workspace = Split-Path -Parent $PSScriptRoot
$ensureScript = Join-Path $workspace 'scripts\ensure_autonomous_worker.ps1'
$pidFile = Join-Path $workspace 'fdo_agi_repo\outputs\autonomous_worker_watchdog.pid'

Write-Host "🛡️  Autonomous Worker Watchdog (meta-layer daemon)" -ForegroundColor Cyan

# 단일 인스턴스 보장: 기존 워치독 종료 옵션
if ($KillExisting) {
    try {
        if (Test-Path $pidFile) {
            $oldPid = Get-Content -Path $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($oldPid) {
                $p = Get-Process -Id [int]$oldPid -ErrorAction SilentlyContinue
                if ($p) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
            }
            Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue | Out-Null
        }
    }
    catch {}
}

# 현재 PID 저장 (참조용)
try {
    New-Item -ItemType Directory -Path (Split-Path $pidFile -Parent) -Force | Out-Null
    Set-Content -Path $pidFile -Value $PID -Encoding ASCII
}
catch {}

while ($true) {
    try {
        # 보증 1회 실행: 없으면 기동
        & $ensureScript -WorkerIntervalSeconds $WorkerIntervalSeconds -StartIfMissing -Quiet | Out-Null
    }
    catch {}
    Start-Sleep -Seconds $IntervalSeconds
}