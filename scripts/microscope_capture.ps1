#Requires -Version 5.1
param(
    [int]$WindowSeconds = 3,
    [ValidateSet('minimal', 'normal', 'full')]
    [string]$Level = 'minimal',
    [string[]]$SparkLabels = @(),
    [string]$OutDir = "$( & { . (Join-Path $PSScriptRoot 'Get-WorkspaceRoot.ps1'); Get-WorkspaceRoot } )\outputs\microscope",
    [switch]$Quiet
)
. "$PSScriptRoot\Get-WorkspaceRoot.ps1"
$WorkspaceRoot = Get-WorkspaceRoot



$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8; $OutputEncoding = [System.Text.UTF8Encoding]::UTF8 } catch {}
$ErrorActionPreference = "Continue"

function Write-Info($m) { if (-not $Quiet) { Write-Host "[Microscope] $m" -ForegroundColor Cyan } }
function Write-Warn($m) { if (-not $Quiet) { Write-Host "[Microscope] $m" -ForegroundColor Yellow } }

if ($WindowSeconds -lt 1) { $WindowSeconds = 1 }
if ($WindowSeconds -gt 30) { $WindowSeconds = 30 }

function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Method = 'GET',
        [string]$BodyJson = $null,
        [int]$TimeoutSec = 3
    )
    $result = @{ Online = $false; Ms = $null; Code = 0; Error = $null; Url = $Url }
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        if ($BodyJson) {
            $null = Invoke-RestMethod -Uri $Url -Method $Method -Body $BodyJson -ContentType "application/json" -TimeoutSec $TimeoutSec -ErrorAction Stop
        }
        else {
            $null = Invoke-RestMethod -Uri $Url -Method $Method -TimeoutSec $TimeoutSec -ErrorAction Stop
        }
        $sw.Stop()
        $result.Online = $true
        $result.Ms = [int][math]::Round($sw.Elapsed.TotalMilliseconds)
        $result.Code = 200
    }
    catch {
        $sw.Stop()
        $result.Online = $false
        $result.Ms = [int][math]::Round($sw.Elapsed.TotalMilliseconds)
        $result.Code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode.value__ } else { 0 }
        $result.Error = $_.Exception.Message
    }
    return $result
}

function Get-ProcessSnapshot {
    try {
        return Get-Process | ForEach-Object {
            try {
                [pscustomobject]@{
                    Name = $_.ProcessName
                    Id   = $_.Id
                    CPU  = [double]($_.CPU)
                    WS   = [long]($_.WorkingSet64)
                    PM   = [long]($_.PagedMemorySize64)
                }
            }
            catch { $null }
        } | Where-Object { $_ -ne $null }
    }
    catch { @() }
}

function Compare-ProcessSnapshot($before, $after, [int]$windowSec) {
    $cores = $env:NUMBER_OF_PROCESSORS; if (-not $cores) { $cores = 4 }
    $map = @{}
    foreach ($b in $before) { $map[[string]$b.Id] = $b }
    $rows = @()
    foreach ($a in $after) {
        $key = [string]$a.Id
        if ($map.ContainsKey($key)) {
            $b = $map[$key]
            $cpuDelta = [double]($a.CPU - $b.CPU)
            if ($cpuDelta -lt 0) { $cpuDelta = 0 }
            $cpuPct = 0
            if ($windowSec -gt 0 -and [int]$cores -gt 0) { $cpuPct = [math]::Min(100, [math]::Max(0, ($cpuDelta / ($windowSec * [double]$cores)) * 100.0)) }
            $rows += [pscustomobject]@{
                Name            = $a.Name
                Id              = $a.Id
                CpuSecondsDelta = [double]::Round($cpuDelta, 3)
                CpuPercent      = [double]::Round($cpuPct, 1)
                WorkingSet      = $a.WS
                PagedMemory     = $a.PM
            }
        }
    }
    $rows | Sort-Object -Property CpuPercent -Descending
}

function New-OutputDir([string]$dir) { if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null } }

New-OutputDir -dir $OutDir

Write-Info "Capturing micro snapshot for ${WindowSeconds}s (level=$Level)"

$procBefore = Get-ProcessSnapshot

Start-Sleep -Seconds $WindowSeconds

$procAfter = Get-ProcessSnapshot
$procDiff = Compare-ProcessSnapshot -before $procBefore -after $procAfter -windowSec $WindowSeconds
$topProcs = $procDiff | Select-Object -First (if ($Level -eq 'full') { 25 } elseif ($Level -eq 'normal') { 15 } else { 10 })

# System counters (best-effort)
$sys = @{ cpu_total_pct = $null; mem_available_mb = $null }
try {
    $cpu = Get-Counter -Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 1 -ErrorAction SilentlyContinue
    if ($cpu -and $cpu.CounterSamples -and $cpu.CounterSamples.CookedValue.Count -gt 0) {
        $sys.cpu_total_pct = [double]::Round($cpu.CounterSamples[0].CookedValue, 1)
    }
}
catch {}
try {
    $mem = Get-Counter -Counter '\Memory\Available MBytes' -SampleInterval 1 -MaxSamples 1 -ErrorAction SilentlyContinue
    if ($mem -and $mem.CounterSamples -and $mem.CounterSamples.CookedValue.Count -gt 0) {
        $sys.mem_available_mb = [int]$mem.CounterSamples[0].CookedValue
    }
}
catch {}

# Quick probes (local/gateway/cloud) - non-fatal
$probes = @{}
try { $probes.Local8080 = Test-Endpoint -Url 'http://127.0.0.1:8080/v1/models' -TimeoutSec 2 } catch {}
try { $probes.Gateway = Test-Endpoint -Url 'https://Core-gateway-x4qvsargwa-uc.a.run.app/chat' -Method POST -BodyJson '{"message":"ping"}' -TimeoutSec 4 } catch {}
try { $probes.Cloud = Test-Endpoint -Url 'https://ion-api-64076350717.us-central1.run.app/chat' -Method POST -BodyJson '{"message":"ping"}' -TimeoutSec 4 } catch {}

# Task Queue Server (8091) - health + last results (best-effort)
$queue = @{ health = $null; last_results = @() }
try {
    $queue.health = Test-Endpoint -Url 'http://127.0.0.1:8091/api/health' -TimeoutSec 2
}
catch {}
try {
    $res = Invoke-RestMethod -Uri 'http://127.0.0.1:8091/api/results' -TimeoutSec 2 -ErrorAction Stop
    if ($res) {
        if ($res -is [array]) { $queue.last_results = $res | Select-Object -First 5 }
        elseif ($res.results) { $queue.last_results = $res.results | Sort-Object time -Descending | Select-Object -First 5 }
        else { $queue.last_results = @($res) }
    }
}
catch {}

$payload = @{
    timestamp  = (Get-Date).ToUniversalTime().ToString('o')
    window_sec = $WindowSeconds
    level      = $Level
    spark      = $SparkLabels
    system     = $sys
    processes  = $topProcs
    probes     = $probes
    queue      = $queue
    host       = @{ machine = $env:COMPUTERNAME; cores = [int]($env:NUMBER_OF_PROCESSORS); user = $env:USERNAME }
}

$outFile = Join-Path $OutDir ("micro_" + (Get-Date -Format 'yyyyMMdd_HHmmssfff') + ".json")
try {
    $json = $payload | ConvertTo-Json -Depth 6 -Compress
    [IO.File]::WriteAllText($outFile, $json, [Text.Encoding]::UTF8)
    Write-Info ("Saved: " + $outFile)
}
catch {
    Write-Warn "Failed to save microscope output: $($_.Exception.Message)"
}

exit 0