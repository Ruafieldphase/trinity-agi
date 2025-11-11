param(
    [string]$Workspace = "${PSScriptRoot}\.."
)

$ErrorActionPreference = 'Stop'

try {
    $wsPath = Resolve-Path -LiteralPath $Workspace | Select-Object -ExpandProperty Path
}
catch {
    # Fallback: use as-is if resolve fails
    $wsPath = $Workspace
}

# Prevent duplicate VS Code instances if already running
$existing = Get-Process -Name 'Code' -ErrorAction SilentlyContinue
if ($existing) {
    return
}

# Try to locate VS Code executable
$candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code\Code.exe'),
    (Join-Path $env:ProgramFiles 'Microsoft VS Code\Code.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Microsoft VS Code\Code.exe')
)
$codeExe = $null
foreach ($c in $candidates) {
    if (Test-Path -LiteralPath $c) { $codeExe = $c; break }
}
if (-not $codeExe) { $codeExe = 'code' } # rely on PATH

try {
    # -n: new window, -r: reuse window if possible, open workspace folder
    Start-Process -FilePath $codeExe -ArgumentList @('-n', $wsPath) -WindowStyle Normal | Out-Null
}
catch {
    try {
        # Fallback: use cmd start to leverage PATH resolution
        Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', 'start', '""', 'code', '-n', $wsPath) -WindowStyle Hidden | Out-Null
    }
    catch {
        # Best-effort logging
        $logDir = Join-Path $PSScriptRoot '..\outputs'
        if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
        $log = Join-Path $logDir 'vscode_autostart_error.log'
        "$(Get-Date -Format o) Failed to launch VS Code. Error: $($_.Exception.Message)" | Out-File -FilePath $log -Append -Encoding UTF8
    }
}
