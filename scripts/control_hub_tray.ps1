# Requires: Windows PowerShell 5.1+
# Purpose: Lightweight system tray for one-click control of common AGI ops without window focus jumps

param(
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Relaunch in STA if needed (Windows Forms requires STA)
try {
    if ([System.Threading.Thread]::CurrentThread.ApartmentState -ne [System.Threading.ApartmentState]::STA) {
        $argsList = @('-STA', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"")
        if ($Quiet) { $argsList += '-Quiet' }
        Start-Process -FilePath 'powershell' -ArgumentList $argsList -WindowStyle Hidden | Out-Null
        return
    }
}
catch {
    # best effort; continue in current apartment if detection fails
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$script:wsRoot = Split-Path -Parent $PSScriptRoot  # workspace root (parent of scripts)

function Join-WSPath([string]$rel) {
    return (Join-Path $script:wsRoot $rel)
}

function Invoke-PSFile([string]$relFile, [string[]]$args = @()) {
    $file = Join-WSPath $relFile
    if (-not (Test-Path -LiteralPath $file)) {
        [System.Windows.Forms.MessageBox]::Show("Missing script: $relFile", 'AGI Control Hub', 'OK', 'Error') | Out-Null
        return
    }
    $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$file`"") + $args
    Start-Process -FilePath 'powershell' -ArgumentList $argList -WindowStyle Hidden | Out-Null
}

function Invoke-Python([string]$relFile, [string[]]$args = @()) {
    $py = Join-WSPath 'fdo_agi_repo\.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $py)) { $py = 'python' }
    $file = Join-WSPath $relFile
    $argList = @("`"$file`"") + $args
    Start-Process -FilePath $py -ArgumentList $argList -WindowStyle Hidden | Out-Null
}

function Stop-ByCommandLinePattern([string]$pattern) {
    try {
        $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*$pattern*" }
        foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    }
    catch { }
}

# Create tray icon
$notifyIcon = New-Object System.Windows.Forms.NotifyIcon
$notifyIcon.Icon = [System.Drawing.SystemIcons]::Application
$notifyIcon.Visible = $true
$notifyIcon.Text = 'AGI Control Hub'

$menu = New-Object System.Windows.Forms.ContextMenuStrip

function Add-MenuItem([string]$text, [scriptblock]$action) {
    $item = New-Object System.Windows.Forms.ToolStripMenuItem
    $item.Text = $text
    $item.add_Click({ param($s, $e) Start-Job -ScriptBlock $action | Out-Null })
    [void]$menu.Items.Add($item)
}

function Add-Separator() { [void]$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator)) }

# Quick Sections
Add-MenuItem 'Morning: Kickoff (1h, open)' { Invoke-PSFile 'scripts\morning_kickoff.ps1' @('-Hours', '1', '-OpenHtml') }
Add-MenuItem 'Unified: Quick Health (fast)' { Invoke-PSFile 'scripts\run_quick_health.ps1' @('-JsonOnly', '-Fast', '-TimeoutSec', '10', '-MaxDuration', '8') }
Add-Separator
Add-MenuItem 'Queue: Ensure Server (8091)' { Invoke-PSFile 'scripts\ensure_task_queue_server.ps1' @('-Port', '8091') }
Add-MenuItem 'Queue: Ensure Worker' { Invoke-PSFile 'scripts\ensure_rpa_worker.ps1' } 
Add-MenuItem 'Watchdog: Start (background)' { Invoke-Python 'fdo_agi_repo\scripts\task_watchdog.py' @('--server', 'http://127.0.0.1:8091', '--interval', '60', '--auto-recover') }
Add-MenuItem 'Watchdog: Stop' { Stop-ByCommandLinePattern 'task_watchdog.py' }
Add-Separator
Add-MenuItem 'Dashboard: Enhanced (open browser)' { Invoke-PSFile 'scripts\generate_enhanced_dashboard.ps1' @('-OpenBrowser') }
Add-MenuItem 'Dashboard: Open (auto-generate)' { Invoke-PSFile 'scripts\open_or_generate_dashboard.ps1' }
Add-MenuItem 'Monitoring: Report (24h)' { Invoke-PSFile 'scripts\generate_monitoring_report.ps1' @('-Hours', '24') }
Add-MenuItem 'Monitoring: Open Latest Dashboard' { 
    $html = Join-WSPath 'outputs\monitoring_dashboard_latest.html'
    if (Test-Path -LiteralPath $html) { Start-Process $html | Out-Null } else { Invoke-PSFile 'scripts\generate_monitoring_report.ps1' @('-Hours', '24') }
}
Add-Separator
Add-MenuItem 'End of Day: Backup' { Invoke-PSFile 'scripts\end_of_day_backup.ps1' @('-Note', 'Control Hub Tray') }
Add-MenuItem 'Open: Latest Monitoring Report (MD)' {
    $md = Join-WSPath 'outputs\monitoring_report_latest.md'
    if (Test-Path -LiteralPath $md) { Start-Process 'code' -ArgumentList @("`"$md`"") -WindowStyle Hidden | Out-Null }
}
Add-Separator

# Exit item
$exitItem = New-Object System.Windows.Forms.ToolStripMenuItem
$exitItem.Text = 'Exit Control Hub'
$exitItem.add_Click({
        try { $notifyIcon.Visible = $false; $notifyIcon.Dispose() } catch {}
        [System.Windows.Forms.Application]::Exit()
    })
[void]$menu.Items.Add($exitItem)

$notifyIcon.ContextMenuStrip = $menu

# Balloon tip on start
try { $notifyIcon.ShowBalloonTip(2500, 'AGI Control Hub', '트레이가 실행되었습니다. 아이콘을 우클릭해 액션을 선택하세요.', [System.Windows.Forms.ToolTipIcon]::Info) } catch {}

# Single-instance lock (best-effort)
try { $script:mutex = New-Object System.Threading.Mutex($false, 'AGI_ControlHub_Tray') } catch {}

[System.Windows.Forms.Application]::Run()

try { if ($script:mutex) { $script:mutex.Close() } } catch {}