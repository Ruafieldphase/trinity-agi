param(
    [switch]$DryRun,
    [string]$OutJson
)

$ErrorActionPreference = 'Stop'

$logsDir = Join-Path $PSScriptRoot '..\logs' | Resolve-Path -ErrorAction SilentlyContinue
if (-not $logsDir) {
    New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot '..\logs') | Out-Null
    $logsDir = Resolve-Path (Join-Path $PSScriptRoot '..\logs')
}
$logsDir = $logsDir.Path
$stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$defaultOut = Join-Path $logsDir ("auto_remediation_" + $stamp + ".json")
if (-not $OutJson -or $OutJson.Trim().Length -eq 0) { $OutJson = $defaultOut }

function Write-ResultJson {
    param([hashtable]$obj)
    $obj | ConvertTo-Json -Depth 6 | Out-File -FilePath $OutJson -Encoding UTF8
    Write-Host ("[auto-remediation] Result saved: {0}" -f $OutJson) -ForegroundColor Cyan
}

function Invoke-PSHidden {
    param([string]$Script, [string[]]$ScriptArgs)
    $ps = 'powershell.exe'
    $tmp = [System.IO.Path]::GetTempFileName()
    try {
        $full = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Script) + ($ScriptArgs | Where-Object { $_ })
        $p = Start-Process -FilePath $ps -ArgumentList $full -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $tmp
        $out = if (Test-Path $tmp) { Get-Content -Path $tmp -Raw -ErrorAction SilentlyContinue } else { '' }
        return @{ ExitCode = $p.ExitCode; Output = $out }
    }
    catch { return @{ ExitCode = 1; Output = $_.Exception.Message } } finally { if (Test-Path $tmp) { Remove-Item $tmp -Force -ErrorAction SilentlyContinue } }
}

# 1) 빠른 건강 확인
$checkScript = Join-Path $PSScriptRoot 'check_monitoring_status.ps1'
$checkJson = Join-Path $logsDir ("status_" + $stamp + ".json")
$checkArgs = @('-ReturnExitCode', '-OutJson', $checkJson)
$chk = Invoke-PSHidden -Script $checkScript -Args $checkArgs
$healthy = ($chk.ExitCode -eq 0)

if ($healthy) {
    Write-ResultJson @{ stage = 'noop'; healthy = $true; message = 'No remediation needed.'; status_json = $checkJson }
    exit 0
}

# 2) 완화 단계: 균형 워밍업으로 콜드 스타트/캐시 누락 완화
$warmupScript = Join-Path $PSScriptRoot 'balanced_warmup.ps1'
if (Test-Path $warmupScript) {
    if ($DryRun) {
        Write-Host '[auto-remediation] DRY RUN: would execute balanced_warmup.ps1 -CountPerSide 25' -ForegroundColor Yellow
    }
    else {
        $res = Invoke-PSHidden -Script $warmupScript -Args @('-CountPerSide', '25')
        Write-Host ("[auto-remediation] Warmup exit={0}" -f $res.ExitCode) -ForegroundColor Gray
    }
}

# 3) 재검증
$chk2 = Invoke-PSHidden -Script $checkScript -Args $checkArgs
$healthy2 = ($chk2.ExitCode -eq 0)
if ($healthy2) {
    Write-ResultJson @{ stage = 'warmup'; healthy = $true; message = 'Recovered after warmup.'; status_json = $checkJson }
    exit 0
}

# 4) 비교 테스트로 회귀 여부 파악
$compareScript = Join-Path $PSScriptRoot 'compare_canary_vs_legacy.ps1'
if (Test-Path $compareScript) {
    if ($DryRun) {
        Write-Host '[auto-remediation] DRY RUN: would run quick compare (10 req, 50ms)' -ForegroundColor Yellow
    }
    else {
        $res2 = Invoke-PSHidden -Script $compareScript -Args @('-Method', 'GET', '-RequestsPerSide', '10', '-Retries', '0', '-DelayMsBetweenRequests', '50', '-MinSuccessRatePercent', '80')
        Write-Host ("[auto-remediation] Compare exit={0}" -f $res2.ExitCode) -ForegroundColor Gray
    }
}

# 5) 최종 재검증 후 여전히 불건강하면 롤백(보수적, DryRun 기본)
$rollbackScript = Join-Path $PSScriptRoot 'rollback_phase4_canary.ps1'
$rolledBack = $false
if (-not $DryRun -and (Test-Path $rollbackScript)) {
    try {
        $res3 = Invoke-PSHidden -Script $rollbackScript -Args @('-ProjectId', 'naeda-genesis', '-AutoApprove')
        $rolledBack = ($res3.ExitCode -eq 0)
    }
    catch { $rolledBack = $false }
}

# 6) 결과 기록
Write-ResultJson @{
    stage       = if ($rolledBack) { 'rollback' } else { 'compare' }
    healthy     = $false
    dry_run     = [bool]$DryRun
    rolled_back = [bool]$rolledBack
    status_json = $checkJson
}
exit (if ($rolledBack) { 0 } else { 1 })
