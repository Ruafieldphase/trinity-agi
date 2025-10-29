<#
.SYNOPSIS
    Trigger the GitHub Actions load test workflow with proper inputs and helpful validation.

.DESCRIPTION
    Wraps `gh workflow run` for the workflow named "Ion Mentoring - Scheduled Load Testing".
    Validates that GitHub CLI is installed and authenticated, maps inputs, and surfaces errors clearly.

.EXAMPLE
    ./trigger_ci_load_test.ps1 -Profile light -TestDurationMinutes 2 -EnforceSlo -SloP95Ms 500 -MaxErrorPct 1 -Ref master

.PARAMETER Profile
    Profile to run: all|light|medium|heavy|stress

.PARAMETER TestDurationMinutes
    Stress scenario duration in minutes (other scenario durations are fixed in the workflow).

.PARAMETER EnforceSlo
    When set, the analyze job will enforce SLO thresholds and fail the workflow on violation.

.PARAMETER SloP95Ms
    P95 latency SLO threshold in milliseconds.

.PARAMETER MaxErrorPct
    Max allowed error percentage (0-100).

.PARAMETER ApiHost
    Optional API host override (e.g., https://your-cloud-run-url). Leave empty to use workflow default.

.PARAMETER Ref
    Git ref to run the workflow against (branch or SHA). Defaults to 'master'.

.PARAMETER WorkflowName
    Workflow display name. Defaults to 'Ion Mentoring - Scheduled Load Testing'.
#>

param(
    [ValidateSet('all', 'light', 'medium', 'heavy', 'stress')]
    [string]$LoadProfile = 'all',
    [int]$TestDurationMinutes = 5,
    [int]$MaxUsers = 200,
    [switch]$EnforceSlo,
    [int]$SloP95Ms = 500,
    [double]$MaxErrorPct = 1,
    [string]$ApiHost = '',
    [string]$Ref = 'master',
    [string]$WorkflowName = 'Ion Mentoring - Scheduled Load Testing',
    [string]$Repo = '' # Optional owner/repo. If empty, gh uses current repo context.
)

function Write-Info($msg) { Write-Host $msg -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor DarkYellow }
function Write-Err($msg) { Write-Host $msg -ForegroundColor Red }

# Validate gh is available
$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
    Write-Err 'GitHub CLI (gh) not found. Install from https://cli.github.com/ and ensure it is on PATH.'
    exit 127
}

# Validate auth
& gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Err 'GitHub CLI is not authenticated. Run: gh auth login'
    exit 128
}

# Prepare optional repo arg for all gh commands
$repoArg = @()
if ($Repo -and $Repo.Trim()) {
    $repoArg = @('-R', $Repo.Trim())
}

# Preflight: verify workflow name exists
$wfList = & gh workflow list --limit 50 @repoArg 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Warn 'Unable to list workflows. Proceeding to run, but name verification skipped.'
}
elseif ($wfList -and ($wfList -join "`n") -notmatch [Regex]::Escape($WorkflowName)) {
    Write-Err "Workflow not found: '$WorkflowName'"
    Write-Host 'Available workflows:' -ForegroundColor Gray
    $wfList | ForEach-Object { Write-Host ("  - {0}" -f $_) -ForegroundColor Gray }
    Write-Warn "Tip: Confirm the workflow display name or use -WorkflowName to match exactly."
    if ($Repo) { Write-Warn "Checked repository: $Repo" } else { Write-Warn 'Checked current repository context.' }
    exit 2
}

Write-Info 'Triggering GitHub Actions workflow:'
Write-Host "  Workflow   : $WorkflowName" -ForegroundColor Gray
Write-Host "  Ref        : $Ref" -ForegroundColor Gray
Write-Host "  Profile    : $LoadProfile" -ForegroundColor Gray
Write-Host "  Duration   : $TestDurationMinutes min (stress scenario)" -ForegroundColor Gray
if ($EnforceSlo) { $enforce = 'true' } else { $enforce = 'false' }
Write-Host "  Enforce SLO: $enforce (P95<=${SloP95Ms}ms, Error%<=${MaxErrorPct})" -ForegroundColor Gray
if ($ApiHost) { Write-Host "  API Host   : $ApiHost" -ForegroundColor Gray }
if ($Repo) { Write-Host "  Repo       : $Repo" -ForegroundColor Gray }

# Build input args
$inputs = @(
    '-f', "profile=$LoadProfile",
    '-f', "test_duration=$TestDurationMinutes",
    '-f', "enforce_slo=$enforce",
    '-f', "slo_p95_ms=$SloP95Ms",
    '-f', "max_error_pct=$MaxErrorPct",
    '-f', "max_users=$MaxUsers"
)
if ($ApiHost) { $inputs += @('-f', "api_host=$ApiHost") }

# Run workflow
& gh workflow run "$WorkflowName" --ref "$Ref" @repoArg @inputs
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Err "Failed to trigger workflow (exit $code)."
    Write-Warn 'Tip: Ensure you have push access, correct repo context, and the workflow name matches exactly.'
    if ($Repo) {
        Write-Warn ("You can list workflows with: gh workflow list -R {0}" -f $Repo)
    }
    else {
        Write-Warn 'You can list workflows with: gh workflow list'
    }
    exit $code
}

Write-Host ''
Write-Info 'Workflow dispatched successfully.'
Write-Host 'You can watch progress with:' -ForegroundColor Gray
if ($Repo) {
    Write-Host ("  gh run list -R {0} --limit 5" -f $Repo) -ForegroundColor Gray
    Write-Host ("  gh run watch -R {0} --exit-status" -f $Repo) -ForegroundColor Gray
}
else {
    Write-Host '  gh run list --limit 5' -ForegroundColor Gray
    Write-Host '  gh run watch --exit-status' -ForegroundColor Gray
}

