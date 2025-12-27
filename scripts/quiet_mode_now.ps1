# Quiet Mode (비노체용)
# - 창 팝업/중복 실행을 즉시 정리
# - 오라 픽셀만 남김

$ErrorActionPreference = "SilentlyContinue"
$ws = Split-Path -Parent $PSScriptRoot

# 1) 팝업 유발/불필요 프로세스 종료(최소 규칙)
$patterns = @(
    "python -m agi_core.heartbeat_loop",
    "-m agi_core.heartbeat_loop",
    "\\agi_core\\heartbeat_loop.py",
    "\\scripts\\aura_controller.py",
    "\\services\\agi_aura.py",
    "\\scripts\\master_daemon_loop.py",
    "\\scripts\\sync_rhythm_from_linux.py",
    "\\scripts\\rhythm_think.py",
    "\\scripts\\start_heartbeat.py"
)

Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and ($patterns | Where-Object { $_ -and $_ -ne "" -and $_ -ne $null -and $_ -ne " " -and $_.CommandLine -like "*$_*" })
} | ForEach-Object {
    try { Stop-Process -Id $_.ProcessId -Force } catch {}
}

# 2) 오라 픽셀 보증(백그라운드)
$ensureAura = Join-Path $ws "scripts\\ensure_rubit_aura_pixel.ps1"
if (Test-Path $ensureAura) {
    & $ensureAura -Silent | Out-Null
}

