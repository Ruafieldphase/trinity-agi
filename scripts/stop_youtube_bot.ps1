# Stop YouTube Live bot (best-effort)
$ErrorActionPreference = "SilentlyContinue"
Get-Process -Name python, py, python3 | Where-Object { $_.Path -ne $null } | ForEach-Object {
    try {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
        if ($cmd -and $cmd -match "youtube_live_bot.py") {
            Write-Host "Stopping PID $($_.Id): $cmd" -ForegroundColor Yellow
            Stop-Process -Id $_.Id -Force
        }
    }
    catch {}
}
Write-Host "Stop command issued (if any bot was running)." -ForegroundColor Green