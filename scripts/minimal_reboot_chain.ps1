<#
.SYNOPSIS
  Minimal, idempotent pre/post reboot chain for AGI workspace (Windows, PowerShell 5.1+).

.DESCRIPTION
  Runs a compact set of safety checks, snapshots, and (optionally) backup before reboot.
  After reboot, verifies core services and regenerates status. Designed to use existing
  repo scripts; any missing step is skipped gracefully and recorded.

.PARAMETER PreOnly
  Run only the pre-reboot phase.

.PARAMETER PostOnly
  Run only the post-reboot verification phase.

.PARAMETER DryRun
  Do not execute child scripts; simulate and record as Skipped with Reason=DryRun.

.PARAMETER Reboot
  After successful Pre phase, initiate a system reboot. Defaults to NO reboot unless this is set.

.PARAMETER NoBackup
  Skip end_of_day_backup.ps1 step.

.PARAMETER NoReport
  Skip generate_monitoring_report.ps1 step.

.PARAMETER Hours
  Lookback hours for monitoring report (default: 24).

.PARAMETER RegisterPostCheck
  Registers a one-shot Startup entry to run this script with -PostOnly on next logon, then self-cleans.

.PARAMETER Quiet
  Reduce console output (errors still shown). For logs, see outputs/minimal_reboot_chain_* files.

.PARAMETER OutDir
  Output directory for summary artifacts (default: repo outputs/).
#>
[CmdletBinding()]
param(
  [switch] $PreOnly,
  [switch] $PostOnly,
  [switch] $DryRun,
  [switch] $Reboot,
  [switch] $NoBackup,
  [switch] $NoReport,
  [int] $Hours = 24,
  [switch] $RegisterPostCheck,
  [switch] $Quiet,
  [string] $OutDir = 'outputs'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'  # we trap per-step

function Write-Log {
  param(
    [string] $Message,
    [ValidateSet('INFO', 'WARN', 'ERROR', 'DEBUG')] [string] $Level = 'INFO'
  )
  if ($Quiet -and $Level -eq 'DEBUG') { return }
  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  Write-Host "[$ts][$Level] $Message" -ForegroundColor @{
    'INFO' = 'Gray'; 'WARN' = 'Yellow'; 'ERROR' = 'Red'; 'DEBUG' = 'DarkGray'
  }[$Level]
}

function Resolve-RepoPaths {
  $scriptDir = $PSScriptRoot
  $repoRoot = Split-Path -Parent $scriptDir
  $outRoot = Join-Path $repoRoot $OutDir
  if (-not (Test-Path -LiteralPath $outRoot)) {
    New-Item -ItemType Directory -Path $outRoot -Force | Out-Null
  }
  return [pscustomobject]@{
    ScriptDir = $scriptDir
    RepoRoot  = $repoRoot
    OutRoot   = $outRoot
    JsonOut   = Join-Path $outRoot 'minimal_reboot_chain_latest.json'
    MdOut     = Join-Path $outRoot 'minimal_reboot_chain_latest.md'
  }
}

function New-StepRecord {
  param(
    [string] $Name
  )
  return [ordered]@{
    name          = $Name
    start         = (Get-Date).ToString('o')
    end           = $null
    durationSec   = $null
    status        = 'Pending'   # Pending|OK|Failed|Skipped
    exitCode      = $null
    error         = $null
    path          = $null
    args          = @()
    skippedReason = $null
  }
}

function Close-StepRecord {
  param(
    [hashtable] $rec,
    [string] $Status,
    [int] $ExitCode = $null,
    [string] $ErrorMessage = $null,
    [string] $SkippedReason = $null
  )
  $rec.end = (Get-Date).ToString('o')
  try {
    $rec.durationSec = [math]::Round(((Get-Date $rec.end) - (Get-Date $rec.start)).TotalSeconds, 3)
  }
  catch { $rec.durationSec = $null }
  $rec.status = $Status
  $rec.exitCode = $ExitCode
  $rec.error = $ErrorMessage
  $rec.skippedReason = $SkippedReason
  return $rec
}

function Invoke-Step {
  param(
    [hashtable] $rec,
    [string] $ScriptPath,
    [object[]] $Args
  )
  $rec.path = $ScriptPath
  $rec.args = $Args

  if ($DryRun) {
    Write-Log "[DryRun] Skip $($rec.name)" 'DEBUG'
    return Close-StepRecord -rec $rec -Status 'Skipped' -SkippedReason 'DryRun'
  }

  if (-not (Test-Path -LiteralPath $ScriptPath)) {
    Write-Log "Missing script: $ScriptPath (skip)" 'WARN'
    return Close-StepRecord -rec $rec -Status 'Skipped' -SkippedReason 'MissingScript'
  }

  $exitCode = $null
  $errMsg = $null
  try {
    Write-Log "Running: $([System.IO.Path]::GetFileName($ScriptPath)) $($Args -join ' ')" 'INFO'
    & $ScriptPath @Args
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) { $exitCode = 0 }
    if ($exitCode -ne 0) {
      Write-Log "Step $($rec.name) exited with code $exitCode" 'WARN'
      return Close-StepRecord -rec $rec -Status 'Failed' -ExitCode $exitCode
    }
    else {
      return Close-StepRecord -rec $rec -Status 'OK' -ExitCode 0
    }
  }
  catch {
    $errMsg = $_.Exception.Message
    Write-Log "Step $($rec.name) failed: $errMsg" 'ERROR'
    return Close-StepRecord -rec $rec -Status 'Failed' -ExitCode ($exitCode ?? 1) -ErrorMessage $errMsg
  }
}

function Save-Outputs {
  param(
    [hashtable] $summary,
    [string] $jsonPath,
    [string] $mdPath
  )
  try {
    $summary | ConvertTo-Json -Depth 8 | Out-File -FilePath $jsonPath -Encoding UTF8 -Force
  }
  catch {}

  try {
    $pre = $summary.pre
    $post = $summary.post
    $lines = @()
    $lines += "# Minimal Reboot Chain Summary"
    $lines += "Generated: $($summary.generated)"
    $lines += "Host: $($summary.env.computerName)  PS: $($summary.env.powershellVersion)"
    $lines += ""
    if ($pre) {
      $lines += "## Pre-Reboot"
      foreach ($s in $pre.steps) {
        $lines += "- $($s.name): $($s.status) (sec=$($s.durationSec))" + $(if ($s.skippedReason) { " [skip:$($s.skippedReason)]" } else { '' })
      }
      $lines += "Pre Status: $($pre.status)  OK=$($pre.ok) Failed=$($pre.failed) Skipped=$($pre.skipped)"
      $lines += ""
    }
    if ($post) {
      $lines += "## Post-Reboot"
      foreach ($s in $post.steps) {
        $lines += "- $($s.name): $($s.status) (sec=$($s.durationSec))" + $(if ($s.skippedReason) { " [skip:$($s.skippedReason)]" } else { '' })
      }
      $lines += "Post Status: $($post.status)  OK=$($post.ok) Failed=$($post.failed) Skipped=$($post.skipped)"
      $lines += ""
    }
    $lines += "Overall: $($summary.overall)"
    if ($summary.nextSteps) {
      $lines += ""
      $lines += "## Next Steps"
      foreach ($n in $summary.nextSteps) { $lines += "- $n" }
    }
    $lines -join "`r`n" | Out-File -FilePath $mdPath -Encoding UTF8 -Force
  }
  catch {}
}

function Aggregate-Stats {
  param([object[]] $stepRecords)
  $ok = ($stepRecords | Where-Object { $_.status -eq 'OK' }).Count
  $failed = ($stepRecords | Where-Object { $_.status -eq 'Failed' }).Count
  $skipped = ($stepRecords | Where-Object { $_.status -eq 'Skipped' }).Count
  $status = if ($failed -gt 0) { 'FAIL' } elseif ($ok -gt 0) { 'PASS' } else { 'SKIP' }
  return @{ ok = $ok; failed = $failed; skipped = $skipped; status = $status }
}

function Register-PostCheckOnce {
  param(
    [string] $scriptFullPath
  )
  $startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
  if (-not (Test-Path -LiteralPath $startup)) { return $false }
  $cmdPath = Join-Path $startup 'MinimalRebootPostCheck.cmd'
  $cmd = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$scriptFullPath`" -PostOnly; powershell -NoProfile -ExecutionPolicy Bypass -Command `"Remove-Item -LiteralPath `'$cmdPath`' -Force`""
  Set-Content -Path $cmdPath -Value $cmd -Encoding ASCII -Force
  Write-Log "Registered post-check once at Startup: $cmdPath" 'INFO'
  return $true
}

function Run-Phase {
  param(
    [string] $Phase,
    [string] $ScriptDir,
    [int] $Hours,
    [switch] $SkipReport,
    [switch] $SkipBackup
  )
  $records = @()
  $defs = @()
  if ($Phase -eq 'Pre') {
    $defs += @{ Name = 'QuickStatus'; Path = (Join-Path $ScriptDir 'quick_status.ps1'); Args = @() }
    $defs += @{ Name = 'QueueHealth'; Path = (Join-Path $ScriptDir 'queue_health_check.ps1'); Args = @() }
    $defs += @{ Name = 'SystemHealth'; Path = (Join-Path $ScriptDir 'system_health_check.ps1'); Args = @() }
    if (-not $SkipReport) {
      $defs += @{ Name = 'MonitoringReport'; Path = (Join-Path $ScriptDir 'generate_monitoring_report.ps1'); Args = @('-Hours', $Hours) }
    }
    if (-not $SkipBackup) {
      $defs += @{ Name = 'SaveSession'; Path = (Join-Path $ScriptDir 'save_session_with_changes.ps1'); Args = @() }
      $defs += @{ Name = 'Backup'; Path = (Join-Path $ScriptDir 'end_of_day_backup.ps1'); Args = @('-Note', 'MinimalRebootChain') }
    }
  }
  else {
    # Post phase: quick verification and short report
    $defs += @{ Name = 'QuickStatus'; Path = (Join-Path $ScriptDir 'quick_status.ps1'); Args = @('-OutJson', (Join-Path (Split-Path -Parent $ScriptDir) 'outputs\quick_status_after_reboot.json')) }
    $defs += @{ Name = 'QueueHealth'; Path = (Join-Path $ScriptDir 'queue_health_check.ps1'); Args = @() }
    $defs += @{ Name = 'SystemHealth'; Path = (Join-Path $ScriptDir 'system_health_check.ps1'); Args = @('-Detailed') }
    if (-not $SkipReport) {
      $defs += @{ Name = 'MonitoringReport'; Path = (Join-Path $ScriptDir 'generate_monitoring_report.ps1'); Args = @('-Hours', [math]::Min($Hours, 6)) }
    }
  }

  foreach ($d in $defs) {
    $rec = New-StepRecord -Name $d.Name
    $records += (Invoke-Step -rec $rec -ScriptPath $d.Path -Args $d.Args)
  }
  $stats = Aggregate-Stats -stepRecords $records
  return [ordered]@{
    status  = $stats.status
    ok      = $stats.ok
    failed  = $stats.failed
    skipped = $stats.skipped
    steps   = $records
  }
}

# ------------------------ main ------------------------
$paths = Resolve-RepoPaths
Write-Log "Minimal Reboot Chain start (PreOnly=$PreOnly, PostOnly=$PostOnly, DryRun=$DryRun, Reboot=$Reboot)" 'INFO'

$summary = [ordered]@{
  generated = (Get-Date).ToString('o')
  env       = [ordered]@{
    computerName      = $env:COMPUTERNAME
    userName          = "$env:USERDOMAIN\\$env:USERNAME"
    powershellVersion = $PSVersionTable.PSVersion.ToString()
  }
  pre       = $null
  post      = $null
  overall   = 'UNKNOWN'
  nextSteps = @()
}

if (-not $PostOnly) {
  $summary.pre = Run-Phase -Phase 'Pre' -ScriptDir $paths.ScriptDir -Hours $Hours -SkipReport:$NoReport -SkipBackup:$NoBackup
}

if ($RegisterPostCheck -and -not $PostOnly) {
  Register-PostCheckOnce -scriptFullPath (Join-Path $paths.ScriptDir 'minimal_reboot_chain.ps1') | Out-Null
}

if ($PostOnly) {
  $summary.post = Run-Phase -Phase 'Post' -ScriptDir $paths.ScriptDir -Hours $Hours -SkipReport:$NoReport -SkipBackup:$true
}

# Decide overall
$statuses = @()
if ($summary.pre) { $statuses += $summary.pre.status }
if ($summary.post) { $statuses += $summary.post.status }
if ($statuses.Count -eq 0) { $summary.overall = 'SKIP' }
elseif ($statuses -contains 'FAIL') { $summary.overall = 'FAIL' }
elseif ($statuses -contains 'PASS') { $summary.overall = 'PASS' } else { $summary.overall = $statuses[0] }

if ($summary.pre -and $summary.pre.failed -gt 0) {
  $summary.nextSteps += 'Review pre-reboot failures above; re-run with -DryRun for quick validation if needed.'
}
if ($Reboot -and -not $PostOnly) {
  $summary.nextSteps += 'System will reboot now. On next logon, run post-check (or use -RegisterPostCheck before reboot).'
}

Save-Outputs -summary $summary -jsonPath $paths.JsonOut -mdPath $paths.MdOut
Write-Log "Summary saved: $($paths.JsonOut) and $($paths.MdOut)" 'INFO'

if ($Reboot -and -not $PostOnly) {
  if ($DryRun) {
    Write-Log '[DryRun] Reboot suppressed' 'WARN'
  }
  else {
    Write-Log 'Rebooting system in 5 seconds...' 'WARN'
    try { shutdown.exe /r /t 5 /c "MinimalRebootChain" | Out-Null } catch { Restart-Computer -Force }
  }
}

if ($summary.overall -eq 'FAIL') { exit 1 } else { exit 0 }
<#
.SYNOPSIS
  Minimal, idempotent pre/post reboot chain for AGI workspace (Windows, PowerShell 5.1+).

.DESCRIPTION
  Runs a compact set of safety checks, snapshots, and (optionally) backup before reboot.
  After reboot, verifies core services and regenerates status. Designed to use existing
  repo scripts; any missing step is skipped gracefully and recorded.

.PARAMETER PreOnly
  Run only the pre-reboot phase.
[CmdletBinding()]
param(
  [switch] $PreOnly,
  [switch] $PostOnly,
  [switch] $DryRun,
  [int] $Hours = 24,
  [switch] $AutoReboot,
  [switch] $OpenReport,
  [switch] $Silent,
  [switch] $EnsureAutoStart,
  [switch] $Backup,
  [int] $RebootAfter = 10
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Resolve paths
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $Root)) { $Root = (Resolve-Path '.').Path }
$Scripts = Join-Path $Root 'scripts'
$Outputs = Join-Path $Root 'outputs'
if (-not (Test-Path -LiteralPath $Outputs)) { New-Item -ItemType Directory -Path $Outputs -Force | Out-Null }

# Utility: small console helpers
function Write-Ok   { param([string]$Msg) if (-not $Silent) { Write-Host $Msg -ForegroundColor Green } }
function Write-Info { param([string]$Msg) if (-not $Silent) { Write-Host $Msg -ForegroundColor Cyan } }
function Write-Warn { param([string]$Msg) if (-not $Silent) { Write-Host $Msg -ForegroundColor Yellow } }
function Write-Err  { param([string]$Msg) Write-Host $Msg -ForegroundColor Red }

# Utility: write step result to JSONL log
$logPath = Join-Path $Outputs 'minimal_reboot_chain_log.jsonl'
function Write-StepLog {
  param(
    [string] $Name,
    [bool] $Success,
    [int] $ExitCode = 0,
    [string] $Message = '',
    [hashtable] $Meta
  )
  $entry = [ordered]@{
    ts = (Get-Date).ToString('o')
    phase = if ($script:Phase) { $script:Phase } else { 'unknown' }
    name = $Name
    success = $Success
    exit_code = $ExitCode
    message = $Message
    meta = $Meta
  }
  $entry | ConvertTo-Json -Depth 8 | Add-Content -Path $logPath -Encoding UTF8
  if (-not $Silent) {
    $color = if ($Success) { 'Green' } else { 'Yellow' }
    Write-Host "[${script:Phase}] $Name => $(if ($Success){'OK'}else{'WARN'})" -ForegroundColor $color
    if ($Message) { Write-Host "  $Message" -ForegroundColor DarkGray }
  }
}

# Utility: safe-invoke another script if present
function Invoke-RepoScript {
  [CmdletBinding()] param(
    [Parameter(Mandatory)] [string] $ScriptName,
    [string[]] $Arguments,
    [switch] $AllowMissing
  )
  $path = Join-Path $Scripts $ScriptName
  if (-not (Test-Path -LiteralPath $path)) {
    if ($AllowMissing) {
      Write-StepLog -Name $ScriptName -Success $true -Message 'Skipped (missing)'
      return @{ success = $true; skipped = $true; exit = 0 }
    } else {
      Write-StepLog -Name $ScriptName -Success $false -ExitCode 127 -Message 'Missing script'
      return @{ success = $false; skipped = $true; exit = 127 }
    }
  }
  try {
    $stdOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $path @Arguments 2>&1
    $code = $LASTEXITCODE
    $ok = ($code -eq 0)
    Write-StepLog -Name $ScriptName -Success $ok -ExitCode $code -Message '' -Meta @{ stdout = ($stdOut -join "`n") }
    return @{ success = $ok; exit = $code; stdout = ($stdOut -join "`n") }
  } catch {
    Write-StepLog -Name $ScriptName -Success $false -ExitCode 1 -Message $_.Exception.Message
    return @{ success = $false; exit = 1; error = $_.Exception.Message }
  }
}

function Run-PrePhase {
  $script:Phase = 'pre'
  $summary = [ordered]@{
    started = (Get-Date).ToString('o')
    hours = $Hours
    steps = @{}
  }
  # 1) Unified dashboard (quick_status)
  $r1 = Invoke-RepoScript -ScriptName 'quick_status.ps1' -Arguments @('-AlertOnDegraded','-LogJsonl') -AllowMissing
  $summary.steps.quick_status = $r1

  # 2) Queue health
  $r2 = Invoke-RepoScript -ScriptName 'queue_health_check.ps1' -AllowMissing
  $summary.steps.queue_health = $r2

  # 3) System quick health
  $r3 = Invoke-RepoScript -ScriptName 'run_quick_health.ps1' -Arguments @('-JsonOnly','-Fast','-TimeoutSec','10','-MaxDuration','8') -AllowMissing
  $summary.steps.system_quick_health = $r3

  # 4) Generate monitoring report
  $r4 = Invoke-RepoScript -ScriptName 'generate_monitoring_report.ps1' -Arguments @('-Hours', "$Hours") -AllowMissing
  $summary.steps.generate_report = $r4

  # 5) Save session continuity context
  $r5 = Invoke-RepoScript -ScriptName 'save_session_with_changes.ps1' -AllowMissing
  $summary.steps.save_session = $r5

  # 6) Optional backup
  if ($Backup) {
    $r6 = Invoke-RepoScript -ScriptName 'end_of_day_backup.ps1' -Arguments @('-Note','MinimalRebootChain') -AllowMissing
    $summary.steps.backup = $r6
  }

  $summary.ended = (Get-Date).ToString('o')
  $preSummaryPath = Join-Path $Outputs 'minimal_reboot_chain_summary_pre.json'
  ($summary | ConvertTo-Json -Depth 8) | Set-Content -Path $preSummaryPath -Encoding UTF8
  Write-Info "Pre phase summary -> $preSummaryPath"
  return $summary
    $proc = [System.Diagnostics.Process]::Start($psi)
function Run-PostPhase {
  $script:Phase = 'post'
  $summary = [ordered]@{
    started = (Get-Date).ToString('o')
    hours = $Hours
    steps = @{}
  }
  # 1) Ensure master orchestrator auto-start (optional)
  if ($EnsureAutoStart) {
    $r1 = Invoke-RepoScript -ScriptName 'register_master_orchestrator.ps1' -Arguments @('-Register') -AllowMissing
    $summary.steps.ensure_autostart = $r1
  } else {
    $r1 = Invoke-RepoScript -ScriptName 'register_master_orchestrator.ps1' -Arguments @('-Status') -AllowMissing
    $summary.steps.orchestrator_status = $r1
  }

  # 2) Ensure task queue server and worker
  $r2 = Invoke-RepoScript -ScriptName 'ensure_task_queue_server.ps1' -Arguments @('-Port','8091') -AllowMissing
  $summary.steps.queue_server = $r2
  $r3 = Invoke-RepoScript -ScriptName 'ensure_rpa_worker.ps1' -AllowMissing
  $summary.steps.queue_worker = $r3

  # 3) Quick health + fresh dashboard
  $r4 = Invoke-RepoScript -ScriptName 'run_quick_health.ps1' -Arguments @('-JsonOnly','-Fast','-TimeoutSec','10','-MaxDuration','8') -AllowMissing
  $summary.steps.system_quick_health = $r4
  $r5 = Invoke-RepoScript -ScriptName 'quick_status.ps1' -Arguments @('-AlertOnDegraded','-LogJsonl') -AllowMissing
  $summary.steps.quick_status = $r5

  # 4) Regenerate monitoring report
  $r6 = Invoke-RepoScript -ScriptName 'generate_monitoring_report.ps1' -Arguments @('-Hours', "$Hours") -AllowMissing
  $summary.steps.generate_report = $r6

  # 5) Optionally open reports
  if ($OpenReport) {
    $md = Join-Path $Outputs 'monitoring_report_latest.md'
    $html = Join-Path $Outputs 'monitoring_dashboard_latest.html'
    $json = Join-Path $Outputs 'monitoring_metrics_latest.json'
    foreach ($p in @($md,$html,$json)) { if (Test-Path -LiteralPath $p) { Start-Process $p } }
  }

  $summary.ended = (Get-Date).ToString('o')
  $postSummaryPath = Join-Path $Outputs 'minimal_reboot_chain_summary_post.json'
  ($summary | ConvertTo-Json -Depth 8) | Set-Content -Path $postSummaryPath -Encoding UTF8
  Write-Info "Post phase summary -> $postSummaryPath"
  return $summary
}

# -------- Argument validation & flow control --------
if ($PreOnly -and $PostOnly) { Write-Err 'Specify only one of -PreOnly or -PostOnly.'; exit 2 }
if ($Hours -le 0) { Write-Err '-Hours must be > 0'; exit 2 }

if ($PostOnly) {
  Run-PostPhase | Out-Null
  Write-Ok 'Post-reboot phase completed.'
  exit 0
}

# Default to pre phase if none specified
Run-PrePhase | Out-Null

if ($AutoReboot) {
  if ($DryRun) {
    Write-Warn 'DryRun set: skipping reboot.'
  } else {
    Write-Info "Scheduling reboot in $RebootAfter seconds..."
    try {
      shutdown /r /t $RebootAfter /c "AGI minimal reboot chain" /f | Out-Null
      Write-Ok 'Reboot initiated.'
    } catch {
      Write-Err "Failed to schedule reboot: $_"
      exit 2
    }
  }
} else {
  Write-Info 'AutoReboot not set; showing post-reboot checklist:'
}

# Post-reboot checklist (always print for the user)
$postChecklist = @(
  '1) Log back in and open this workspace in VS Code',
  '2) Run task: ?? Master: Check Status (or script register_master_orchestrator.ps1 -Status)',
  '3) Run task: Queue: Health Check (ensure server healthy)',
  '4) Run task: Monitoring: Unified Dashboard (AGI + Lumen)',
  '5) Optional: Monitoring: Generate Report (24h) + Open',
  '6) If degraded: Watchdog: Start Task Watchdog (Background) and Queue: Ensure Worker'
)
    $stdErr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    $code = $proc.ExitCode
    $ok = ($code -eq 0)
    Write-StepLog -Name $ScriptName -Success $ok -ExitCode $code -Message ($stdErr.Trim()) -Meta @{ stdout = $stdOut }
    return @{ success = $ok; exit = $code; stdout = $stdOut; stderr = $stdErr }
  } catch {
    Write-StepLog -Name $ScriptName -Success $false -ExitCode 1 -Message $_.Exception.Message
    return @{ success = $false; exit = 1; error = $_.Exception.Message }
  }
}

function Run-PrePhase {
  $script:Phase = 'pre'
  $summary = [ordered]@{
    started = (Get-Date).ToString('o')
    hours = $Hours
    steps = @{}
  }
  # 1) Unified dashboard (quick_status)
  $r1 = Invoke-RepoScript -ScriptName 'quick_status.ps1'
  $summary.steps.quick_status = $r1

  # 2) Queue health
  $r2 = Invoke-RepoScript -ScriptName 'queue_health_check.ps1' -AllowMissing
  $summary.steps.queue_health = $r2

  # 3) System quick health
  $r3 = Invoke-RepoScript -ScriptName 'run_quick_health.ps1' -Arguments @('-JsonOnly','-Fast','-TimeoutSec','10','-MaxDuration','8') -AllowMissing
  $summary.steps.system_quick_health = $r3

  # 4) Generate 24h report
  $r4 = Invoke-RepoScript -ScriptName 'generate_monitoring_report.ps1' -Arguments @('-Hours',"$Hours")
  $summary.steps.generate_report = $r4

  # 5) Save session continuity snapshot
  $r5 = Invoke-RepoScript -ScriptName 'save_session_with_changes.ps1' -AllowMissing
  $summary.steps.save_session = $r5

  # 6) Backup (optional in DryRun)
  if ($DryRun) {
    Write-StepLog -Name 'end_of_day_backup.ps1' -Success $true -Message 'DryRun: skipped backup'
    $r6 = @{ success = $true; skipped = $true; exit = 0 }
  } else {
    $r6 = Invoke-RepoScript -ScriptName 'end_of_day_backup.ps1' -Arguments @('-Note','Minimal Reboot Chain') -AllowMissing
  }
  $summary.steps.backup = $r6

  $summary.completed = (Get-Date).ToString('o')
  $preJson = Join-Path $Outputs 'minimal_reboot_precheck.json'
  $summary | ConvertTo-Json -Depth 8 | Set-Content -Path $preJson -Encoding UTF8

  if ($OpenReport) {
    $md = Join-Path $Outputs 'monitoring_report_latest.md'
    if (Test-Path -LiteralPath $md) { Start-Process 'code' $md }
  }

  # Optional: reboot
  if ($AutoReboot -and -not $DryRun) {
    Write-Host 'Issuing reboot in 30 seconds...' -ForegroundColor Cyan
    shutdown.exe /r /t 30 /c "AGI minimal reboot chain" | Out-Null
  } elseif ($AutoReboot -and $DryRun) {
    Write-Host 'DryRun enabled: skipping reboot' -ForegroundColor Yellow
  }
}

function Run-PostPhase {
  $script:Phase = 'post'
  $summary = [ordered]@{
    started = (Get-Date).ToString('o')
    steps = @{}
  }

  # 0) Ensure auto-start (optional)
  if ($EnsureAutoStart) {
    $ra = Invoke-RepoScript -ScriptName 'register_master_orchestrator.ps1' -Arguments @('-Register') -AllowMissing
    $summary.steps.ensure_autostart = $ra
  }

  # 1) Ensure queue server
  $r1 = Invoke-RepoScript -ScriptName 'ensure_task_queue_server.ps1' -Arguments @('-Port','8091') -AllowMissing
  $summary.steps.ensure_queue_server = $r1

  # 2) Ensure single worker
  $r2 = Invoke-RepoScript -ScriptName 'ensure_rpa_worker.ps1' -Arguments @('-EnforceSingle','-MaxWorkers','1') -AllowMissing
  $summary.steps.ensure_worker = $r2

  # 3) Start watchdog (background)
  $watchdogPy = Join-Path $Scripts '..\fdo_agi_repo\.venv\Scripts\python.exe'
  $watchdogScript = Join-Path $Scripts '..\fdo_agi_repo\scripts\task_watchdog.py'
  try {
    if (Test-Path -LiteralPath $watchdogScript) {
      $py = if (Test-Path -LiteralPath $watchdogPy) { $watchdogPy } else { 'python' }
      Start-Process -FilePath $py -ArgumentList "`"$watchdogScript`" --server http://127.0.0.1:8091 --interval 60 --auto-recover" -WindowStyle Hidden | Out-Null
      Write-StepLog -Name 'task_watchdog.py' -Success $true -Message 'Launched (background)'
      $summary.steps.watchdog = @{ success = $true; launched = $true }
    } else {
      Write-StepLog -Name 'task_watchdog.py' -Success $true -Message 'Skipped (missing)'
      $summary.steps.watchdog = @{ success = $true; skipped = $true }
    }
  } catch {
    Write-StepLog -Name 'task_watchdog.py' -Success $false -Message $_.Exception.Message
    $summary.steps.watchdog = @{ success = $false; error = $_.Exception.Message }
  }

  # 4) Unified dashboard + 24h report
  $r3 = Invoke-RepoScript -ScriptName 'quick_status.ps1' -Arguments @('-OutJson', (Join-Path $Outputs 'quick_status_latest.json')) -AllowMissing
  $summary.steps.quick_status = $r3

  $r4 = Invoke-RepoScript -ScriptName 'generate_monitoring_report.ps1' -Arguments @('-Hours',"$Hours")
  $summary.steps.generate_report = $r4

  $summary.completed = (Get-Date).ToString('o')
  $postJson = Join-Path $Outputs 'minimal_reboot_postcheck.json'
  $summary | ConvertTo-Json -Depth 8 | Set-Content -Path $postJson -Encoding UTF8

  if ($OpenReport) {
    $html = Join-Path $Outputs 'monitoring_dashboard_latest.html'
    if (Test-Path -LiteralPath $html) { Start-Process $html }
  }
}

if ($PreOnly -and $PostOnly) {
  Write-Host 'Cannot specify both -PreOnly and -PostOnly.' -ForegroundColor Red
  exit 2
}

if (-not $PreOnly -and -not $PostOnly) {
  # Default: pre only (safe)
  $PreOnly = $true
}

if ($PreOnly) { Run-PrePhase }
if ($PostOnly) { Run-PostPhase }

Write-Host 'Minimal reboot chain completed.' -ForegroundColor Green
exit 0
<#!
Minimal Reboot Chain Script
Purpose:
  Orchestrates a safe, idempotent pre-reboot snapshot for the AGI workspace and gives post-reboot guidance.

Features:
  1. Health & readiness checks (queue server, core processes) with light timeout.
  2. Session continuity save (if not saved in last N minutes).
  3. Monitoring 24h report generation only if older than freshness threshold (default 6h).
  4. Optional lightweight backup (skips if a backup ran < 8h ago).
  5. Emits a concise markdown summary of actions under outputs/minimal_reboot_chain_summary.md.
  6. Provides the exact reboot command suggested.
  7. Post‑reboot checklist printed to console and saved for reference.

Usage Examples:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\minimal_reboot_chain.ps1 -DryRun
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\minimal_reboot_chain.ps1 -SkipBackup
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\minimal_reboot_chain.ps1 -FreshReportHours 4 -ForceReport

Parameters:
  -DryRun            : Show what would happen; do not perform state-changing actions.
  -SkipBackup        : Do not attempt backup logic.
  -ForceReport       : Always regenerate 24h monitoring report.
  -FreshReportHours  : Consider report stale after this many hours (default 6).
  -MaxSessionAgeMin  : Resave continuity if last save older than this (default 45).
  -BackupFreshHours  : Skip backup if a backup was done within this window (default 8).
  -RebootAfter       : If provided, automatically initiate reboot after successful prep (Seconds). Default: none (prompt only).
  -ConfirmAutoReboot : Required when -RebootAfter is used to avoid accidental reboot.

Returns non‑zero exit code on hard failures.
Note: This script is intentionally defensive & uses simple checks—adapt thresholds as system evolves.
!>
param(
  [switch]$DryRun,
  [switch]$SkipBackup,
  [switch]$ForceReport,
  [int]$FreshReportHours = 6,
  [int]$MaxSessionAgeMin = 45,
  [int]$BackupFreshHours = 8,
  [int]$RebootAfter,
  [switch]$ConfirmAutoReboot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($msg){ Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg){ Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warn($msg){ Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg){ Write-Host "[ERR] $msg" -ForegroundColor Red }

$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$outputs = Join-Path $root 'outputs'
if (!(Test-Path -LiteralPath $outputs)) { New-Item -ItemType Directory -Path $outputs -Force | Out-Null }
$summaryFile = Join-Path $outputs 'minimal_reboot_chain_summary.md'

$summaryLines = @()
function Add-Summary($line){ $script:summaryLines += $line }

Add-Summary("# Minimal Reboot Chain Summary (`$(Get-Date -Format 'u')`)\n")

function Get-FileAgeHours($path){ if (!(Test-Path -LiteralPath $path)) { return $null }; return ((Get-Date) - (Get-Item -LiteralPath $path).LastWriteTime).TotalHours }

# 1. Queue health check
Write-Info 'Checking task queue server health (port 8091)...'
$queueHealthy = $false
try {
  $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8091/api/health' -TimeoutSec 2
  if ($resp.StatusCode -eq 200) { $queueHealthy = $true }
} catch {}
if ($queueHealthy){ Write-Ok 'Queue server healthy.'; Add-Summary("- Queue server: healthy") } else { Write-Warn 'Queue server not responding (will attempt to continue).'; Add-Summary("- Queue server: NOT healthy") }

# 2. Session continuity save freshness
$sessionFile = Join-Path $outputs 'session_continuity_latest.md'
$sessionAgeMin = if (Test-Path -LiteralPath $sessionFile) { ((Get-Date) - (Get-Item $sessionFile).LastWriteTime).TotalMinutes } else { $null }
if ($sessionAgeMin -eq $null){ Write-Warn 'No session continuity file found; will trigger save.' } elseif ($sessionAgeMin -le $MaxSessionAgeMin){ Write-Ok "Session continuity recent (${sessionAgeMin:N1} min)." }
else { Write-Info "Session continuity stale (${sessionAgeMin:N1} min > $MaxSessionAgeMin). Will refresh." }

if (-not $DryRun){
  if (($sessionAgeMin -eq $null) -or ($sessionAgeMin -gt $MaxSessionAgeMin)){
    $saveScript = Join-Path $root 'scripts/session_continuity_restore.ps1'
    if (Test-Path -LiteralPath $saveScript){
      try { & $saveScript -Silent; Write-Ok 'Session continuity refreshed.'; Add-Summary("- Session continuity: refreshed") } catch { Write-Err "Failed to refresh session continuity: $_"; Add-Summary("- Session continuity: refresh FAILED") }
    } else { Write-Warn 'Session continuity restore script missing.'; Add-Summary("- Session continuity: script missing") }
  } else { Add-Summary("- Session continuity: fresh (${sessionAgeMin:N1} min)") }
} else { Add-Summary("- Session continuity: would refresh if stale") }

# 3. Monitoring report freshness
$reportMd = Join-Path $outputs 'monitoring_report_latest.md'
$reportAge = Get-FileAgeHours $reportMd
if ($ForceReport){ Write-Info 'ForceReport specified: will regenerate monitoring report.' }
elseif ($reportAge -eq $null){ Write-Warn 'Monitoring report missing; will generate.' }
elseif ($reportAge -gt $FreshReportHours){ Write-Info "Monitoring report stale (${reportAge:N2}h > $FreshReportHours h); will regenerate." }
else { Write-Ok "Monitoring report fresh (${reportAge:N2}h)." }

if (-not $DryRun){
  if ($ForceReport -or $reportAge -eq $null -or $reportAge -gt $FreshReportHours){
    $monitorScript = Join-Path $root 'scripts/generate_monitoring_report.ps1'
    if (Test-Path -LiteralPath $monitorScript){
      try { & $monitorScript -Hours 24; Write-Ok '24h monitoring report generated.'; Add-Summary("- Monitoring report: regenerated (24h)") } catch { Write-Err "Failed to generate monitoring report: $_"; Add-Summary("- Monitoring report: generation FAILED") }
    } else { Write-Warn 'Monitoring generation script missing.'; Add-Summary("- Monitoring report: script missing") }
  } else { Add-Summary("- Monitoring report: fresh (${reportAge:N2}h)") }
} else { Add-Summary("- Monitoring report: would regenerate if stale/forced") }

# 4. Backup logic
$backupScript = Join-Path $root 'scripts/end_of_day_backup.ps1'
$backupRecent = $false
$backupAgeHours = $null
if (Test-Path -LiteralPath $outputs){
  $bk = Get-ChildItem -Path $outputs -Filter '*backup*' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($bk){ $backupAgeHours = ((Get-Date) - $bk.LastWriteTime).TotalHours; if ($backupAgeHours -le $BackupFreshHours){ $backupRecent = $true } }
}
if ($SkipBackup){ Write-Info 'SkipBackup enabled: will not perform backup.'; Add-Summary("- Backup: skipped by flag") }
elseif ($backupRecent){ Write-Ok "Recent backup found (${backupAgeHours:N2}h). Skipping."; Add-Summary("- Backup: skipped (fresh ${backupAgeHours:N2}h)") }
elseif ($DryRun){ Write-Info 'DryRun: would perform backup.'; Add-Summary("- Backup: would run (DryRun)") }
else {
  if (Test-Path -LiteralPath $backupScript){
    try { & $backupScript -Note 'MinimalRebootChain'; Write-Ok 'Backup completed.'; Add-Summary("- Backup: completed") } catch { Write-Err "Backup failed: $_"; Add-Summary("- Backup: FAILED") }
  } else { Write-Warn 'Backup script missing.'; Add-Summary("- Backup: script missing") }
}

# 5. Post-reboot checklist assembly
$postChecklist = @(
  'POST-REBOOT CHECKLIST:',
  '  1. Verify queue server health: scripts/queue_health_check.ps1',
  '  2. Run quick status dashboard: scripts/quick_status.ps1 -OutJson outputs/quick_status_latest.json',
  '  3. Confirm session continuity auto-restore (should run on folder open).',
  '  4. Spot check monitoring dashboard HTML.',
  '  5. (Optional) Run Python tests: Python: Run All Tests (repo venv).'
)
Add-Summary("\n## Post-Reboot Checklist\n" + ($postChecklist -join "`n") + "\n")

# 6. Recommended reboot command
$rebootCmd = 'shutdown /r /t 5 /c "AGI scheduled reboot after snapshot" /f'
Add-Summary("## Recommended Reboot Command\n````powershell\n$rebootCmd\n````\n")

Write-Info 'Writing summary file...'
try { $summaryLines | Out-File -FilePath $summaryFile -Encoding UTF8 -Force; Write-Ok "Summary written: $summaryFile" } catch { Write-Err "Failed to write summary: $_" }

if ($RebootAfter -and -not $ConfirmAutoReboot){
  Write-Warn 'RebootAfter specified but -ConfirmAutoReboot not provided; will NOT reboot.'
} elseif ($RebootAfter -and $ConfirmAutoReboot){
  if ($DryRun){ Write-Info "DryRun: would reboot in $RebootAfter seconds." }
  else {
    Write-Info "Scheduling reboot in $RebootAfter seconds..."
Write-Ok 'Minimal reboot chain completed.'
Write-Host '--- Post-Reboot Checklist ---' -ForegroundColor Magenta
$postChecklist | ForEach-Object { Write-Host $_ }

exit 0