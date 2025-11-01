# Register/Unregister a Windows Scheduled Task to run Lumen probe collector periodically
[CmdletBinding(DefaultParameterSetName = 'status')]
param(
    [Parameter(ParameterSetName = 'register')]
    [switch]$Register,
    [Parameter(ParameterSetName = 'unregister')]
    [switch]$Unregister,
    [Parameter(ParameterSetName = 'status')]
    [switch]$Status,
    [string]$TaskName = 'LumenProbeCollector',
    [int]$IntervalMinutes = 10,
    [switch]$RunNow,
    # passthrough to collector
    [string]$Url = '',
    [ValidateSet('GET','POST')][string]$Method = 'POST',
    [string]$Message = 'ping',
    [string]$Tag = 'scheduled',
    [int]$TimeoutSec = 8,
    [int]$Attempts = 3,
    [int]$BackoffMs = 300,
    [switch]$WriteLatest
)

$ErrorActionPreference = 'Continue'

function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m) { Write-Host $m -ForegroundColor Green }
function Warn($m) { Write-Host $m -ForegroundColor Yellow }
function Err($m) { Write-Host $m -ForegroundColor Red }

$collector = Join-Path $PSScriptRoot 'lumen_probe_collector.ps1'
if (-not (Test-Path $collector)) { Err "Collector not found: $collector"; exit 2 }
$collector = (Resolve-Path $collector).Path  # Get absolute path

$taskPath = "\\"  # root folder

try {
    if ($PSCmdlet.ParameterSetName -eq 'register' -or $Register) {
        Info "[Register] Task '$TaskName' every $IntervalMinutes minute(s)"
        
        # Unregister if exists
        $exists = schtasks /query /tn $TaskName 2>$null
        if ($LASTEXITCODE -eq 0) {
            schtasks /delete /tn $TaskName /f | Out-Null
        }
        
        # Register using schtasks (more reliable than PowerShell cmdlets)
        # Use absolute PowerShell path and expand env vars before schtasks
        $pwsh = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        $argList = @('-NoProfile','-ExecutionPolicy','Bypass','-File', '"' + $collector + '"',
            '-TimeoutSec', $TimeoutSec,
            '-Attempts', $Attempts,
            '-BackoffMs', $BackoffMs,
            '-Method', $Method,
            '-Message', ('"' + $Message + '"'),
            '-Tag', ('"' + $Tag + '"')
        )
        if (-not [string]::IsNullOrWhiteSpace($Url)) { $argList += @('-Url', ('"' + $Url + '"')) }
        if ($WriteLatest) { $argList += '-WriteLatest' }
        $cmd = $pwsh + ' ' + ($argList -join ' ')
        $user = $env:USERNAME
        
        $output = schtasks /create /tn $TaskName /tr $cmd /sc minute /mo $IntervalMinutes /ru $user /f 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Err "Operation failed: $output"
            exit 2
        }
        
        Ok "Task registered: $TaskName"
        if ($RunNow) {
            schtasks /run /tn $TaskName | Out-Null
            Ok "Task triggered now."
        }
        exit 0
    }
    elseif ($PSCmdlet.ParameterSetName -eq 'unregister' -or $Unregister) {
        $exists = schtasks /query /tn $TaskName 2>$null
        if ($LASTEXITCODE -eq 0) {
            schtasks /delete /tn $TaskName /f | Out-Null
            Ok "Task unregistered: $TaskName"
        }
        else {
            Warn "Task not found: $TaskName"
        }
        exit 0
    }
    else {
        $exists = schtasks /query /tn $TaskName 2>$null
        if ($LASTEXITCODE -eq 0) {
            Ok "Task exists: $TaskName"
            schtasks /query /tn $TaskName /v /fo list | Write-Host
        }
        else {
            Warn "Task not found: $TaskName"
        }
        exit 0
    }
}
catch {
    Err "Operation failed: $_"
    exit 2
}

