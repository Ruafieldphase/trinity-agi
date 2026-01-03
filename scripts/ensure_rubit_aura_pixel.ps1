<# 
Ensure Rubit Aura Pixel (Windowless)

원칙:
- 창 없이(=pythonw) 실행
- 코드가 업데이트되면 자동 재시작(최소한의 신뢰성)
#>

param(
    [switch]$ForceRestart,
    [switch]$Silent
)

$ErrorActionPreference = "SilentlyContinue"

$WORKSPACE_ROOT = Resolve-Path "$PSScriptRoot\.."
$SCRIPT_PATH = "$WORKSPACE_ROOT\scripts\rubit_aura_pixel.py"
$PID_FILE = "$WORKSPACE_ROOT\outputs\rubit_aura_pixel.pid"
$LOCK_FILE = "$WORKSPACE_ROOT\outputs\rubit_aura_pixel.ensure.lock"
$PYW = "$WORKSPACE_ROOT\.venv\Scripts\pythonw.exe"
if (-not (Test-Path $PYW)) { $PYW = "pythonw.exe" }

# 0) Best-effort single-flight lock (prevents duplicate starters from concurrent schedulers)
try {
    if (Test-Path $LOCK_FILE) {
        try {
            $lockAgeSec = ((Get-Date) - (Get-Item $LOCK_FILE).LastWriteTime).TotalSeconds
            if ($lockAgeSec -gt 120) { Remove-Item -LiteralPath $LOCK_FILE -Force -ErrorAction SilentlyContinue }
        }
        catch { }
    }
    New-Item -ItemType File -Path $LOCK_FILE -ErrorAction Stop | Out-Null
}
catch {
    # Another instance is already running; exit quietly.
    exit 0
}

try {
    # 1. Check if running (PID file)
    $running = $false
    $needRestart = $false
    $proc = $null
    if (Test-Path $PID_FILE) {
        $pid_val = Get-Content $PID_FILE
        if ($pid_val -match "^\d+$") {
            $proc = Get-Process -Id $pid_val -ErrorAction SilentlyContinue
            if ($proc) {
                $running = $true
            }
        }
    }

    # 1.5 Code update detection (restart if script is newer than process start)
    try {
        if ($running) {
            $scriptTime = (Get-Item $SCRIPT_PATH).LastWriteTime
            $startTime = $proc.StartTime
            if ($scriptTime -gt $startTime) { $needRestart = $true }
        }
    }
    catch { }

    # Force restart requested
    if ($ForceRestart) { $needRestart = $true }

    # 1.8 Always de-duplicate (keep at most one *instance*).
    # Note: In some environments `pythonw.exe script.py` can appear as a small launcher process + a child GUI process.
    # We treat one "instance" as one root process (whose parent is not another aura process) plus its descendants.
    try {
        $procs = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*rubit_aura_pixel.py*" }
        $procList = @($procs)

        if ($needRestart -and $procList.Count -gt 0) {
            foreach ($d in $procList) {
                try { Stop-Process -Id $d.ProcessId -Force -ErrorAction SilentlyContinue } catch { }
            }
            Start-Sleep -Milliseconds 300
            $procList = @()
            $running = $false
        }
        elseif ($procList.Count -gt 0) {
            $ids = @($procList | ForEach-Object { $_.ProcessId })
            $idSet = @{}
            foreach ($id in $ids) { $idSet[$id] = $true }

            # Roots = processes whose parent is not another aura process
            $roots = @($procList | Where-Object { -not $idSet.ContainsKey($_.ParentProcessId) })

            if ($roots.Count -gt 1) {
                $keepRoot = $null
                $pidFromFile = $null
                if (Test-Path $PID_FILE) {
                    try { $pidFromFile = [int](Get-Content $PID_FILE -Raw).Trim() } catch { }
                }
                if ($pidFromFile -and ($roots | Where-Object { $_.ProcessId -eq $pidFromFile })) {
                    $keepRoot = ($roots | Where-Object { $_.ProcessId -eq $pidFromFile } | Select-Object -First 1)
                }
                else {
                    $keepRoot = ($roots | Sort-Object { $_.CreationDate } -Descending | Select-Object -First 1)
                }

                # Keep the root + its descendants
                $keepIds = @{}
                $frontier = @($keepRoot.ProcessId)
                while ($frontier.Count -gt 0) {
                    $next = @()
                    foreach ($node in $frontier) {
                        if ($keepIds.ContainsKey($node)) { continue }
                        $keepIds[$node] = $true
                        $children = @($procList | Where-Object { $_.ParentProcessId -eq $node } | ForEach-Object { $_.ProcessId })
                        $next += $children
                    }
                    $frontier = $next
                }

                foreach ($d in $procList) {
                    if ($keepIds.ContainsKey($d.ProcessId)) { continue }
                    try { Stop-Process -Id $d.ProcessId -Force -ErrorAction SilentlyContinue } catch { }
                }
                Start-Sleep -Milliseconds 200
                $keepRoot.ProcessId | Out-File $PID_FILE -Encoding ascii -Force
                $running = $true
            }
            elseif ($roots.Count -eq 1) {
                $roots[0].ProcessId | Out-File $PID_FILE -Encoding ascii -Force
                $running = $true
            }
        }
    }
    catch { }

    # 2. If not running, start with pythonw (WindowStyle Hidden)
    if (-not $running) {
        # Start new process
        $processParams = @{
            FilePath     = $PYW
            ArgumentList = """$SCRIPT_PATH""", "--position", "all", "--thickness", "2"
            WindowStyle  = "Hidden"
            PassThru     = $true
        }
        $p = Start-Process @processParams
        $p.Id | Out-File $PID_FILE -Encoding ascii -Force
    }
}
finally {
    try { Remove-Item -LiteralPath $LOCK_FILE -Force -ErrorAction SilentlyContinue } catch { }
}